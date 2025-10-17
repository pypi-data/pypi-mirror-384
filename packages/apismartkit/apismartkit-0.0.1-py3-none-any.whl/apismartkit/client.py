import asyncio
import logging
import typing as tp
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import httpx
import tenacity

from .config import CircuitBreakerConfig, ClientConfig, RetryConfig
from .exceptions import APIClientException, RequestAPIException, ResponseAPIException
from .middlewares import (
    BaseMiddleware,
    CacheMiddleware,
    CircuitBreakerMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    RetryMiddleware,
)
from .request import Request, RequestBuilder
from .response import Response


class BaseAPIClient(ABC):
    """Базовый API клиент с общей функциональностью"""

    def __init__(
        self,
        config: ClientConfig,
        *,
        middlewares: tp.Optional[tp.List[BaseMiddleware]] = None,
        **client_kwargs,
    ):
        self.config = config
        self._client_kwargs = client_kwargs

        # Ленивая инициализация клиента
        self._client: tp.Optional[tp.Union[httpx.Client, httpx.AsyncClient]] = None

        # Настройка middleware
        self._middlewares = list(middlewares) if middlewares else []

        # Добавляем стандартные middleware если не предоставлены
        self._add_default_middlewares()

        self._logger = logging.getLogger(self.__class__.__name__)

    def _add_default_middlewares(self) -> None:
        """Добавляет middleware по умолчанию"""
        if not any(isinstance(m, RetryMiddleware) for m in self._middlewares):
            retry_config = RetryConfig(max_retries=self.config.max_retries, backoff_factor=self.config.retry_backoff)
            self._middlewares.append(RetryMiddleware(config=retry_config))

        if not any(isinstance(m, LoggingMiddleware) for m in self._middlewares):
            self._middlewares.append(LoggingMiddleware())

        if not any(isinstance(m, CircuitBreakerMiddleware) for m in self._middlewares):
            circuit_config = CircuitBreakerConfig()
            self._middlewares.append(CircuitBreakerMiddleware(config=circuit_config))

        if not any(isinstance(m, MetricsMiddleware) for m in self._middlewares):
            self._middlewares.append(MetricsMiddleware())

        if not any(isinstance(m, CacheMiddleware) for m in self._middlewares):
            self._middlewares.append(CacheMiddleware())

    @property
    @abstractmethod
    def client(self) -> tp.Union[httpx.Client, httpx.AsyncClient]:
        """Получить или создать HTTP клиент (ленивая инициализация)"""
        pass

    @abstractmethod
    def _create_client(self) -> tp.Union[httpx.Client, httpx.AsyncClient]:
        """Создать экземпляр HTTP клиента"""
        pass

    @abstractmethod
    def _apply_middleware_request(self, request: Request) -> Request:
        """Применить request middleware"""
        pass

    @abstractmethod
    def _apply_middleware_response(self, response: Response) -> Response:
        """Применить response middleware"""
        pass

    @abstractmethod
    def _handle_error(self, error: APIClientException) -> None:
        """Обработать ошибку через middleware"""
        pass

    def build_request(self, endpoint: "Endpoint") -> RequestBuilder:  # noqa: F821
        """Создать builder запроса для endpoint"""
        return RequestBuilder(endpoint)

    def _should_retry(self, error: BaseException) -> bool:
        """Определяет, нужно ли повторять запрос при ошибке"""
        retry_middleware = next((m for m in self._middlewares if isinstance(m, RetryMiddleware)), None)
        if retry_middleware:
            return retry_middleware.should_retry(error)
        return False

    def _get_retry_config(self) -> tp.Dict[str, tp.Any]:
        """Получить конфигурацию повторных попыток"""
        retry_middleware = next((m for m in self._middlewares if isinstance(m, RetryMiddleware)), None)

        if not retry_middleware:
            return {}

        return {
            "reraise": True,
            "stop": tenacity.stop_after_attempt(retry_middleware.config.max_retries),
            "wait": tenacity.wait_exponential(
                multiplier=retry_middleware.config.backoff_factor,
                min=retry_middleware.config.backoff_factor,
                max=retry_middleware.config.backoff_factor * 10,
            ),
            "retry": tenacity.retry_if_exception(self._should_retry),
        }

    def get_metrics(self) -> tp.Dict[str, tp.Any]:
        """Получить метрики из MetricsMiddleware"""
        metrics_middleware = next((m for m in self._middlewares if isinstance(m, MetricsMiddleware)), None)
        if metrics_middleware:
            return metrics_middleware.get_metrics()
        return {}


class APIClient(BaseAPIClient):
    """Синхронный API клиент"""

    def __init__(
        self, config: ClientConfig, *, middlewares: tp.Optional[tp.List[BaseMiddleware]] = None, **client_kwargs
    ):
        super().__init__(config, middlewares=middlewares, **client_kwargs)
        # Сразу создаем клиент для синхронного использования
        self._client = self._create_client()

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self.config.timeout,
            base_url=str(self.config.base_url),
            headers=self.config.default_headers,
            **self._client_kwargs,
        )

    def close(self) -> None:
        """Закрыть клиент и освободить ресурсы"""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _apply_middleware_request(self, request: Request) -> Request:
        """Применить request middleware"""
        current = request
        for middleware in self._middlewares:
            current = middleware.on_request_sync(current)
        return current

    def _apply_middleware_response(self, response: Response) -> Response:
        """Применить response middleware"""
        current = response
        for middleware in self._middlewares:
            current = middleware.on_response_sync(current)
        return current

    def _handle_error(self, error: APIClientException) -> None:
        """Обработать ошибку через middleware"""
        for middleware in self._middlewares:
            middleware.on_error_sync(error)

    def _execute(self, request: Request) -> Response:
        """Выполнить одиночный запрос"""
        try:
            # Применяем middleware
            request = self._apply_middleware_request(request)

            # Собираем данные запроса
            method, path, params, data, headers = request.build_request()
            url = urljoin(str(self.config.base_url) + "/", path.lstrip("/"))

            # Выполняем запрос
            http_response = self.client.request(
                method=method,
                url=url,
                params=params,
                content=data if isinstance(data, (str, bytes)) else None,
                data=data if not isinstance(data, (str, bytes)) else None,
                headers=headers,
                timeout=request.timeout or self.config.timeout,
            )

            # Создаем ответ
            response = Response(http_response, request)

            # Применяем middleware и возвращаем
            return self._apply_middleware_response(response)

        except Exception as exc:
            # Преобразуем в APIClientException если нужно
            if not isinstance(exc, APIClientException):
                if isinstance(exc, httpx.HTTPStatusError):
                    exc = ResponseAPIException(f"HTTP error: {exc}", status_code=exc.response.status_code)
                else:
                    exc = RequestAPIException(f"Request failed: {exc}")

            # Обрабатываем ошибку через middleware
            self._handle_error(exc)
            raise exc

    def execute(self, request: Request) -> Response:
        """Выполнить запрос с логикой повторных попыток"""

        retry_config = self._get_retry_config()

        def _execute_with_retry_and_status():
            """Внутренняя функция для повторных попыток включая проверку статуса"""
            response = self._execute(request)

            # Проверяем статус и при необходимости вызываем исключение
            if self.config.raise_for_status:
                try:
                    response.raise_for_status()
                except Exception as exc:
                    # Преобразуем в APIClientException для механизма повторных попыток
                    if not isinstance(exc, APIClientException):
                        if isinstance(exc, httpx.HTTPStatusError):
                            exc = ResponseAPIException(f"HTTP error: {exc}", status_code=exc.response.status_code)
                        else:
                            exc = RequestAPIException(f"Status check failed: {exc}")
                    raise exc
            return response

        if retry_config:

            @tenacity.retry(**retry_config)
            def _execute_retry():
                return _execute_with_retry_and_status()

            response = _execute_retry()
        else:
            response = _execute_with_retry_and_status()

        if self.config.raise_for_status:
            response.raise_for_status()

        return response

    def paginate(self, request: Request) -> tp.Generator[Response, None, None]:
        """Пагинировать через все страницы результатов"""
        if not request.paginator:
            request = request.with_pagination()

        current_request = request

        while True:
            response = self.execute(current_request)
            yield response

            # Получаем следующую страницу
            next_request = response.as_paginated().paginator.get_next_page()
            if next_request is None:
                break

            current_request = next_request


class AsyncAPIClient(BaseAPIClient):
    """Асинхронный API клиент"""

    def __init__(
        self, config: ClientConfig, *, middlewares: tp.Optional[tp.List[BaseMiddleware]] = None, **client_kwargs
    ):
        super().__init__(config, middlewares=middlewares, **client_kwargs)

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=self.config.timeout,
            base_url=str(self.config.base_url),
            headers=self.config.default_headers,
            **self._client_kwargs,
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncAPIClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def _apply_middleware_request(self, request: Request) -> Request:
        """Применить request middleware"""
        current = request
        for middleware in self._middlewares:
            current = await middleware.on_request_async(current)
        return current

    async def _apply_middleware_response(self, response: Response) -> Response:
        """Применить response middleware"""
        current = response
        for middleware in self._middlewares:
            current = await middleware.on_response_async(current)
        return current

    async def _handle_error(self, error: APIClientException) -> None:
        """Обработать ошибку через middleware"""
        for middleware in self._middlewares:
            await middleware.on_error_async(error)

    async def _execute(self, request: Request) -> Response:
        """Выполнить одиночный асинхронный запрос"""
        try:
            request = await self._apply_middleware_request(request)

            method, path, params, data, headers = request.build_request()
            url = urljoin(str(self.config.base_url) + "/", path.lstrip("/"))

            http_response = await self.client.request(
                method=method,
                url=url,
                params=params,
                content=data if isinstance(data, (str, bytes)) else None,
                data=data if not isinstance(data, (str, bytes)) else None,
                headers=headers,
                timeout=request.timeout or self.config.timeout,
            )

            response = Response(http_response, request)
            return await self._apply_middleware_response(response)

        except Exception as exc:
            if not isinstance(exc, APIClientException):
                if isinstance(exc, httpx.HTTPStatusError):
                    exc = ResponseAPIException(
                        f"HTTP error: {exc}", status_code=exc.response.status_code, request_id=request.request_id
                    )
                else:
                    exc = RequestAPIException(f"Request failed: {exc}", request_id=request.request_id)

            await self._handle_error(exc)
            raise

    async def execute(self, request: Request) -> Response:
        """Выполнить асинхронный запрос с логикой повторных попыток"""

        retry_config = self._get_retry_config()

        async def _execute_with_retry_and_status():
            """Внутренняя функция для повторных попыток включая проверку статуса"""
            response = await self._execute(request)

            # Проверяем статус и при необходимости вызываем исключение
            if self.config.raise_for_status:
                try:
                    response.raise_for_status()
                except Exception as exc:
                    # Преобразуем в APIClientException для механизма повторных попыток
                    if not isinstance(exc, APIClientException):
                        if isinstance(exc, httpx.HTTPStatusError):
                            exc = ResponseAPIException(f"HTTP error: {exc}", status_code=exc.response.status_code)
                        else:
                            exc = RequestAPIException(f"Status check failed: {exc}")
                    raise exc
            return response

        if retry_config:

            @tenacity.retry(**retry_config)
            async def _execute_retry():
                return await _execute_with_retry_and_status()

            response = await _execute_retry()
        else:
            response = await _execute_with_retry_and_status()

        if self.config.raise_for_status:
            response.raise_for_status()

        return response

    async def paginate(self, request: Request) -> tp.AsyncGenerator[Response, None]:
        """Асинхронная пагинация через все страницы результатов"""
        if not request.paginator:
            request = request.with_pagination()

        current_request = request

        while True:
            response = await self.execute(current_request)
            yield response

            next_request = response.as_paginated().paginator.get_next_page()
            if next_request is None:
                break

            current_request = next_request

    async def execute_bulk(
        self, requests: tp.List[Request], max_concurrent: tp.Optional[int] = None
    ) -> tp.List[Response]:
        """Выполнить несколько запросов конкурентно с ограничением"""
        max_workers = max_concurrent or self.config.max_concurrent
        semaphore = asyncio.Semaphore(max_workers)

        async def _execute_with_semaphore(req: Request) -> Response:
            async with semaphore:
                return await self.execute(req)

        tasks = [_execute_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Обрабатываем исключения
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                if self.config.raise_for_status:
                    raise result
                # Создаем ответ с ошибкой
                responses.append(
                    Response(
                        httpx.Response(500, content=str(result).encode()),
                        requests[i],
                    )
                )
            else:
                responses.append(result)

        return responses

    async def stream(self, request: Request) -> tp.AsyncGenerator[bytes, None]:
        """Потоковая передача содержимого ответа"""
        request = await self._apply_middleware_request(request)

        method, path, params, data, headers = request.build_request()
        url = urljoin(str(self.config.base_url) + "/", path.lstrip("/"))

        async with self.client.stream(
            method=method,
            url=url,
            params=params,
            content=data,
            headers=headers,
            timeout=request.timeout or self.config.timeout,
        ) as response:
            if self.config.raise_for_status:
                response.raise_for_status()

            async for chunk in response.aiter_bytes():
                yield chunk
