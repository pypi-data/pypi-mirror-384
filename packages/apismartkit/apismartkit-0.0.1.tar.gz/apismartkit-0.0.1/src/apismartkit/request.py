import json
import typing as tp
import uuid

import pydantic as pd
from pydantic import BaseModel

from .endpoint import Endpoint
from .enums import ResponseType
from .exceptions import ParamsValidationError, RequestValidationError
from .pagination import Paginator


class Request:
    def __init__(
        self,
        endpoint: Endpoint,
        *,
        path_vars: tp.Optional[tp.Dict[str, tp.Any]] = None,
        params: tp.Optional[tp.Union[tp.Dict[str, tp.Any], BaseModel]] = None,
        headers: tp.Optional[tp.Dict[str, str]] = None,
        data: tp.Optional[tp.Any] = None,
        timeout: tp.Optional[float] = None,
        paginator: tp.Optional[Paginator] = None,
        json_mode: bool = True,
    ):
        self._endpoint = endpoint
        self._path_vars = path_vars or {}
        self._params = params or {}
        self._headers = headers or {}
        self._data = data
        self._timeout = timeout or endpoint.timeout
        self._paginator = paginator
        self._json_mode = json_mode
        self._request_id = str(uuid.uuid4())
        self._metrics: tp.Dict[str, tp.Any] = {}

        self._validated = False
        self._validated_params: tp.Optional[tp.Dict[str, tp.Any]] = None
        self._validated_data: tp.Optional[tp.Dict[str, tp.Any]] = None

        # Привязываем пагинатор к запросу
        if self._paginator and self._endpoint.response_type == ResponseType.PAGINATED_LIST:
            self._paginator.bind_to_request(self)

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def params(self):
        return self._params

    @property
    def path_vars(self):
        return self._path_vars

    @property
    def headers(self):
        return self._headers

    @property
    def data(self):
        return self._data

    @property
    def request_id(self):
        return self._request_id

    @property
    def paginator(self):
        return self._paginator

    @property
    def timeout(self):
        return self._timeout

    @property
    def metrics(self):
        return self._metrics

    def validate(self) -> None:
        """Валидация данных запроса против схем endpoint'а"""
        # Валидация параметров
        if self.endpoint.params_schema is not None:
            try:
                if isinstance(self._params, dict):
                    params_model = self.endpoint.params_schema(**self._params)
                elif isinstance(self._params, BaseModel):
                    params_model = self._params
                else:
                    params_model = self.endpoint.params_schema.model_validate(self._params)

                self._validated_params = params_model.model_dump(mode="json", exclude_none=True)
            except pd.ValidationError as exc:
                raise ParamsValidationError(f"Params validation failed: {exc}", request_id=self.request_id) from exc

        # Валидация тела запроса
        if self.endpoint.request_schema is not None and self.data is not None:
            try:
                if isinstance(self.data, dict):
                    data_model = self.endpoint.request_schema(**self.data)
                elif isinstance(self.data, BaseModel):
                    data_model = self.data
                else:
                    data_model = self.endpoint.request_schema.model_validate(self.data)

                self._validated_data = data_model.model_dump(mode="json", exclude_none=True)
            except pd.ValidationError as exc:
                raise RequestValidationError(
                    f"Request body validation failed: {exc}", request_id=self.request_id
                ) from exc

        self._validated = True

    def build_request(self) -> tp.Tuple[str, str, tp.Dict[str, tp.Any], tp.Any, tp.Dict[str, str]]:
        """Сборка параметров HTTP запроса"""
        if not self._validated:
            self.validate()

        # Используем валидированные данные или оригинальные
        params = self._validated_params if self._validated_params is not None else self._params
        data = self._validated_data if self._validated_data is not None else self.data

        # Добавляем параметры пагинации если нужно
        if self._paginator and self.endpoint.response_type == ResponseType.PAGINATED_LIST:
            pagination_params = self._paginator.strategy.get_params()
            if isinstance(params, dict):
                params = {**params, **pagination_params}
            else:
                # Если params это модель, нам нужно обработать это иначе
                # Пока предполагаем dict для пагинации
                params = pagination_params

        # Подготавливаем финальные параметры
        final_params = {**self.endpoint.default_params, **params} if isinstance(params, dict) else params
        final_headers = {**self.endpoint.default_headers, **self.headers}

        if self._json_mode and "Content-Type" not in final_headers:
            final_headers["Content-Type"] = "application/json"

        # Сериализуем данные для JSON
        final_data = data
        if self._json_mode and data is not None:
            if isinstance(data, (dict, list)):
                final_data = json.dumps(data, default=str)
            elif isinstance(data, BaseModel):
                final_data = data.model_dump_json()

        path = self.endpoint.format_path(**self._path_vars)

        return (
            self._endpoint.method.value,
            path,
            final_params,
            final_data,
            final_headers,
        )

    def with_pagination(self, strategy: tp.Union[str, Paginator] = "page", **strategy_kwargs) -> "Request":
        """Создает новый запрос с пагинацией"""
        if self.endpoint.response_type != ResponseType.PAGINATED_LIST:
            raise ValueError("Pagination only available for PAGINATED_LIST endpoints")

        if isinstance(strategy, str):
            paginator = Paginator(strategy=strategy, **strategy_kwargs)
        else:
            paginator = strategy

        return Request(
            endpoint=self._endpoint,
            path_vars=self._path_vars,
            params=self._params,
            headers=self._headers,
            data=self._data,
            timeout=self._timeout,
            paginator=paginator,
            json_mode=self._json_mode,
        )


class RequestBuilder:
    """Fluid interface для создания запросов"""

    def __init__(self, endpoint: Endpoint):
        self._endpoint = endpoint
        self._path_vars: tp.Dict[str, tp.Any] = {}
        self._params: tp.Dict[str, tp.Any] = {}
        self._headers: tp.Dict[str, str] = {}
        self._data: tp.Optional[tp.Any] = None
        self._timeout: tp.Optional[float] = None
        self._paginator: tp.Optional[Paginator] = None

    def with_path_vars(self, **path_vars: tp.Any) -> "RequestBuilder":
        self._path_vars = path_vars
        return self

    def with_params(self, params: tp.Dict[str, tp.Any]) -> "RequestBuilder":
        self._params = params
        return self

    def with_headers(self, headers: tp.Dict[str, tp.Any]) -> "RequestBuilder":
        self._headers = headers
        return self

    def with_data(self, data: tp.Any) -> "RequestBuilder":
        self._data = data
        return self

    def with_timeout(self, timeout: float) -> "RequestBuilder":
        self._timeout = timeout
        return self

    def with_pagination(self, strategy: tp.Union[str, Paginator] = "page", **strategy_kwargs) -> "RequestBuilder":
        if self._endpoint.response_type == ResponseType.PAGINATED_LIST:
            if isinstance(strategy, str):
                self._paginator = Paginator(strategy=strategy, **strategy_kwargs)
            else:
                self._paginator = strategy
        return self

    def build(self) -> Request:
        return Request(
            endpoint=self._endpoint,
            path_vars=self._path_vars,
            params=self._params,
            headers=self._headers,
            data=self._data,
            timeout=self._timeout,
            paginator=self._paginator,
        )
