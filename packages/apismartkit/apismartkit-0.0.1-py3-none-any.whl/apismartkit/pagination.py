import typing as tp
from abc import ABC, abstractmethod

from .enums import ResponseType
from .exceptions import ResponseTypeError


class PagePaginationStrategyInfo(tp.TypedDict):
    page_number: int
    page_size: int
    total_pages: int
    total_items: int


class LimitOffsetPaginationStrategyInfo(tp.TypedDict):
    limit: int
    offset: int
    total_items: int


class PaginationStrategy(ABC):
    """Абстрактный класс стратегии пагинации"""

    @abstractmethod
    def get_params(self) -> tp.Dict[str, tp.Any]:
        """Возвращает параметры для текущей страницы"""
        pass

    @abstractmethod
    def update_from_response(self, response_meta: tp.Dict[str, tp.Any]) -> None:
        """Обновляет состояние пагинации из метаданных ответа"""
        pass

    @abstractmethod
    def has_next_page(self) -> bool:
        """Проверяет, есть ли следующая страница"""
        pass

    @abstractmethod
    def next_page(self) -> None:
        """Переходит к следующей странице"""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Сбрасывает состояние пагинации"""
        pass

    @abstractmethod
    def get_page(self, page_info: tp.Union[int, tp.Dict[str, int]]) -> None:
        """Переходит к конкретной странице/позиции"""
        pass

    @property
    @abstractmethod
    def current_page_info(self) -> tp.Dict[str, tp.Any]:
        """Возвращает информацию о текущей странице"""
        pass


class PagePagination(PaginationStrategy):
    """
    Пагинация по страницам (page_number, page_size)
    """

    def __init__(
        self,
        page_size: int = 100,
        page_param: str = "page",
        page_size_param: str = "page_size",
        total_key: str = "total",
        pages_key: str = "pages",
    ):
        self.page_size = page_size
        self.page_param = page_param
        self.page_size_param = page_size_param
        self.total_key = total_key
        self.pages_key = pages_key

        self.current_page = 1
        self.total_pages: tp.Optional[int] = None
        self.total_items: tp.Optional[int] = None

    def get_params(self) -> tp.Dict[str, tp.Any]:
        return {self.page_param: self.current_page, self.page_size_param: self.page_size}

    def update_from_response(self, response_meta: tp.Dict[str, tp.Any]) -> None:
        self.total_items = response_meta[self.total_key]
        self.total_pages = response_meta[self.pages_key]

        # Если total_pages не предоставлен, вычисляем
        if self.total_items and not self.total_pages:
            self.total_pages = (self.total_items + self.page_size - 1) // self.page_size

    def has_next_page(self) -> bool:
        if self.total_pages is None:
            # Если неизвестно общее количество страниц, предполагаем что есть следующая
            return True
        return self.current_page < self.total_pages

    def next_page(self) -> None:
        if self.has_next_page():
            self.current_page += 1
        else:
            raise StopIteration("No more pages available")

    def reset(self) -> None:
        self.current_page = 1
        self.total_pages = None
        self.total_items = None

    def get_page(self, page_info: tp.Union[int, tp.Dict[str, int]]) -> None:
        if isinstance(page_info, int):
            self.current_page = page_info
        else:
            self.current_page = page_info.get("page_number", 1)
            if "page_size" in page_info:
                self.page_size = page_info["page_size"]

    @property
    def current_page_info(self) -> PagePaginationStrategyInfo:
        return {
            "page_number": self.current_page,
            "page_size": self.page_size,
            "total_pages": self.total_pages if self.total_pages else 0,
            "total_items": self.total_items if self.total_items else 0,
        }


class LimitOffsetPagination(PaginationStrategy):
    """
    Пагинация по лимиту и смещению (limit, offset)
    """

    def __init__(
        self, limit: int = 100, limit_param: str = "limit", offset_param: str = "offset", total_key: str = "total"
    ):
        self.limit = limit
        self.limit_param = limit_param
        self.offset_param = offset_param
        self.total_key = total_key

        self.current_offset = 0
        self.total_items: tp.Optional[int] = None

    def get_params(self) -> tp.Dict[str, tp.Any]:
        return {self.limit_param: self.limit, self.offset_param: self.current_offset}

    def update_from_response(self, response_meta: tp.Dict[str, tp.Any]) -> None:
        self.total_items = response_meta[self.total_key]

    def has_next_page(self) -> bool:
        if self.total_items is None:
            # Если неизвестно общее количество, предполагаем что есть следующая страница
            return True
        return self.current_offset + self.limit < self.total_items

    def next_page(self) -> None:
        if self.has_next_page():
            self.current_offset += self.limit
        else:
            raise StopIteration("No more pages available")

    def reset(self) -> None:
        self.current_offset = 0
        self.total_items = None

    def get_page(self, page_info: tp.Union[int, tp.Dict[str, int]]) -> None:
        if isinstance(page_info, int):
            # Интерпретируем как номер страницы
            self.current_offset = (page_info - 1) * self.limit
        else:
            self.current_offset = page_info.get("offset", 0)
            if "limit" in page_info:
                self.limit = page_info["limit"]

    @property
    def current_page_info(self) -> LimitOffsetPaginationStrategyInfo:
        return {
            "offset": self.current_offset,
            "limit": self.limit,
            "total_items": self.total_items if self.total_items else 0,
        }


class Paginator:
    """
    Основной класс пагинации для работы с PAGINATED_LIST
    """

    def __init__(self, strategy: tp.Union[PaginationStrategy, str] = "page", **strategy_kwargs):
        if isinstance(strategy, str):
            if strategy == "page":
                self.strategy = PagePagination(**strategy_kwargs)
            elif strategy == "limit_offset":
                self.strategy = LimitOffsetPagination(**strategy_kwargs)
            else:
                raise ValueError(f"Unknown pagination strategy: {strategy}")
        else:
            self.strategy = strategy

        self._request = None

    def bind_to_request(self, request: "Request") -> None:  # noqa: F821
        """Привязывает пагинатор к запросу"""
        self._request = request

        # Проверяем тип ответа
        if request.endpoint.response_type != ResponseType.PAGINATED_LIST:
            raise ResponseTypeError("PAGINATED_LIST", request.endpoint.response_type)

    def get_next_page(self) -> tp.Optional["Request"]:  # noqa: F821
        """Возвращает запрос для следующей страницы или None"""
        if not self._request:
            raise ValueError("Paginator not bound to request")

        if not self.strategy.has_next_page():
            return None

        # Создаем копию запроса с обновленными параметрами пагинации
        self.strategy.next_page()
        return self._create_paginated_request()

    def reset_pagination(self) -> None:
        """Сбрасывает состояние пагинации"""
        self.strategy.reset()
        if self._request:
            self._request._paginator = self

    def get_page(self, page_info: tp.Union[int, tp.Dict[str, int]]) -> "Request":  # noqa: F821
        """Возвращает запрос для конкретной страницы"""
        if not self._request:
            raise ValueError("Paginator not bound to request")

        self.strategy.get_page(page_info)
        return self._create_paginated_request()

    def update_from_response(self, response_meta: tp.Dict[str, tp.Any]) -> None:
        """Обновляет состояние пагинации из ответа"""
        self.strategy.update_from_response(response_meta)

    def _create_paginated_request(self) -> "Request":  # noqa: F821
        """Создает запрос с текущими параметрами пагинации"""
        from .request import Request

        # Создаем новый запрос с обновленными параметрами
        pagination_params = self.strategy.get_params()

        # Объединяем с существующими параметрами
        current_params = self._request.params.copy()
        if isinstance(current_params, dict):
            updated_params = {**current_params, **pagination_params}
        else:
            updated_params = pagination_params

        return Request(
            endpoint=self._request.endpoint,
            path_vars=self._request.path_vars,
            params=updated_params,
            headers=self._request.headers,
            data=self._request.data,
            timeout=self._request.timeout,
            paginator=self,  # Привязываем тот же пагинатор
        )

    @property
    def has_more(self) -> bool:
        """Проверяет, есть ли еще страницы"""
        return self.strategy.has_next_page()

    @property
    def current_page_info(self):
        """Возвращает информацию о текущей странице"""
        return self.strategy.current_page_info
