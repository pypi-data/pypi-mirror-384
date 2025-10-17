from enum import Enum
from typing import TypeVar

T = TypeVar("T")


class ResponseType(Enum):
    SINGLE_OBJECT = "single"
    PAGINATED_LIST = "paginated"
    PLAIN_LIST = "plain_list"
    RAW = "raw"
    STREAM = "stream"


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
