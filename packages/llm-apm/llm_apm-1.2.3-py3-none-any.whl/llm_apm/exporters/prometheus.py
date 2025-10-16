import logging
import time
import threading
from typing import Optional
from prometheus_client import (
    Counter, Histogram, Gauge, CollectorRegistry,
    generate_latest, REGISTRY, start_http_server
)
from ..core.metrics import RequestMetrics
from ..config.settings import config
import psycopg2

logger = logging.getLogger(__name__)

# small in-memory cache for resolved user names
_USER_NAME_CACHE = {}


def _get_user_name_from_db(user_id: Optional[str]) -> str:
    """Fetch user name from PostgreSQL using user_id (synchronous).
       Caches lookups in memory to avoid frequent DB queries.
    """
    if not user_id:
        return "unknown"
    # fast path cache
    if user_id in _USER_NAME_CACHE:
        return _USER_NAME_CACHE[user_id]

    # try config.postgresql_url (settings prefers POSTGRESQL_URL)
    db_url = getattr(config, "postgresql_url", "") or ""
    if not db_url:
        logger.debug("No postgresql_url configured; returning user-hash fallback")
        fallback = f"uid:{user_id[:8]}"
        _USER_NAME_CACHE[user_id] = fallback
        return fallback

    try:
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name FROM llm_apm.llm_users WHERE id = %s", (user_id,))
                row = cursor.fetchone()
                name = (row[0] if row and row[0] else f"uid:{user_id[:8]}")
                _USER_NAME_CACHE[user_id] = name
                return name
    except Exception as e:
        logger.warning("Failed to fetch user name from DB: %s", e)
        fallback = f"uid:{user_id[:8]}"
        _USER_NAME_CACHE[user_id] = fallback
        return fallback


def _coerce_model_label(raw_model: Optional[str]) -> str:
    """Convert model value to a valid Prometheus label, never returning empty or None."""
    if not raw_model:
        return "unknown"
    s = str(raw_model).strip()
    if not s or s.lower() in ("none", "null", ""):
        return "unknown"
    return s


class PrometheusExporter:
    def __init__(
        self,
        registry: Optional[CollectorRegistry] = None,
        port: Optional[int] = None,
        host: Optional[str] = None,
        start_http_server_flag: bool = True,
    ):
        self.registry = registry or (REGISTRY if start_http_server_flag else CollectorRegistry())
        self.port = port or getattr(config, "prometheus_port", 8000)
        self.host = host or getattr(config, "prometheus_host", "0.0.0.0")
        self.start_http_server_flag = start_http_server_flag
        self.server_thread = None
        self._create_metrics()

    def _create_metrics(self):
        """Define all Prometheus metrics."""
        self.request_total = Counter(
            "llm_requests_total",
            "Total number of LLM requests",
            ["model", "endpoint", "status", "experiment", "user_name"],
            registry=self.registry,
        )
        self.request_duration = Histogram(
            "llm_request_duration_seconds",
            "LLM request duration in seconds",
            ["model", "endpoint", "experiment", "user_name"],
            buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, float("inf")),
            registry=self.registry,
        )
        self.step_latency = Histogram(
            "llm_step_latency_seconds",
            "Latency for individual processing steps",
            ["model", "endpoint", "step_name", "user_name", "experiment"],
            buckets=(0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, float("inf")),
            registry=self.registry,
        )
        self.model_usage = Counter(
            "llm_model_usage_total",
            "Total usage per model",
            ["model", "experiment", "user_name"],
            registry=self.registry,
        )
        self.active_requests = Gauge(
            "llm_active_requests",
            "Number of currently active LLM requests",
            ["model", "endpoint", "experiment", "user_name"],
            registry=self.registry,
        )
        self.apm_errors_total = Counter(
            "llm_apm_errors_total",
            "Total errors",
            ["model", "endpoint", "error_type", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_success_total = Counter(
            "llm_apm_success_total",
            "Total successes",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_response_quality = Gauge(
            "llm_apm_response_quality",
            "Response quality score (0..1 or custom scale)",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_input_tokens_total = Counter(
            "llm_apm_input_tokens_total",
            "Total input tokens (prompt)",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_output_tokens_total = Counter(
            "llm_apm_output_tokens_total",
            "Total output tokens (completion)",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_tokens_request_total = Counter(
            "llm_apm_tokens_request_total",
            "Total tokens used for requests (not cache)",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_cost_request_usd_total = Counter(
            "llm_apm_cost_request_usd_total",
            "Total cost for requests (not cache)",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_tokens_cache_total = Counter(
            "llm_apm_tokens_cache_total",
            "Total tokens served from cache",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_cost_cache_usd_total = Counter(
            "llm_apm_cost_cache_usd_total",
            "Total cost attributed to cache",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_cache_hit_total = Counter(
            "llm_apm_cache_hit_total",
            "Cache hits",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_cache_miss_total = Counter(
            "llm_apm_cache_miss_total",
            "Cache misses",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_tokens_total = Counter(
            "llm_apm_tokens_total",
            "Total tokens (request + cache)",
            ["model", "endpoint", "type", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_cost_per_request_gauge = Gauge(
            "llm_apm_cost_per_request_usd",
            "Cost per request in USD (last observed)",
            ["model", "endpoint", "type", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_input_tokens_cache = Counter(
            "llm_apm_input_tokens_cache_total",
            "Input tokens from cache",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_output_tokens_cache = Counter(
            "llm_apm_output_tokens_cache_total",
            "Output tokens from cache",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_input_tokens_request = Counter(
            "llm_apm_input_tokens_request_total",
            "Input tokens from request (non-cache)",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        self.apm_output_tokens_request = Counter(
            "llm_apm_output_tokens_request_total",
            "Output tokens from request (non-cache)",
            ["model", "endpoint", "user_name", "experiment"],
            registry=self.registry,
        )
        
        # Add total_latency_ms as a histogram
        self.apm_total_latency_ms = Histogram(
            "llm_apm_total_latency_ms",
            "Total request latency in milliseconds",
            ["model", "endpoint", "user_name", "experiment"],
            buckets=(10, 50, 100, 250, 500, 1000, 2000, 5000, 10000, float("inf")),
            registry=self.registry,
        )

        logger.info(
            "Prometheus metrics created (registry=%s)",
            "global" if self.registry is REGISTRY else "private",
        )

    def start(self):
        if not self.start_http_server_flag:
            logger.info("PrometheusExporter HTTP server not started (flag disabled)")
            return
        if self.server_thread is None or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(
                target=start_http_server, args=(self.port, self.host), daemon=True
            )
            self.server_thread.start()
            logger.info(f"Prometheus server started on {self.host}:{self.port}")

    def increment_active_requests(self, model: str, endpoint: str, experiment: str = "control", user_name: str = "unknown"):
        try:
            model = _coerce_model_label(model)
            self.active_requests.labels(model=model, endpoint=endpoint, experiment=experiment, user_name=user_name).inc()
        except Exception:
            logger.debug("increment_active_requests failed", exc_info=True)

    def decrement_active_requests(self, model: str, endpoint: str, experiment: str = "control", user_name: str = "unknown"):
        try:
            model = _coerce_model_label(model)
            self.active_requests.labels(model=model, endpoint=endpoint, experiment=experiment, user_name=user_name).dec()
        except Exception:
            logger.debug("decrement_active_requests failed", exc_info=True)

    def _get_user_name(self, metrics: Optional[RequestMetrics]) -> str:
        if not metrics:
            return "unknown"
        if getattr(metrics, "user_name", None):
            return metrics.user_name
        uid = getattr(metrics, "user_id", None)
        if uid:
            name = _get_user_name_from_db(uid)
            try:
                metrics.user_name = name
            except Exception:
                pass
            return name
        return "unknown"

    def _extract_model_from_metrics(self, metrics: RequestMetrics) -> str:
        """Extract model name from metrics with multiple fallback strategies."""
        # Primary: metrics.model attribute
        model = getattr(metrics, "model", None)
        if model:
            coerced = _coerce_model_label(model)
            if coerced != "unknown":
                return coerced
        
        # Fallback 1: metadata dict
        metadata = getattr(metrics, "metadata", {})
        if isinstance(metadata, dict):
            model = metadata.get("model") or metadata.get("model_name")
            if model:
                logger.debug(f"Extracted model from metadata: {model}")
                return _coerce_model_label(model)
        
        # Fallback 2: request_data dict
        request_data = getattr(metrics, "request_data", {})
        if isinstance(request_data, dict):
            model = request_data.get("model")
            if model:
                logger.debug(f"Extracted model from request_data: {model}")
                return _coerce_model_label(model)
        
        # Fallback 3: Check steps dict
        steps = getattr(metrics, "steps", {})
        if isinstance(steps, dict):
            model = steps.get("model")
            if model:
                logger.debug(f"Extracted model from steps: {model}")
                return _coerce_model_label(model)
        
        logger.warning(
            f"No model found for request {getattr(metrics, 'request_id', 'unknown')}, "
            f"endpoint={getattr(metrics, 'endpoint', 'unknown')}"
        )
        return "unknown"

    def record_request(self, metrics: RequestMetrics) -> float:
        t0 = time.perf_counter()
        model_label = "unknown"
        try:
            user_name = self._get_user_name(metrics)
            experiment = getattr(metrics, "experiment", "control") or "control"
            model_label = self._extract_model_from_metrics(metrics)
            endpoint = metrics.endpoint or "unknown"
            status = "error" if metrics.error else "success"

            logger.debug(
                f"Recording metrics - model={model_label}, endpoint={endpoint}, "
                f"status={status}, user={user_name}, experiment={experiment}"
            )

            self.request_total.labels(
                model=model_label, 
                endpoint=endpoint, 
                status=status, 
                experiment=experiment,
                user_name=user_name
            ).inc()
            self.request_duration.labels(
                model=model_label, 
                endpoint=endpoint, 
                experiment=experiment,
                user_name=user_name
            ).observe((metrics.total_latency_ms or 0) / 1000.0)
            
            # Also record as milliseconds
            self.apm_total_latency_ms.labels(
                model=model_label,
                endpoint=endpoint,
                user_name=user_name,
                experiment=experiment
            ).observe(metrics.total_latency_ms or 0)
            
            self.model_usage.labels(
                model=model_label, 
                experiment=experiment,
                user_name=user_name
            ).inc()

            # Export step timings
            step_names = ["preprocessing", "llm_api_call", "postprocessing", "metrics_export"]
            for step_name in step_names:
                attr_name = f"{step_name}_ms"
                duration_ms = getattr(metrics, attr_name, None)
                if duration_ms is not None and duration_ms > 0:
                    try:
                        self.step_latency.labels(
                            model=model_label,
                            endpoint=endpoint,
                            step_name=step_name,
                            user_name=user_name,
                            experiment=experiment
                        ).observe(duration_ms / 1000.0)
                        logger.debug(f"Exported step '{step_name}': {duration_ms}ms")
                    except Exception as e:
                        logger.warning(f"Failed to export step '{step_name}': {e}")

            if metrics.error:
                err_type = (metrics.error_type or "unknown").lower()
                self.apm_errors_total.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    error_type=err_type, 
                    user_name=user_name, 
                    experiment=experiment
                ).inc()
            else:
                self.apm_success_total.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    user_name=user_name, 
                    experiment=experiment
                ).inc()

            if hasattr(metrics, "response_quality") and metrics.response_quality is not None:
                self.apm_response_quality.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    user_name=user_name, 
                    experiment=experiment
                ).set(float(metrics.response_quality))

            cache_hit_flag = bool(getattr(metrics, "cache_hit", False) or getattr(metrics, "from_cache", False))
            input_tokens = int(getattr(metrics, "input_tokens", 0) or 0)
            output_tokens = int(getattr(metrics, "output_tokens", 0) or 0)
            total_tokens = int(getattr(metrics, "total_tokens", None) or (input_tokens + output_tokens))
            estimated_cost = float(getattr(metrics, "estimated_cost_usd", 0.0) or 0.0)

            self.apm_input_tokens_total.labels(
                model=model_label,
                endpoint=endpoint,
                user_name=user_name,
                experiment=experiment
            ).inc(input_tokens)
            self.apm_output_tokens_total.labels(
                model=model_label,
                endpoint=endpoint,
                user_name=user_name,
                experiment=experiment
            ).inc(output_tokens)

            if cache_hit_flag:
                self.apm_cache_hit_total.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    user_name=user_name, 
                    experiment=experiment
                ).inc()
                self.apm_tokens_cache_total.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    user_name=user_name, 
                    experiment=experiment
                ).inc(total_tokens)
                self.apm_cost_cache_usd_total.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    user_name=user_name, 
                    experiment=experiment
                ).inc(estimated_cost)
                self.apm_tokens_total.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    type="cache", 
                    user_name=user_name, 
                    experiment=experiment
                ).inc(total_tokens)
                self.apm_cost_per_request_gauge.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    type="cache", 
                    user_name=user_name, 
                    experiment=experiment
                ).set(estimated_cost)
                self.apm_input_tokens_cache.labels(
                    model=model_label,
                    endpoint=endpoint,
                    user_name=user_name,
                    experiment=experiment
                ).inc(input_tokens)
                self.apm_output_tokens_cache.labels(
                    model=model_label,
                    endpoint=endpoint,
                    user_name=user_name,
                    experiment=experiment
                ).inc(output_tokens)
            else:
                self.apm_cache_miss_total.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    user_name=user_name, 
                    experiment=experiment
                ).inc()
                self.apm_tokens_request_total.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    user_name=user_name, 
                    experiment=experiment
                ).inc(total_tokens)
                self.apm_cost_request_usd_total.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    user_name=user_name, 
                    experiment=experiment
                ).inc(estimated_cost)
                self.apm_tokens_total.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    type="request", 
                    user_name=user_name, 
                    experiment=experiment
                ).inc(total_tokens)
                self.apm_cost_per_request_gauge.labels(
                    model=model_label, 
                    endpoint=endpoint, 
                    type="request", 
                    user_name=user_name, 
                    experiment=experiment
                ).set(estimated_cost)
                self.apm_input_tokens_request.labels(
                    model=model_label,
                    endpoint=endpoint,
                    user_name=user_name,
                    experiment=experiment
                ).inc(input_tokens)
                self.apm_output_tokens_request.labels(
                    model=model_label,
                    endpoint=endpoint,
                    user_name=user_name,
                    experiment=experiment
                ).inc(output_tokens)

        except Exception:
            logger.exception("Failed to record Prometheus metrics")
        finally:
            return time.perf_counter() - t0

    def get_metrics(self) -> str:
        try:
            return generate_latest(self.registry).decode("utf-8")
        except Exception:
            logger.exception("Failed to generate Prometheus metrics")
            return ""

    def shutdown(self):
        logger.info("Prometheus exporter shutdown")


# Global exporter instance
_GLOBAL_EXPORTER: Optional[PrometheusExporter] = None


def set_global_exporter(exporter: PrometheusExporter):
    global _GLOBAL_EXPORTER
    _GLOBAL_EXPORTER = exporter


def get_global_exporter() -> Optional[PrometheusExporter]:
    return _GLOBAL_EXPORTER