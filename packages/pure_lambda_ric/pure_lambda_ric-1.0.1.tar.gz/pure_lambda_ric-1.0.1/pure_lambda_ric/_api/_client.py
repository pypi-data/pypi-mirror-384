from __future__ import (
    annotations,
)

from dataclasses import (
    dataclass,
)
from logging import Logger
from typing import (
    TypeVar,
)

from fa_purity import (
    Cmd,
    FrozenDict,
    Maybe,
    Result,
    ResultE,
    ResultTransform,
    cast_exception,
)
from fa_purity.json import (
    JsonObj,
    JsonUnfolder,
    UnfoldedFactory,
)
from pure_requests.basic import (
    Authentication,
    Data,
    Endpoint,
    HttpClient,
    HttpClientFactory,
    Params,
)
from pure_requests.response import (
    handle_status,
    json_decode,
)
from requests import (
    RequestException,
    Response,
)

from .core import (
    ApiClient,
    ApiEndpoint,
    AwsRequestId,
    Event,
    LambdaError,
    NextInvocation,
)

_S = TypeVar("_S")
_F = TypeVar("_F")


def _get_optional(items: FrozenDict[_S, _F], key: _S) -> Maybe[_F]:
    return Maybe.from_result(ResultTransform.try_get(items, key).alt(lambda _: None))


def _decode_next(
    log: Logger,
    headers: FrozenDict[str, str],
    body: JsonObj,
) -> ResultE[NextInvocation]:
    log.info("_decode_next %s", headers)
    return (
        ResultTransform.try_get(headers, "Lambda-Runtime-Aws-Request-Id")
        .map(AwsRequestId)
        .bind(
            lambda req_id: ResultTransform.try_get(headers, "Lambda-Runtime-Trace-Id").bind(
                lambda trace: ResultTransform.try_get(headers, "Lambda-Runtime-Deadline-Ms").bind(
                    lambda dead_line: ResultTransform.try_get(
                        headers,
                        "Lambda-Runtime-Invoked-Function-Arn",
                    ).map(
                        lambda invoked: NextInvocation(
                            req_id,
                            trace,
                            _get_optional(headers, "Lambda-Runtime-Client-Context"),
                            _get_optional(headers, "Lambda-Runtime-Cognito-Identity"),
                            dead_line,
                            invoked,
                            Event(body),
                        ),
                    ),
                ),
            ),
        )
    )


@dataclass(frozen=True)
class HttpClientWithLogging:
    _log: Logger
    _client: HttpClient

    @staticmethod
    def new(
        log: Logger,
        auth: Authentication | None,
        headers: JsonObj | None,
        stream: bool | None,
    ) -> HttpClientWithLogging:
        client = HttpClientFactory.new_client(auth, headers, stream)
        return HttpClientWithLogging(log, client)

    def _log_api_call(
        self,
        endpoint: Endpoint,
        params: Params,
        data: Data | None,
        result: Result[_S, _F],
    ) -> Cmd[None]:
        return Cmd.wrap_impure(
            lambda: self._log.info(
                "[lambda API] endpoint=%s params=%s data=%s result=%s",
                endpoint,
                params,
                data,
                result,
            ),
        )

    def _get(self, endpoint: Endpoint, params: Params) -> Cmd[Result[Response, RequestException]]:
        result = self._client.get(endpoint, params)
        return result.bind(lambda r: self._log_api_call(endpoint, params, None, r).map(lambda _: r))

    def _post(
        self,
        endpoint: Endpoint,
        params: Params,
        data: Data,
    ) -> Cmd[Result[Response, RequestException]]:
        result = self._client.post(endpoint, params, data)
        return result.bind(lambda r: self._log_api_call(endpoint, params, data, r).map(lambda _: r))

    @property
    def client(self) -> HttpClient:
        return HttpClient(self._get, self._post)


@dataclass(frozen=True)
class _Client1:
    _log: Logger
    _endpoint: ApiEndpoint

    def _log_result(self, name: str, result: Cmd[Result[_S, _F]]) -> Cmd[Result[_S, _F]]:
        return result.bind(
            lambda r: Cmd.wrap_impure(
                lambda: self._log.info("[lambda client] `%s` response=%s", name, r),
            ).map(lambda _: r),
        )

    @staticmethod
    def _to_endpoint(api: ApiEndpoint) -> Endpoint:
        return Endpoint(api.raw)

    def get_next(self) -> Cmd[ResultE[NextInvocation]]:
        client = HttpClientWithLogging.new(self._log, None, None, None).client
        empty: JsonObj = FrozenDict({})
        result = client.get(
            self._to_endpoint(self._endpoint.relative("/runtime/invocation/next")),
            Params(empty),
        ).map(
            lambda r: r.alt(cast_exception).bind(
                lambda t: handle_status(t)
                .alt(cast_exception)
                .bind(
                    lambda s: json_decode(s)
                    .alt(cast_exception)
                    .bind(
                        lambda c: c.map(
                            lambda j: _decode_next(
                                self._log,
                                FrozenDict(dict(s.headers.items())),
                                j,
                            ),
                            lambda _: Result.failure(
                                TypeError("Expected non-list"),
                                NextInvocation,
                            ).alt(cast_exception),
                        ),
                    ),
                ),
            ),
        )
        return self._log_result("get_next", result)

    def init_error(self, error: LambdaError) -> Cmd[ResultE[None]]:
        empty: JsonObj = FrozenDict({})
        headers = UnfoldedFactory.from_dict(
            {"Lambda-Runtime-Function-Error-Type": error.error_type},
        )
        client = HttpClientWithLogging.new(self._log, None, headers, None).client
        result = client.post(
            self._to_endpoint(self._endpoint.relative("/runtime/init/error")),
            Params(empty),
            Data(JsonUnfolder.dumps(error.details)),
        ).map(
            lambda r: r.alt(cast_exception).bind(
                lambda t: handle_status(t).map(lambda _: None).alt(cast_exception),
            ),
        )
        return self._log_result("_init_error", result)

    def send_response(self, request_id: AwsRequestId, data: JsonObj) -> Cmd[ResultE[None]]:
        empty: JsonObj = FrozenDict({})
        client = HttpClientWithLogging.new(self._log, None, None, None).client
        result = client.post(
            self._to_endpoint(
                self._endpoint.relative("/runtime/invocation/" + request_id.raw + "/response"),
            ),
            Params(empty),
            Data(JsonUnfolder.dumps(data)),
        ).map(
            lambda r: r.alt(cast_exception).bind(
                lambda t: handle_status(t).map(lambda _: None).alt(cast_exception),
            ),
        )
        return self._log_result("send_response", result)

    def send_error(self, request_id: AwsRequestId, error: LambdaError) -> Cmd[ResultE[None]]:
        empty: JsonObj = FrozenDict({})
        headers = UnfoldedFactory.from_dict(
            {"Lambda-Runtime-Function-Error-Type": error.error_type},
        )
        client = HttpClientWithLogging.new(self._log, None, headers, None).client
        result = client.post(
            self._to_endpoint(
                self._endpoint.relative("/runtime/invocation/" + request_id.raw + "/error"),
            ),
            Params(empty),
            Data(JsonUnfolder.dumps(error.details)),
        ).map(
            lambda r: r.alt(cast_exception).bind(
                lambda t: handle_status(t).map(lambda _: None).alt(cast_exception),
            ),
        )
        return self._log_result("send_error", result)


def new_client(log: Logger, endpoint: ApiEndpoint) -> ApiClient:
    client = _Client1(log, endpoint)
    return ApiClient(
        client.get_next(),
        client.send_response,
        client.send_error,
        client.init_error,
    )
