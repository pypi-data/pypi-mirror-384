from __future__ import (
    annotations,
)

from collections.abc import (
    Callable,
)
from dataclasses import (
    dataclass,
    field,
)

from fa_purity import (
    Cmd,
    FrozenDict,
    FrozenList,
    Maybe,
    ResultE,
)
from fa_purity.json import (
    JsonObj,
    JsonPrimitive,
    JsonValue,
    JsonValueFactory,
)


@dataclass(frozen=True)
class _Private:
    pass


@dataclass(frozen=True)
class AwsRequestId:
    """The id of the lambda request."""

    raw: str


@dataclass(frozen=True)
class LambdaError:
    """Base type for creating a custom lambda error."""

    _private: _Private = field(repr=False, hash=False, compare=False)
    error_type: str
    details: JsonObj

    @staticmethod
    def new(error_type: str, msg: str, trace_back: FrozenList[str]) -> LambdaError:
        details = FrozenDict(
            {
                "errorMessage": JsonValue.from_primitive(JsonPrimitive.from_str(msg)),
                "errorType": JsonValue.from_primitive(JsonPrimitive.from_str(error_type)),
                "stackTrace": JsonValueFactory.from_list(trace_back),
            },
        )
        return LambdaError(_Private(), error_type, details)


@dataclass(frozen=True)
class Event:
    """The json data that was supplied to the lambda."""

    raw: JsonObj


@dataclass(frozen=True)
class PartialContext:
    """Lambda function partial context metadata."""

    function_name: str
    function_version: str
    memory_limit_in_mb: str
    log_group_name: Maybe[str]
    log_stream_name: Maybe[str]


@dataclass(frozen=True)
class Context:
    """Lambda function context."""

    this: PartialContext
    request_id: AwsRequestId


@dataclass(frozen=True)
class NextInvocation:
    request_id: AwsRequestId
    trace_id: str
    client_context: Maybe[str]
    cognito_identity: Maybe[str]
    deadline_ms: str
    invoked_function_arn: str
    event: Event


@dataclass(frozen=True)
class HandlerId:
    """The id of an specific lambda event handler."""

    raw: str


@dataclass(frozen=True)
class ApiEndpoint:
    raw: str

    def relative(self, path: str) -> ApiEndpoint:
        raw = "http://" + self.raw.rstrip("/") + "/2018-06-01/" + path.lstrip("/")
        return ApiEndpoint(raw)


@dataclass(frozen=True)
class ApiClient:
    get_next: Cmd[ResultE[NextInvocation]]
    send_response: Callable[[AwsRequestId, JsonObj], Cmd[ResultE[None]]]
    send_error: Callable[[AwsRequestId, LambdaError], Cmd[ResultE[None]]]
    init_error: Callable[[LambdaError], Cmd[ResultE[None]]]
