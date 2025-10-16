# llm_apm/config/settings.py
from typing import Optional, Dict, Any, List
import logging
import time

logger = logging.getLogger(__name__)

_pydantic_v2 = False
pv = None
try:
    import pydantic
    pv = getattr(pydantic, "__version__", None)
    if pv:
        major = int(pv.split(".")[0])
        _pydantic_v2 = major >= 2
except Exception:
    pv = None

# Ensure Field is available for both pydantic v1 and v2 usage
if _pydantic_v2:
    from pydantic import Field, SecretStr, validator
    from pydantic_settings import BaseSettings  # type: ignore
else:
    from pydantic import BaseSettings, Field, SecretStr, validator  # type: ignore


class LLMAPMConfig(BaseSettings):
    """Configuration class for LLM-APM settings."""
    # Monitoring settings
    enable_monitoring: bool = True
    sampling_rate: float = 1.0
    per_endpoint_sampling: Dict[str, float] = {}
    metrics_endpoint: str = "/metrics"

    # Postgres settings (component fields)
    postgresql_host: Optional[str] = None
    postgresql_port: Optional[int] = None
    postgresql_database: Optional[str] = None
    postgresql_username: Optional[str] = None
    postgresql_password: Optional[str] = None

    # NEW: Accept a single DATABASE/POSTGRES URL environment variable (preferred)
    postgresql_url_direct: Optional[str] = Field(None, env="POSTGRESQL_URL")
    database_url_direct: Optional[str] = Field(None, env="DATABASE_URL")

    # Prometheus settings
    prometheus_port: int = 8000
    prometheus_host: str = "0.0.0.0"

    # Model routing — read from env
    default_model: Optional[str] = Field(None, env="DEFAULT_MODEL")
    cheap_model: Optional[str] = Field(None, env="CHEAP_MODEL")
    high_quality_model: Optional[str] = Field(None, env="HIGH_QUALITY_MODEL")

    # Auto-discovery settings
    enable_auto_discovery: bool = Field(True, env="ENABLE_AUTO_DISCOVERY")
    discovery_interval_seconds: int = Field(3600, env="DISCOVERY_INTERVAL")
    fallback_pricing_strategy: str = Field("conservative", env="FALLBACK_PRICING_STRATEGY")

    # Default pricing for unknown models
    default_input_price_per_1k: float = Field(0.003, env="DEFAULT_INPUT_PRICE_PER_1K")
    default_output_price_per_1k: float = Field(0.006, env="DEFAULT_OUTPUT_PRICE_PER_1K")

    # Token pricing
    token_pricing: Dict[str, Dict[str, float]] = {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-35-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "gemini-pro": {"input": 0.0005, "output": 0.0015},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
        "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
        "text-davinci-003": {"input": 0.02, "output": 0.02},
        "text-curie-001": {"input": 0.002, "output": 0.002},
        "tinyllama:latest": {"input": 0.00005, "output": 0.0001},
        "llama3": {"input": 0.0005, "output": 0.0015},
        "llama3:latest": {"input": 0.0005, "output": 0.0015},
        "olama-large": {"input": 0.0008, "output": 0.0025},
        "olama-mini": {"input": 0.00012, "output": 0.00045},
        "gemini-1.5-mini": {"input": 0.00008, "output": 0.00032},
        "gemini-ultra-1": {"input": 0.0025, "output": 0.0075},
    }

    # Model family patterns
    model_family_patterns: Dict[str, Dict[str, float]] = {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4": {"input": 0.02, "output": 0.04},
        "gpt-3.5": {"input": 0.001, "output": 0.002},
        "claude-3": {"input": 0.001, "output": 0.005},
        "gemini": {"input": 0.001, "output": 0.003},
        "mini": {"input": 0.0002, "output": 0.0008},
        "turbo": {"input": 0.002, "output": 0.004},
        "large": {"input": 0.01, "output": 0.03},
        "olama": {"input": 0.0005, "output": 0.0018},
    }

    # Alerts / logging
    error_rate_threshold: float = 0.05
    latency_threshold_ms: int = 3000
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    metrics_jwt_secret: Optional[SecretStr] = Field(None, env="METRICS_JWT_SECRET")

    quota_max_requests: int = Field(10, env="QUOTA_MAX_REQUESTS")
    quota_window_seconds: int = Field(3600, env="QUOTA_WINDOW_SECONDS")
    quota_cooldown_seconds: int = Field(3600, env="QUOTA_COOLDOWN_SECONDS")

    # Runtime discovered models storage
    _discovered_models: Dict[str, Dict[str, Any]] = {}
    _last_discovery: float = 0

    @validator("sampling_rate")
    def validate_sampling_rate(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("sampling_rate must be between 0.0 and 1.0")
        return v

    def get_endpoint_sampling(self, endpoint: Optional[str]) -> float:
        if not endpoint:
            return float(self.sampling_rate)
        if endpoint in self.per_endpoint_sampling:
            return float(self.per_endpoint_sampling[endpoint])
        for k, v in self.per_endpoint_sampling.items():
            if k and k in endpoint:
                return float(v)
        return float(self.sampling_rate)

    @property
    def postgresql_url(self) -> str:
        """
        Prefer a direct POSTGRESQL_URL/DATABASE_URL if provided. Otherwise compose from pieces.
        """
        direct = self.postgresql_url_direct or self.database_url_direct
        if direct:
            return str(direct)

        if not (
            self.postgresql_host
            and self.postgresql_port
            and self.postgresql_database
            and self.postgresql_username
            and self.postgresql_password
        ):
            return ""
        return (
            f"postgresql://{self.postgresql_username}:{self.postgresql_password}"
            f"@{self.postgresql_host}:{self.postgresql_port}/{self.postgresql_database}"
        )

    def get_token_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = self.get_model_pricing(model)
        return (input_tokens / 1000) * pricing["input"] + (output_tokens / 1000) * pricing["output"]

    def get_model_pricing(self, model: str) -> Dict[str, float]:
        if not model:
            model = self.default_model or "gpt-4o-mini"
        model_lower = model.lower().strip()
        if model_lower in self.token_pricing:
            return self.token_pricing[model_lower]
        if model_lower in self._discovered_models:
            discovered = self._discovered_models[model_lower]
            if "pricing" in discovered:
                return discovered["pricing"]
        family_pricing = self._match_model_family(model_lower)
        if family_pricing:
            logger.info(f"Using family pricing for {model}: {family_pricing}")
            return family_pricing
        fallback = self._get_fallback_pricing(model_lower)
        logger.warning(f"Using fallback pricing for unknown model {model}: {fallback}")
        return fallback

    def _match_model_family(self, model_lower: str) -> Optional[Dict[str, float]]:
        sorted_patterns = sorted(
            self.model_family_patterns.items(), key=lambda x: len(x[0]), reverse=True
        )
        for pattern, pricing in sorted_patterns:
            if pattern.lower() in model_lower:
                return pricing.copy()
        return None

    def _get_fallback_pricing(self, model_lower: str) -> Dict[str, float]:
        if self.fallback_pricing_strategy == "conservative":
            return {"input": 0.01, "output": 0.03}
        elif self.fallback_pricing_strategy == "aggressive":
            return {"input": 0.001, "output": 0.003}
        else:
            return {
                "input": self.default_input_price_per_1k,
                "output": self.default_output_price_per_1k,
            }

    def register_discovered_model(self, model: str, pricing: Dict[str, float], metadata: Optional[Dict[str, Any]] = None):
        self._discovered_models[model.lower()] = {
            "pricing": pricing,
            "metadata": metadata or {},
            "discovered_at": time.time(),
        }
        logger.info(f"Registered discovered model: {model} with pricing {pricing}")

    def get_discovered_models(self) -> Dict[str, Dict[str, Any]]:
        return self._discovered_models.copy()

    def should_rediscover_models(self) -> bool:
        if not self.enable_auto_discovery:
            return False
        return time.time() - self._last_discovery > self.discovery_interval_seconds

    def mark_discovery_complete(self):
        self._last_discovery = time.time()

    def get_all_known_models(self) -> List[str]:
        static_models = set(self.token_pricing.keys())
        discovered_models = set(self._discovered_models.keys())
        return list(static_models | discovered_models)

    def estimate_model_tier(self, model: str) -> str:
        pricing = self.get_model_pricing(model)
        input_price = pricing["input"]
        if input_price <= 0.001:
            return "budget"
        elif input_price <= 0.005:
            return "standard"
        elif input_price <= 0.015:
            return "premium"
        else:
            return "enterprise"

    def get_models_by_tier(self, tier: str) -> List[str]:
        all_models = self.get_all_known_models()
        return [model for model in all_models if self.estimate_model_tier(model) == tier]

    # pydantic v1 compatibility (inner Config)
    class Config:
        env_prefix = "LLM_APM_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False


# Global configuration instance
config = LLMAPMConfig()
_global_config = config


def get_config() -> LLMAPMConfig:
    return _global_config


def set_config(new_config: LLMAPMConfig) -> None:
    global _global_config
    _global_config = new_config


def register_model_pricing(model: str, input_price: float, output_price: float, metadata: Optional[Dict[str, Any]] = None):
    pricing = {"input": input_price, "output": output_price}
    config.register_discovered_model(model, pricing, metadata)


def bulk_register_models(models: Dict[str, Dict[str, float]]):
    for model, pricing in models.items():
        config.register_discovered_model(model, pricing)


def register_common_models():
    additional_models = {
        "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
        "gpt-4-vision-preview": {"input": 0.01, "output": 0.03},
        "code-davinci-002": {"input": 0.02, "output": 0.02},
    }
    bulk_register_models(additional_models)


def _debug_env_loaded():
    try:
        return {
            "pydantic_version": pv,
            "redis_url": bool(config.redis_url),
            "metrics_jwt_secret_set": bool(config.metrics_jwt_secret),
            "default_model": config.default_model,
            "enable_auto_discovery": config.enable_auto_discovery,
            "fallback_strategy": config.fallback_pricing_strategy,
            "known_models_count": len(config.get_all_known_models()),
            "env_prefix": "LLM_APM_",
        }
    except Exception:
        return {}
# End of file
