from __future__ import (
    annotations,
)

from ._bug import (
    LibraryBug,
)
from dataclasses import (
    dataclass,
)
from fa_purity import (
    Cmd,
    PureIterFactory,
    Result,
    StreamFactory,
    Unsafe,
)
from fa_purity._core.coproduct import (
    Coproduct,
    UnionFactory,
)
import logging
from time import (
    sleep,
)
from typing import (
    Callable,
    Generic,
    TypeVar,
    Union,
)

LOG = logging.getLogger(__name__)
_S = TypeVar("_S")
_F = TypeVar("_F")
_U = TypeVar("_U")


class MaxRetriesReached(Exception):
    pass


@dataclass(frozen=True)
class HandledError(Generic[_F, _U]):
    """
    Error classifier between handled and unhandled
    Handled: left type
    Unhandled: right type
    """

    value: Coproduct[_F, _U]

    @staticmethod
    def handled(item: _F) -> HandledError[_F, _U]:
        return HandledError(Coproduct.inl(item))

    @staticmethod
    def unhandled(item: _U) -> HandledError[_F, _U]:
        return HandledError(Coproduct.inr(item))


@dataclass(frozen=True)
class HandledErrorFactory(Generic[_F, _U]):
    def handled(self, item: _F) -> HandledError[_F, _U]:
        return HandledError(Coproduct.inl(item))

    def unhandled(self, item: _U) -> HandledError[_F, _U]:
        return HandledError(Coproduct.inr(item))


def retry_cmd(
    cmd: Cmd[Result[_S, HandledError[_F, _U]]],
    next_cmd: Callable[
        [int, Result[_S, HandledError[_F, _U]]],
        Cmd[Result[_S, HandledError[_F, _U]]],
    ],
    max_retries: int,
) -> Cmd[Result[_S, Union[_U, MaxRetriesReached]]]:
    """
    Retry the suplied cmd until some successful value is returned
    or when an unhandled error is triggered.
    - `cmd` = the command that will be retried
    - `next_cmd` = what to do after the execution of each cmd. Two arguments are supplied:
        - first = # of the retry
        - second = the `Result` object that the cmd have returned
        e.g. common `next_cmd` arguments are sleeps that enable a time gap between retries
    - `max_retries` = limit on the # of retries
    """
    commands = PureIterFactory.from_range(range(0, max_retries + 1)).map(
        lambda i: cmd.bind(
            lambda r: next_cmd(i + 1, r) if i + 1 <= max_retries else Cmd.wrap_value(r)
        )
    )
    factory: UnionFactory[_U, MaxRetriesReached] = UnionFactory()
    return (
        StreamFactory.from_commands(commands)
        .find_first(
            lambda x: x.map(lambda _: True)
            .alt(lambda h: h.value.map(lambda _: False, lambda _: True))
            .to_union()
        )
        .map(
            lambda m: m.map(
                lambda r: r.alt(
                    lambda h: h.value.map(
                        lambda _: Unsafe.raise_exception(
                            LibraryBug(Exception("impossible"))
                        ),
                        lambda x: x,
                    )
                )
            )
            .to_result()
            .alt(lambda _: MaxRetriesReached(max_retries))
        )
        .map(lambda r: r.alt(factory.inr).bind(lambda r2: r2.alt(factory.inl)))
    )


def cmd_if_fail(
    result: Result[_S, _F],
    cmd: Cmd[None],
) -> Cmd[Result[_S, _F]]:
    "Execute a `cmd` if a `result` is a failure"

    def _cmd(err: _F) -> Cmd[Result[_S, _F]]:
        fail: Result[_S, _F] = Result.failure(err)
        return cmd.map(lambda _: fail)

    return result.map(lambda _: Cmd.wrap_value(result)).alt(_cmd).to_union()


def sleep_cmd(delay: float) -> Cmd[None]:
    "sleep command"
    return Cmd.wrap_impure(lambda: sleep(delay))
