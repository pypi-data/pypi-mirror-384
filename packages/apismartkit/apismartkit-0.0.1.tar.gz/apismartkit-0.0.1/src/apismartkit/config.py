import typing as tp

from pydantic import BaseModel, HttpUrl


class ClientConfig(BaseModel):
    """Конфигурация клиента"""

    base_url: HttpUrl
    timeout: float = 30.0
    raise_for_status: bool = True
    max_retries: int = 3
    retry_backoff: float = 0.1
    default_headers: tp.Optional[tp.Dict[str, str]] = None
    max_concurrent: int = 10
    pool_size: int = 10

    model_config = {"extra": "forbid"}


class RetryConfig(BaseModel):
    """Конфигурация повторных попыток"""

    max_retries: int = 3
    backoff_factor: float = 0.1
    retry_status_codes: tp.List[int] = [429, 500, 502, 503, 504]

    model_config = {"extra": "forbid"}


class CircuitBreakerConfig(BaseModel):
    """Конфигурация circuit breaker"""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exceptions: tp.Tuple = (Exception,)

    model_config = {"extra": "forbid"}
