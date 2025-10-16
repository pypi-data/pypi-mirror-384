from collections.abc import Callable
from dataclasses import (
    dataclass,
)
from logging import Logger
from os import (
    environ,
)

from fa_purity import (
    Cmd,
    CmdUnwrapper,
    FrozenDict,
    Maybe,
    Result,
    ResultE,
    ResultTransform,
    cast_exception,
)
from fa_purity.json import (
    JsonObj,
)

from pure_lambda_ric._api import (
    new_client,
)
from pure_lambda_ric._api.core import (
    ApiClient,
    ApiEndpoint,
    Context,
    Event,
    HandlerId,
    LambdaError,
    PartialContext,
)

HandlerFunction = Callable[[Event, Context], Cmd[Result[JsonObj, LambdaError]]]
HandlerMap = FrozenDict[HandlerId, HandlerFunction]


def _get_handler_map(handler_map: Callable[[], HandlerMap]) -> ResultE[HandlerMap]:
    try:
        return Result.success(handler_map())
    except Exception as error:  # noqa: BLE001
        # its ok because error is returned
        # Lambda runtime needs to catch any exception
        # for reporting it to the aws lambda service.
        return Result.failure(error)


def _require_env_var(key: str) -> Cmd[ResultE[str]]:
    return Cmd.wrap_impure(
        lambda: Maybe.from_optional(environ.get(key))
        .to_result()
        .alt(lambda _: KeyError(key))
        .alt(cast_exception),
    )


def _get_env_var(key: str) -> Cmd[Maybe[str]]:
    return Cmd.wrap_impure(lambda: Maybe.from_optional(environ.get(key)))


def _get_context() -> Cmd[ResultE[PartialContext]]:
    def _action(unwrapper: CmdUnwrapper) -> ResultE[PartialContext]:
        name = unwrapper.act(_require_env_var("AWS_LAMBDA_FUNCTION_NAME"))
        version = unwrapper.act(_require_env_var("AWS_LAMBDA_FUNCTION_VERSION"))
        memory = unwrapper.act(_require_env_var("AWS_LAMBDA_FUNCTION_MEMORY_SIZE"))
        log_group = unwrapper.act(_get_env_var("AWS_LAMBDA_LOG_GROUP_NAME"))
        log_stream = unwrapper.act(_get_env_var("AWS_LAMBDA_LOG_STREAM_NAME"))
        return name.bind(
            lambda n: version.bind(
                lambda v: memory.map(lambda m: PartialContext(n, v, m, log_group, log_stream)),
            ),
        )

    return Cmd.new_cmd(_action)


def _get_endpoint(log: Logger) -> Cmd[ResultE[ApiEndpoint]]:
    def _print(item: str) -> str:
        log.info("ApiEndpoint = %s", item)
        return item

    return _require_env_var("AWS_LAMBDA_RUNTIME_API").map(lambda r: r.map(_print).map(ApiEndpoint))


def _get_handler() -> Cmd[ResultE[HandlerId]]:
    return _require_env_var("HANDLER_ID").map(lambda r: r.map(HandlerId))


@dataclass(frozen=True)
class InitContext:
    client: ApiClient
    partial_context: PartialContext
    handler: HandlerFunction


def get_api_client(log: Logger) -> Cmd[ResultE[ApiClient]]:
    return _get_endpoint(log).map(lambda e: e.map(lambda a: new_client(log, a)))


def initialize(log: Logger, _map: Callable[[], HandlerMap]) -> Cmd[ResultE[InitContext]]:
    def _action(unwrapper: CmdUnwrapper) -> ResultE[InitContext]:
        log.info("Initializing...")
        _client = unwrapper.act(get_api_client(log))
        _partial_context = unwrapper.act(_get_context())
        log.info("partial context = %s", _partial_context)
        _handler = unwrapper.act(_get_handler())
        log.info("Handler id = %s", _handler)
        _handler_function = _get_handler_map(_map).bind(
            lambda _map: _handler.bind(lambda h: ResultTransform.get_key(_map, h)),
        )
        return _client.bind(
            lambda client: _partial_context.bind(
                lambda context: _handler_function.map(lambda fx: InitContext(client, context, fx)),
            ),
        )

    return Cmd.new_cmd(_action)
