from abc import ABC, abstractmethod
from typing import AsyncGenerator, Generator, List, Optional

from .exceptions import APIClientException
from .request import Request
from .response import Response


class IAPIClient(ABC):
    """Интерфейс базового API клиента"""

    @abstractmethod
    def execute(self, request: Request) -> Response:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class IAsyncAPIClient(ABC):
    """Интерфейс асинхронного API клиента"""

    @abstractmethod
    async def execute(self, request: Request) -> Response:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


class IPaginatable(ABC):
    """Интерфейс пагинации"""

    @abstractmethod
    def paginate(self, request: Request) -> Generator[Response, None, None]:
        pass


class IAsyncPaginatable(ABC):
    """Интерфейс асинхронной пагинации"""

    @abstractmethod
    async def paginate(self, request: Request) -> AsyncGenerator[Response, None]:
        pass


class IBulkOperations(ABC):
    """Интерфейс массовых операций"""

    @abstractmethod
    async def execute_bulk(self, requests: List[Request], max_concurrent: Optional[int] = None) -> List[Response]:
        pass


class IMiddleware(ABC):
    """Интерфейс middleware"""

    @abstractmethod
    async def on_request_async(self, request: Request) -> Request:
        pass

    @abstractmethod
    async def on_response_async(self, response: Response) -> Response:
        pass

    @abstractmethod
    async def on_error_async(self, error: APIClientException) -> None:
        pass

    @abstractmethod
    def on_request_sync(self, request: Request) -> Request:
        pass

    @abstractmethod
    def on_response_sync(self, response: Response) -> Response:
        pass

    @abstractmethod
    def on_error_sync(self, error: APIClientException) -> None:
        pass
