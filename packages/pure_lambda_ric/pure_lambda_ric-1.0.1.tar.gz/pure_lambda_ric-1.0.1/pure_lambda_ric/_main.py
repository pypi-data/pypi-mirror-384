import sys
from collections.abc import (
    Callable,
)
from logging import Logger
from typing import (
    NoReturn,
    TypeVar,
)

from fa_purity import (
    Cmd,
    Unsafe,
)

from pure_lambda_ric._api.core import (
    LambdaError,
)
from pure_lambda_ric._init import (
    HandlerMap,
    get_api_client,
    initialize,
)

from ._listener import (
    LambdaListener,
)

_T = TypeVar("_T")


def _init_error_exit(_: _T) -> NoReturn:
    sys.exit(1)


def _report_init_error(log: Logger, error: Exception) -> Cmd[None]:
    return (
        get_api_client(log)
        .map(lambda r: r.alt(Unsafe.raise_exception).to_union())
        .bind(
            lambda c: c.init_error(LambdaError.new(str(type(error)), str(error), ())).map(
                lambda r: r.alt(_init_error_exit).to_union(),
            ),
        )
    )


def start_lambda_listener(
    log: Logger,
    handler_map: Callable[[], HandlerMap],
) -> Cmd[None]:
    """Start lambda event listener."""
    return initialize(log, handler_map).bind(
        lambda r: r.map(lambda c: LambdaListener(log, c).event_loop())
        .alt(lambda e: _report_init_error(log, e).map(_init_error_exit).map(lambda _: None))
        .to_union(),
    )
