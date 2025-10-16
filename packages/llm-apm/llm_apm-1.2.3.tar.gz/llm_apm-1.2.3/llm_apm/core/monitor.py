import uuid
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .timer import StepTimer
from .metrics import MetricsCollector, RequestMetrics
from ..config.settings import config
from ..storage.base import BaseStorage
from ..exporters.prometheus import PrometheusExporter
import random
import asyncio
import inspect
from concurrent.futures import ThreadPoolExecutor

from .decorators import get_current_step_metrics, clear_step_context

logger = logging.getLogger(__name__)

_BG_EXECUTOR = ThreadPoolExecutor(max_workers=4)

class LLMMonitor:
    def __init__(self, storage: Optional[BaseStorage] = None, exporter: Optional[PrometheusExporter] = None, sampling_rate: float = None):
        self.storage = storage
        self.exporter = exporter
        self.sampling_rate = sampling_rate or getattr(config, "sampling_rate", 1.0)
        self.metrics_collector = MetricsCollector()
        try:
            if self.exporter and getattr(self.exporter, "start_http_server_flag", False):
                self.exporter.start()
        except Exception as e:
            logger.warning(f"Could not start exporter server: {e}")
        logger.info(f"LLM Monitor initialized with sampling rate: {self.sampling_rate}")

    def should_sample(self, user_id: Optional[str] = None, endpoint: Optional[str] = None) -> bool:
        try:
            from ..utils.sampler import should_sample as deterministic_should_sample
            try:
                samp = config.get_endpoint_sampling(endpoint)
            except Exception:
                samp = getattr(config, "sampling_rate", 1.0)
            return deterministic_should_sample(user_id, samp)
        except Exception:
            return random.random() < getattr(config, "sampling_rate", 1.0)

    def start_request_monitoring(self, endpoint: str, model: str, prompt: str = "", user_id: Optional[str] = None, session_id: Optional[str] = None, request_id: Optional[str] = None) -> 'RequestMonitor':
        if not self.should_sample(user_id=user_id, endpoint=endpoint):
            logger.debug("Request not sampled, skipping monitoring")
            return RequestMonitor(None, None, sample=False)
        request_id = request_id or str(uuid.uuid4())
        metrics = self.metrics_collector.create_request_metrics(
            request_id=request_id,
            model=model,
            endpoint=endpoint,
            prompt=prompt,
            user_id=user_id,
            session_id=session_id
        )
        return RequestMonitor(self, metrics)

    def record_request(self, metrics: RequestMetrics):
        """
        Synchronous record_request - exports to Prometheus only (no storage).
        Storage persistence should be handled by the endpoint handler.
        """
        try:
            metrics.timestamp = datetime.now(timezone.utc)
            self.metrics_collector.add_metrics(metrics)
            
            # Only export to Prometheus
            if self.exporter:
                try:
                    self.exporter.record_request(metrics)
                except Exception as e:
                    logger.error(f"Exporter.record_request failed: {e}", exc_info=True)
            
            logger.debug(f"Recorded metrics (Prometheus only) for request {metrics.request_id}")
        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}", exc_info=True)

    async def record_request_async(self, metrics: RequestMetrics):
        """
        Async version - exports to Prometheus only (no storage).
        Storage persistence should be handled by the endpoint handler.
        """
        try:
            metrics.timestamp = datetime.now(timezone.utc)
            self.metrics_collector.add_metrics(metrics)
            
            # Only export to Prometheus
            if self.exporter:
                try:
                    self.exporter.record_request(metrics)
                except Exception as e:
                    logger.error(f"Exporter.record_request failed: {e}", exc_info=True)

            logger.debug(f"Recorded metrics (async, Prometheus only) for request {metrics.request_id}")
        except Exception as e:
            logger.error(f"Failed to record request metrics (async): {e}", exc_info=True)

    def get_metrics_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        return self.metrics_collector.get_aggregated_metrics(time_window_minutes)

    def get_model_stats(self) -> Dict[str, Any]:
        return self.metrics_collector.get_model_stats()

    def shutdown(self):
        try:
            if self.exporter:
                try:
                    self.exporter.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down exporter: {e}")
            if self.storage:
                try:
                    fn = getattr(self.storage, "close", None)
                    if fn is not None:
                        if inspect.iscoroutinefunction(fn):
                            try:
                                new_loop = asyncio.new_event_loop()
                                try:
                                    new_loop.run_until_complete(fn())
                                finally:
                                    new_loop.close()
                            except Exception as e:
                                logger.exception("Error awaiting storage.close(): %s", e)
                        else:
                            try:
                                fn()
                            except Exception as e:
                                logger.exception("Error calling storage.close(): %s", e)
                except Exception as e:
                    logger.error(f"Error closing storage: {e}")
            try:
                _BG_EXECUTOR.shutdown(wait=False)
            except Exception:
                pass
            logger.info("LLM Monitor shutdown completed")
        except Exception as e:
            logger.error(f"Error during monitor shutdown: {e}", exc_info=True)


class RequestMonitor:
    def __init__(self, monitor: Optional[LLMMonitor], metrics: Optional[RequestMetrics], sample: bool = True):
        self.monitor = monitor
        self.metrics = metrics
        self.step_timer = StepTimer() if sample else None
        self.sample = sample
        self._error_occurred = False
        self._consolidated = False  # Track if we've already consolidated

    def __enter__(self):
        if self.sample and self.step_timer:
            self.step_timer.start_overall()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.sample:
            return
        try:
            if self.step_timer and self.metrics:
                try:
                    self.step_timer.stop_overall()
                except Exception:
                    pass
            
            # THIS IS KEY: Merge decorator metrics into self.metrics BEFORE anything else
            self._consolidate_step_metrics()

            # Handle errors
            if exc_type is not None or self._error_occurred:
                self.metrics.error = True
                self.metrics.error_message = str(exc_val) if exc_val else "Unknown error"
                self.metrics.error_type = exc_type.__name__ if exc_type else "UnknownError"
                self.metrics.status_code = getattr(self.metrics, "status_code", 500)
            
            self.metrics.timestamp = datetime.now(timezone.utc)

            # Export to Prometheus only (no storage persistence here)
            if self.monitor:
                try:
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None

                    if loop and loop.is_running():
                        try:
                            loop.call_soon_threadsafe(
                                lambda: asyncio.create_task(
                                    self.monitor.record_request_async(self.metrics)
                                )
                            )
                        except Exception as e:
                            logger.debug(f"Failed to schedule async record_request: {e}")
                    else:
                        def _bg_call(monitor_obj, metrics_obj):
                            try:
                                monitor_obj.record_request(metrics_obj)
                            except Exception:
                                logger.exception("Background record_request failed")
                        _BG_EXECUTOR.submit(_bg_call, self.monitor, self.metrics)
                except Exception as e:
                    logger.error(f"Failed to schedule background record_request: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error in RequestMonitor cleanup: {e}", exc_info=True)
        finally:
            try:
                clear_step_context()
            except Exception:
                pass

    def _consolidate_step_metrics(self):
        """
        Consolidate all step timing sources into self.metrics attributes.
        This is called in __exit__ so metrics are ready for both Prometheus export AND storage persistence.
        """
        if not self.metrics:
            return
        
        # Only consolidate once
        if getattr(self, '_consolidated', False):
            return
        self._consolidated = True
        
        # Collect all step timings from various sources
        steps = {}
        
        # Source 1: StepTimer
        if self.step_timer:
            steps.update(self.step_timer.get_all_steps())
        
        # Source 2: Decorator metrics (from ContextVar)
        try:
            decorator_metrics = get_current_step_metrics()
            if isinstance(decorator_metrics, dict):
                for k, v in decorator_metrics.items():
                    k_norm = k.rstrip("_ms")
                    try:
                        v_float = float(v)
                        if steps.get(k_norm, 0.0) == 0.0:
                            steps[k_norm] = v_float
                    except Exception:
                        continue
        except Exception:
            logger.debug("Failed to merge decorator metrics", exc_info=True)
        
        # Source 3: metrics.steps dict (if set by endpoint handler)
        try:
            metrics_steps = getattr(self.metrics, "steps", None)
            if isinstance(metrics_steps, dict):
                for key, val in metrics_steps.items():
                    k_norm = key.rstrip("_ms")
                    if val is None:
                        continue
                    try:
                        v_float = float(val)
                        if steps.get(k_norm, 0.0) == 0.0:
                            steps[k_norm] = v_float
                    except Exception:
                        continue
        except Exception:
            logger.debug("Failed merging metrics.steps", exc_info=True)
        
        # Update self.metrics with consolidated values
        self.metrics.preprocessing_ms = steps.get("preprocessing", self.metrics.preprocessing_ms or 0.0)
        self.metrics.llm_api_call_ms = steps.get("llm_api_call", self.metrics.llm_api_call_ms or 0.0)
        self.metrics.postprocessing_ms = steps.get("postprocessing", self.metrics.postprocessing_ms or 0.0)
        self.metrics.metrics_export_ms = steps.get("metrics_export", self.metrics.metrics_export_ms or 0.0)
        
        # Calculate total_latency_ms from the step timings
        self.metrics.total_latency_ms = (
            self.metrics.preprocessing_ms +
            self.metrics.llm_api_call_ms +
            self.metrics.postprocessing_ms +
            self.metrics.metrics_export_ms
        )
        
        logger.debug(
            f"Consolidated step metrics for {self.metrics.request_id}: "
            f"preprocessing={self.metrics.preprocessing_ms:.2f}ms, "
            f"llm_api_call={self.metrics.llm_api_call_ms:.2f}ms, "
            f"postprocessing={self.metrics.postprocessing_ms:.2f}ms, "
            f"metrics_export={self.metrics.metrics_export_ms:.2f}ms, "
            f"total={self.metrics.total_latency_ms:.2f}ms"
        )

    def start_step(self, step_name: str):
        if self.sample and self.step_timer:
            self.step_timer.start_step(step_name)

    def stop_current_step(self):
        if self.sample and self.step_timer:
            return self.step_timer.stop_current_step()
        return None

    def update_tokens(self, input_tokens: int = None, output_tokens: int = None):
        if not self.sample or not self.metrics:
            return
        if input_tokens is not None:
            self.metrics.input_tokens = input_tokens
        if output_tokens is not None:
            self.metrics.output_tokens = output_tokens
        self.metrics.total_tokens = self.metrics.input_tokens + self.metrics.output_tokens
        try:
            from ..utils.cost_calculator import cost_calculator
            self.metrics.estimated_cost_usd = cost_calculator.calculate_cost(
                self.metrics.model,
                self.metrics.input_tokens,
                self.metrics.output_tokens
            )
        except Exception:
            pass

    def update_response(self, response: str, status_code: int = 200):
        if not self.sample or not self.metrics:
            return
        self.metrics.response_size_bytes = len(response.encode('utf-8'))
        self.metrics.status_code = status_code
        try:
            from ..utils.token_counter import token_counter
            output_tokens = token_counter.count_tokens(response, self.metrics.model)
            self.update_tokens(output_tokens=output_tokens)
        except Exception:
            pass

    def record_error(self, error: Exception, status_code: int = 500):
        if not self.sample or not self.metrics:
            return
        self._error_occurred = True
        self.metrics.error = True
        self.metrics.error_message = str(error)
        self.metrics.error_type = type(error).__name__
        self.metrics.status_code = status_code
        logger.error(f"Request {self.metrics.request_id} failed: {error}")

    def get_current_metrics(self) -> Dict[str, Any]:
        if not self.sample or not self.metrics:
            return {"error": True, "message": "Not sampled"}
        
        # Consolidate metrics before returning
        self._consolidate_step_metrics()
        
        return {
            "request_id": self.metrics.request_id,
            "total_latency_ms": self.metrics.total_latency_ms,
            "steps": {
                "preprocessing_ms": self.metrics.preprocessing_ms,
                "llm_api_call_ms": self.metrics.llm_api_call_ms,
                "postprocessing_ms": self.metrics.postprocessing_ms,
                "metrics_export_ms": self.metrics.metrics_export_ms
            },
            "tokens_used": self.metrics.total_tokens,
            "estimated_cost_usd": self.metrics.estimated_cost_usd,
            "error": self.metrics.error
        }


global_monitor: Optional[LLMMonitor] = None

def get_global_monitor() -> Optional[LLMMonitor]:
    """Return the global LLMMonitor instance (or None)."""
    return global_monitor

def set_global_monitor(monitor: LLMMonitor):
    """Set the global LLMMonitor instance (used by middleware on startup)."""
    global global_monitor
    global_monitor = monitor