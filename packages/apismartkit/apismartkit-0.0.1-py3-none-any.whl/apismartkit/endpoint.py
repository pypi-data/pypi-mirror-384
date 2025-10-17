import typing as tp
from http import HTTPMethod

from pydantic import BaseModel

from .enums import ResponseType
from .exceptions import ParamsValidationError, RequestValidationError, ResponseValidationError


class Endpoint:
    """
    API endpoint definition with validation schemas
    """

    def __init__(
        self,
        method: HTTPMethod,
        path: str,
        *,
        request_schema: tp.Optional[tp.Type[BaseModel]] = None,
        params_schema: tp.Optional[tp.Type[BaseModel]] = None,
        response_schema: tp.Optional[tp.Type[BaseModel]] = None,
        default_headers: tp.Optional[tp.Dict[str, str]] = None,
        default_params: tp.Optional[tp.Dict[str, tp.Any]] = None,
        response_type: ResponseType = ResponseType.SINGLE_OBJECT,
        pagination_keys: tp.Optional[tp.Dict[str, str]] = None,
        timeout: tp.Optional[float] = None,
        cache_ttl: tp.Optional[int] = None,
    ):
        self._method = method
        self._path = path
        self._request_schema = request_schema
        self._params_schema = params_schema
        self._response_schema = response_schema
        self._response_type = response_type
        self._default_headers = default_headers or {}
        self._default_params = default_params or {}
        self._pagination_keys = pagination_keys or {"items": "results", "meta": "meta"}
        self._timeout = timeout
        self._cache_ttl = cache_ttl

    @property
    def method(self) -> HTTPMethod:
        return self._method

    @property
    def path(self) -> str:
        return self._path

    @property
    def request_schema(self) -> tp.Optional[tp.Type[BaseModel]]:
        return self._request_schema

    @property
    def params_schema(self) -> tp.Optional[tp.Type[BaseModel]]:
        return self._params_schema

    @property
    def response_schema(self) -> tp.Optional[tp.Type[BaseModel]]:
        return self._response_schema

    @property
    def response_type(self) -> ResponseType:
        return self._response_type

    @property
    def default_headers(self) -> tp.Dict[str, str]:
        return self._default_headers

    @property
    def default_params(self) -> tp.Dict[str, tp.Any]:
        return self._default_params

    @property
    def pagination_keys(self) -> tp.Dict[str, str]:
        return self._pagination_keys

    @property
    def timeout(self) -> tp.Optional[float]:
        return self._timeout

    @property
    def cache_ttl(self) -> tp.Optional[int]:
        return self._cache_ttl

    def format_path(self, **path_vars: tp.Any) -> str:
        """Format path with variables"""
        try:
            return self._path.format(**path_vars)
        except KeyError as exc:
            raise ValueError(f"Missing path variable: {exc}") from exc

    def validate_request(self, data: tp.Any) -> BaseModel:
        """Валидирует данные запроса"""
        if self._request_schema is None:
            return data

        try:
            if isinstance(data, BaseModel):
                return data
            elif isinstance(data, dict):
                return self._request_schema(**data)
            else:
                return self._request_schema.model_validate(data)
        except Exception as exc:
            raise RequestValidationError(f"Request validation failed: {exc}")

    def validate_params(self, params: tp.Any) -> tp.Dict[str, tp.Any]:
        """Валидирует параметры запроса"""
        if self._params_schema is None:
            return params if isinstance(params, dict) else {}

        try:
            if isinstance(params, BaseModel):
                validated = params
            elif isinstance(params, dict):
                validated = self._params_schema(**params)
            else:
                validated = self._params_schema.model_validate(params)

            return validated.model_dump(mode="json", exclude_none=True)
        except Exception as exc:
            raise ParamsValidationError(f"Params validation failed: {exc}")

    def validate_response(self, data: tp.Any) -> tp.Any:
        """Валидирует данные ответа"""
        if self._response_schema is None:
            return data

        try:
            if isinstance(data, BaseModel):
                return data
            elif isinstance(data, dict):
                return self._response_schema(**data)
            else:
                return self._response_schema.model_validate(data)
        except Exception as exc:
            raise ResponseValidationError(f"Response validation failed: {exc}")
