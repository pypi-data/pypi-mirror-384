import sys
from dataclasses import (
    dataclass,
)
from logging import Logger
from typing import (
    NoReturn,
    TypeVar,
)

from fa_purity import (
    Cmd,
    CmdUnwrapper,
    PureIterFactory,
    PureIterTransform,
    Result,
    Unsafe,
)
from fa_purity.json import (
    JsonObj,
)

from pure_lambda_ric._api.core import (
    AwsRequestId,
    Context,
    LambdaError,
    NextInvocation,
)
from pure_lambda_ric._init import (
    InitContext,
)

_T = TypeVar("_T")


def _init_error_exit(_: _T) -> NoReturn:
    sys.exit(1)


@dataclass(frozen=True)
class LambdaListener:
    log: Logger
    context: InitContext

    def _send_result(
        self,
        request_id: AwsRequestId,
        result: Result[JsonObj, LambdaError],
    ) -> Cmd[None]:
        return (
            result.to_coproduct()
            .map(
                lambda j: self.context.client.send_response(request_id, j),
                lambda e: self.context.client.send_error(request_id, e),
            )
            .map(lambda r: r.alt(Unsafe.raise_exception).to_union())
        )

    def _call_wrapped_handler(self, _next: NextInvocation) -> Cmd[Result[JsonObj, LambdaError]]:
        def _action(unwrapper: CmdUnwrapper) -> Result[JsonObj, LambdaError]:
            try:
                _result = self.context.handler(
                    _next.event,
                    Context(self.context.partial_context, _next.request_id),
                )
                return unwrapper.act(_result)
            except Exception as e:  # noqa: BLE001
                # its ok because error is returned
                return Result.failure(
                    LambdaError.new(
                        "Unhandled error " + str(type(e)),
                        str(e),
                        (str(e.__traceback__),),
                    ),
                )

        return Cmd.new_cmd(_action)

    def _process_next(self, _next: NextInvocation) -> Cmd[None]:
        return self._call_wrapped_handler(_next).bind(
            lambda r: self._send_result(_next.request_id, r),
        )

    def _report_init_error(self, error: LambdaError) -> Cmd[None]:
        return (
            self.context.client.init_error(error)
            .map(lambda error: error.alt(Unsafe.raise_exception).to_union())
            .map(_init_error_exit)
            .map(lambda _: None)
        )

    def _get_and_process_next(self) -> Cmd[None]:
        return self.context.client.get_next.bind(
            lambda r: r.map(self._process_next)
            .alt(
                lambda e: LambdaError.new("Runtime.api_error", "get_next i.e. " + str(e), ()),
            )
            .alt(self._report_init_error)
            .to_union(),
        )

    def event_loop(self) -> Cmd[None]:
        msg = Cmd.wrap_impure(lambda: self.log.info("Starting event loop..."))
        cmds = PureIterFactory.infinite_range(0, 0).map(lambda _: self._get_and_process_next())
        return msg + PureIterTransform.consume(cmds)
