import time
import typing as tp
from dataclasses import dataclass
from functools import cached_property

import httpx
from pydantic import BaseModel, ValidationError

from .enums import ResponseType
from .exceptions import ResponseTypeError, ResponseValidationError
from .request import Request
from .schemas import PaginationMeta

T = tp.TypeVar("T", bound=BaseModel)


@dataclass
class PaginatedResponse(tp.Generic[T]):
    """Контейнер для пагинированного ответа"""

    items: tp.List[T]
    meta: PaginationMeta
    paginator: tp.Optional["Paginator"] = None  # noqa: F821


class Response(tp.Generic[T]):
    """
    Улучшенный API response с умным парсингом и валидацией
    """

    def __init__(self, raw: httpx.Response, request: Request):
        self._raw = raw
        self._request = request
        self._processed = False
        self._cached_data: tp.Optional[tp.Union[T, tp.List[T], PaginatedResponse[T], tp.Any]] = None
        self._duration: tp.Optional[float] = None
        self._start_time = time.time()

    @cached_property
    def request(self) -> Request:
        return self._request

    @cached_property
    def duration(self) -> float:
        """Время выполнения запроса в секундах"""
        if self._duration is None:
            self._duration = time.time() - self._start_time
        return self._duration

    @cached_property
    def _parsed_content(self) -> tp.Any:
        """Парсинг содержимого ответа на основе content type"""
        endpoint = self._request.endpoint

        if endpoint.response_type == ResponseType.RAW:
            return self._raw.content

        if endpoint.response_type == ResponseType.STREAM:
            return self._raw

        # Пробуем JSON для не-сырых ответов
        try:
            return self._raw.json()
        except ValueError:
            # Fallback на text/bytes
            try:
                text = self._raw.text
                return text if text else self._raw.content
            except Exception:
                return self._raw.content

    def _ensure_processed(self) -> None:
        """Обработка данных ответа при первом доступе"""
        if self._processed:
            return

        try:
            endpoint = self._request.endpoint
            parsed = self._parsed_content

            if endpoint.response_type == ResponseType.RAW:
                self._cached_data = parsed

            elif endpoint.response_type == ResponseType.SINGLE_OBJECT:
                self._cached_data = self._parse_single_object(parsed)

            elif endpoint.response_type == ResponseType.PLAIN_LIST:
                self._cached_data = self._parse_plain_list(parsed)

            elif endpoint.response_type == ResponseType.PAGINATED_LIST:
                self._cached_data = self._parse_paginated_list(parsed)

            else:
                self._cached_data = parsed

            self._processed = True

        except (ResponseValidationError, ResponseTypeError):
            raise
        except Exception as exc:
            raise ResponseValidationError(
                f"Response processing failed: {exc}", request_id=self._request.request_id
            ) from exc

    def _parse_single_object(self, parsed: tp.Any) -> tp.Any:
        """Парсинг одиночного объекта"""
        endpoint = self._request.endpoint

        if endpoint.response_schema is None:
            return parsed

        try:
            if isinstance(parsed, BaseModel):
                return parsed
            return endpoint.response_schema.model_validate(parsed)
        except ValidationError as exc:
            raise ResponseValidationError(
                f"Single object validation failed: {exc}", request_id=self._request.request_id
            ) from exc

    def _parse_plain_list(self, parsed: tp.Any) -> tp.List[T]:
        """Парсинг простого списка"""
        endpoint = self._request.endpoint

        if not isinstance(parsed, list):
            parsed = [parsed] if parsed is not None else []

        if endpoint.response_schema is None:
            return parsed  # type: ignore

        try:
            return [endpoint.response_schema.model_validate(item) for item in parsed]
        except ValidationError as exc:
            raise ResponseValidationError(
                f"List validation failed: {exc}", request_id=self._request.request_id
            ) from exc

    def _parse_paginated_list(self, parsed: tp.Any) -> PaginatedResponse[T]:
        """Парсинг пагинированного списка"""
        endpoint = self._request.endpoint

        if not isinstance(parsed, dict):
            raise ResponseTypeError("dict", type(parsed).__name__, request_id=self._request.request_id)

        # Извлекаем элементы и метаданные
        items_key = endpoint.pagination_keys.get("items", "results")
        meta_key = endpoint.pagination_keys.get("meta", "meta")

        raw_items = parsed.get(items_key, [])
        raw_meta = parsed.get(meta_key, {})

        # Обновляем пагинатор если существует
        if self._request.paginator:
            self._request.paginator.update_from_response(raw_meta)

        # Парсим элементы
        if endpoint.response_schema is None:
            items = raw_items
        else:
            try:
                items = [endpoint.response_schema.model_validate(item) for item in raw_items]
            except ValidationError as exc:
                raise ResponseValidationError(
                    f"Paginated item validation failed: {exc}", request_id=self._request.request_id
                ) from exc

        # Парсим метаданные
        try:
            meta = PaginationMeta.model_validate(raw_meta)
        except ValidationError:
            meta = PaginationMeta()  # Fallback на пустые метаданные

        return PaginatedResponse(items=items, meta=meta, paginator=self._request.paginator)

    def get(self) -> tp.Union[T, tp.List[T], PaginatedResponse[T], tp.Any]:
        """Получить обработанные данные ответа (авто-определение типа)"""
        self._ensure_processed()
        return self._cached_data

    # Удобные аксессоры с правильной типизацией
    def as_object(self) -> T:
        """Получить как одиночный объект"""
        data = self.get()
        if self._request.endpoint.response_type != ResponseType.SINGLE_OBJECT:
            raise ResponseTypeError(
                "SINGLE_OBJECT", self._request.endpoint.response_type.value, request_id=self._request.request_id
            )
        return data  # type: ignore

    def as_list(self) -> tp.List[T]:
        """Получить как список"""
        data = self.get()
        if self._request.endpoint.response_type not in {ResponseType.PLAIN_LIST, ResponseType.PAGINATED_LIST}:
            raise ResponseTypeError(
                "LIST", self._request.endpoint.response_type.value, request_id=self._request.request_id
            )

        if isinstance(data, PaginatedResponse):
            return data.items
        return data  # type: ignore

    def as_paginated(self) -> PaginatedResponse[T]:
        """Получить как пагинированный результат"""
        data = self.get()
        if self._request.endpoint.response_type != ResponseType.PAGINATED_LIST:
            raise ResponseTypeError(
                "PAGINATED_LIST", self._request.endpoint.response_type.value, request_id=self._request.request_id
            )
        return data  # type: ignore

    def as_raw(self) -> tp.Any:
        """Получить сырые данные ответа"""
        return self.get()

    # Property аксессоры
    @property
    def status_code(self) -> int:
        return self._raw.status_code

    @property
    def headers(self) -> httpx.Headers:
        return self._raw.headers

    @property
    def raw(self) -> httpx.Response:
        return self._raw

    @property
    def success(self) -> bool:
        return 200 <= self.status_code < 300

    def raise_for_status(self) -> None:
        """Вызвать исключение для не-2xx ответов"""
        self._raw.raise_for_status()
