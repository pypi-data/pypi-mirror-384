import typing as tp
import uuid
from datetime import UTC, datetime

from .schemas import ApiError


class APIClientException(Exception):
    """Базовое исключение API клиента"""

    def __init__(
        self,
        message: str,
        status_code: tp.Optional[int] = None,
        code: tp.Optional[str] = None,
        details: tp.Optional[tp.Dict[str, tp.Any]] = None,
        request_id: tp.Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.now(UTC)
        self.error = ApiError(code=code or "api_error", message=message, details=details)
        super().__init__(self.message)

    def to_dict(self) -> tp.Dict[str, tp.Any]:
        return {
            "message": self.message,
            "status_code": self.status_code,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error.model_dump(),
        }


class RequestAPIException(APIClientException):
    """Базовое исключение запроса"""

    def __init__(self, message: str, status_code: tp.Optional[int] = None, request_id: tp.Optional[str] = None):
        super().__init__(message=message, status_code=status_code, code="request_error", request_id=request_id)


class ResponseAPIException(APIClientException):
    """Базовое исключение ответа"""

    def __init__(self, message: str, status_code: tp.Optional[int] = None, request_id: tp.Optional[str] = None):
        super().__init__(message=message, status_code=status_code, code="response_error", request_id=request_id)


# Исключения валидации
class RequestValidationError(APIClientException):
    """Ошибка валидации тела запроса"""

    def __init__(self, message: str, field: tp.Optional[str] = None, request_id: tp.Optional[str] = None):
        details = {"field": field} if field else None
        super().__init__(
            message=f"Request validation failed: {message}",
            code="request_validation_error",
            details=details,
            request_id=request_id,
        )


class ParamsValidationError(APIClientException):
    """Ошибка валидации параметров запроса"""

    def __init__(self, message: str, field: tp.Optional[str] = None, request_id: tp.Optional[str] = None):
        details = {"field": field} if field else None
        super().__init__(
            message=f"Params validation failed: {message}",
            code="params_validation_error",
            details=details,
            request_id=request_id,
        )


class ResponseValidationError(APIClientException):
    """Ошибка валидации тела ответа"""

    def __init__(self, message: str, field: tp.Optional[str] = None, request_id: tp.Optional[str] = None):
        details = {"field": field} if field else None
        super().__init__(
            message=f"Response validation failed: {message}",
            code="response_validation_error",
            details=details,
            request_id=request_id,
        )


class ResponseTypeError(APIClientException):
    """Ошибка валидации типа ответа"""

    def __init__(self, expected: str, actual: str, request_id: tp.Optional[str] = None):
        super().__init__(
            message=f"Expected response type {expected}, but got {actual}",
            code="response_type_error",
            details={"expected": expected, "actual": actual},
            request_id=request_id,
        )


class CircuitBreakerOpen(APIClientException):
    """Исключение при открытом circuit breaker"""

    def __init__(self, breaker_name: str, request_id: tp.Optional[str] = None):
        super().__init__(
            message=f"Circuit breaker '{breaker_name}' is open",
            code="circuit_breaker_open",
            details={"breaker_name": breaker_name},
            request_id=request_id,
        )
