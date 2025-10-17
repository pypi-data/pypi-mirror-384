import typing as tp
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict


class ApiError(BaseModel):
    """Standard API error model"""

    code: str
    message: tp.Optional[str] = None
    details: tp.Optional[tp.Dict[str, tp.Any]] = None
    timestamp: datetime = None

    model_config = ConfigDict(extra="forbid")

    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.now(UTC)
        super().__init__(**data)


class PaginationMeta(BaseModel):
    """Pagination metadata model"""

    total: tp.Optional[int] = None
    page: tp.Optional[int] = None
    page_size: tp.Optional[int] = None
    pages: tp.Optional[int] = None
    next: tp.Optional[str] = None
    previous: tp.Optional[str] = None

    model_config = ConfigDict(extra="allow")


class RequestMetrics(BaseModel):
    """Метрики запроса"""

    request_id: str
    duration: float
    method: str
    path: str
    status_code: tp.Optional[int] = None
    success: bool = True
    retry_count: int = 0

    model_config = ConfigDict(extra="forbid")
