import logging
import time
import typing as tp
from datetime import UTC, datetime, timedelta
from http import HTTPMethod

from .config import CircuitBreakerConfig, RetryConfig
from .enums import CircuitState
from .exceptions import APIClientException, CircuitBreakerOpen, RequestAPIException
from .interfaces import IMiddleware
from .request import Request
from .response import Response


class BaseMiddleware(IMiddleware):
    """Базовый класс middleware"""

    def on_request_sync(self, request: Request):
        """Вызывается перед отправкой запроса"""
        return request

    async def on_request_async(self, request: Request) -> Request:
        """Вызывается перед отправкой запроса"""
        return request

    def on_response_sync(self, response: Response) -> Response:
        """Вызывается после получения ответа"""
        return response

    async def on_response_async(self, response: Response) -> Response:
        """Вызывается после получения ответа"""
        return response

    def on_error_sync(self, error: APIClientException) -> None:
        """Вызывается при возникновении ошибки"""
        pass

    async def on_error_async(self, error: APIClientException) -> None:
        """Вызывается при возникновении ошибки"""
        pass


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования с фильтрацией чувствительных данных"""

    def __init__(
        self,
        logger: tp.Optional[logging.Logger] = None,
        sensitive_headers: tp.Union[None, set, list, tuple] = None,
        sensitive_params: tp.Union[None, set, list, tuple] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)

        if sensitive_headers and not isinstance(sensitive_headers, (set, list, tuple)):
            raise TypeError("sensitive_headers must be a set, a tuple or a list")

        if sensitive_params and not isinstance(sensitive_params, (set, list, tuple)):
            raise TypeError("sensitive_params must be a set, a tuple or a list")

        self.sensitive_headers = sensitive_headers or {"authorization", "token", "password", "api-key", "cookie"}
        self.sensitive_params = sensitive_params or {"password", "secret", "token"}

    def _sanitize_headers(self, headers: tp.Dict[str, str]) -> tp.Dict[str, str]:
        return {
            k: "***" if k.lower() in {header.lower() for header in self.sensitive_headers} else v
            for k, v in headers.items()
        }

    def _sanitize_params(self, params: tp.Dict[str, tp.Any]) -> tp.Dict[str, tp.Any]:
        return {
            k: "***" if k.lower() in {param.lower() for param in self.sensitive_params} else v
            for k, v in params.items()
        }

    def _log_request(self, request: Request):
        method, url, params, data, headers = request.build_request()

        self.logger.info(
            "Request: %s %s\nParams: %s\nHeaders: %s",
            method,
            url,
            self._sanitize_params(params),
            self._sanitize_headers(headers),
        )

    def _log_response(self, response: Response):
        self.logger.info(
            "Response: %s %s\nStatus: %d",
            response.request.endpoint.method,
            response.request.endpoint.path,
            response.status_code,
        )

    def _log_error(self, error: APIClientException):
        self.logger.error("API Error: %s", error.message)

    def on_request_sync(self, request: Request) -> Request:
        self._log_request(request)
        return request

    async def on_request_async(self, request: Request) -> Request:
        self._log_request(request)
        return request

    def on_response_sync(self, response: Response) -> Response:
        self._log_response(response)
        return response

    async def on_response_async(self, response: Response) -> Response:
        self._log_response(response)
        return response

    def on_error_sync(self, error: APIClientException) -> None:
        self._log_error(error)

    async def on_error_async(self, error: APIClientException) -> None:
        self._log_error(error)


class RetryMiddleware(BaseMiddleware):
    """
    Middleware для повторных попыток запроса
    """

    def __init__(
        self,
        config: tp.Optional[RetryConfig] = None,
    ):
        self.config = config or RetryConfig()
        self._retry_condition = self._default_retry_condition

    def _default_retry_condition(self, error: Exception) -> bool:
        """Условие по умолчанию для повторной попытки"""
        if isinstance(error, APIClientException):
            if error.status_code and error.status_code in self.config.retry_status_codes:
                return True
            # Также повторяем для сетевых ошибок и таймаутов
            if isinstance(error, RequestAPIException) and error.status_code is None:
                return True
        return False

    def on_error_sync(self, response: Response) -> Response:
        """Обработка ошибок для повторных попыток"""
        pass

    async def on_error_async(self, error: APIClientException) -> None:
        """Обработка ошибок для повторных попыток"""
        pass

    def should_retry(self, error: BaseException) -> bool:
        """Проверяет, требует ли ошибка повторной попытки"""
        return self._retry_condition(error)

    def get_retry_delay(self, attempt: int) -> float:
        """Вычисляет задержку для попытки"""
        return self.config.backoff_factor * (2 ** (attempt - 1))


class CircuitBreakerMiddleware(BaseMiddleware):
    """Circuit Breaker middleware для предотвращения каскадных отказов"""

    def __init__(self, config: tp.Optional[CircuitBreakerConfig] = None, name: str = "default"):
        self.config = config or CircuitBreakerConfig()
        self.name = name

        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time: tp.Optional[datetime] = None
        self._success_count = 0

    def _on_request(self, request: Request) -> Request:
        if self._state == CircuitState.OPEN:
            if self._should_try_recovery():
                self._state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpen(self.name, request.request_id)

        return request

    def _on_response(self, response: Response) -> Response:
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.failure_threshold:
                self._reset()

        elif response.status_code >= 500:
            self._record_failure()

        return response

    def _on_error(self, error: APIClientException):
        if isinstance(error, CircuitBreakerOpen):
            return

        self._record_failure()

    def on_request_sync(self, request: Request) -> Request:
        return self._on_request(request)

    async def on_request_async(self, request: Request) -> Request:
        return self._on_request(request)

    def on_response_sync(self, response: Response) -> Response:
        return self._on_response(response)

    async def on_response_async(self, response: Response) -> Response:
        return self._on_response(response)

    def on_error_sync(self, error: APIClientException) -> None:
        self._on_error(error)

    async def on_error_async(self, error: APIClientException) -> None:
        self._on_error(error)

    def _record_failure(self) -> None:
        """Записывает неудачу и обновляет состояние"""
        self._failure_count += 1
        self._last_failure_time = datetime.now(UTC)

        if self._failure_count >= self.config.failure_threshold:
            self._state = CircuitState.OPEN

    def _should_try_recovery(self) -> bool:
        """Проверяет, можно ли попробовать восстановление"""
        if self._last_failure_time and datetime.now(UTC) - self._last_failure_time > timedelta(
            seconds=self.config.recovery_timeout
        ):
            return True
        return False

    def _reset(self) -> None:
        """Сбрасывает состояние circuit breaker"""
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count


class MetricsMiddleware(BaseMiddleware):
    """Middleware для сбора метрик"""

    def __init__(self):
        self.metrics: tp.Dict[str, tp.Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_duration": 0.0,
            "requests_by_status": {},
            "circuit_breaker_state": {},
        }
        self._durations: tp.List[float] = []

    def _on_request(self, request: Request) -> Request:
        request.metrics["start_time"] = time.time()
        self.metrics["total_requests"] += 1
        return request

    def _on_response(self, response: Response) -> Response:
        duration = time.time() - response.request.metrics["start_time"]
        self._durations.append(duration)

        status_code = response.status_code
        self.metrics["requests_by_status"][status_code] = self.metrics["requests_by_status"].get(status_code, 0) + 1

        if 200 <= status_code < 300:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1

        # Обновляем среднюю продолжительность
        self.metrics["average_duration"] = sum(self._durations) / len(self._durations)

        return response

    def _on_error(self, error: APIClientException):
        self.metrics["failed_requests"] += 1

    def on_request_sync(self, request: Request) -> Request:
        return self._on_request(request)

    async def on_request_async(self, request: Request) -> Request:
        return self._on_request(request)

    def on_response_sync(self, response: Response) -> Response:
        return self._on_response(response)

    async def on_response_async(self, response: Response) -> Response:
        return self._on_response(response)

    def on_error_sync(self, error: APIClientException) -> None:
        self._on_error(error)

    async def on_error_async(self, error: APIClientException) -> None:
        self._on_error(error)

    def get_metrics(self) -> tp.Dict[str, tp.Any]:
        """Возвращает текущие метрики"""
        return self.metrics.copy()


class CacheMiddleware(BaseMiddleware):
    """Middleware для кэширования GET запросов"""

    def __init__(self, default_ttl: int = 300):
        self._cache: tp.Dict[str, tuple[tp.Any, float]] = {}
        self.default_ttl = default_ttl

    def _on_response(self, response: Response) -> Response:
        if (
            response.request.endpoint.method == "GET"
            and response.status_code == 200
            and self._should_cache(response.request)
        ):
            cache_key = self._get_cache_key(response.request)
            self._cache[cache_key] = (
                response._raw.content,  # Кэшируем сырой контент
                time.time() + self.default_ttl,
            )

        return response

    def _on_request(self, request: Request) -> Request:
        if request.endpoint.method == HTTPMethod.GET.value and self._should_cache(request):
            cache_key = self._get_cache_key(request)
            if cache_key in self._cache:
                cached_data, expiry = self._cache[cache_key]
                if time.time() < expiry:
                    # Помечаем запрос как кэшированный
                    request.metrics["cached"] = True
                    # Здесь нужно вернуть кэшированный response
                    # Для упрощения пропускаем эту логику
        return request

    def on_request_sync(self, request: Request) -> Request:
        return self._on_request(request)

    async def on_request_async(self, request: Request) -> Request:
        return self._on_request(request)

    def on_response_sync(self, response: Response) -> Response:
        return self._on_response(response)

    async def on_response_async(self, response: Response) -> Response:
        return self._on_response(response)

    def _should_cache(self, request: Request) -> bool:
        """Определяет, нужно ли кэшировать запрос"""
        # Можно добавить логику исключения определенных путей
        return True

    def _get_cache_key(self, request: Request) -> str:
        """Генерирует ключ кэша для запроса"""
        method, path, params, data, headers = request.build_request()
        return f"{method}:{path}:{str(params)}"

    def clear_cache(self) -> None:
        """Очищает кэш"""
        self._cache.clear()
