from __future__ import (
    annotations,
)

import bisect
from dataclasses import (
    dataclass,
    field,
)
from fa_purity import (
    Cmd,
    CmdUnwrapper,
    Result,
    ResultE,
)
from fa_purity.date_time import (
    DatetimeFactory,
)
from fa_purity.lock import (
    ThreadLock,
)
from time import (
    sleep,
)
from typing import (
    List,
    TypeVar,
)

_T = TypeVar("_T")


@dataclass(frozen=True)
class _Private:
    pass


@dataclass(frozen=True)
class RateLimiter:
    _private: _Private = field(repr=False, hash=False, compare=False)
    _last_calls_times: List[int]
    _lock: ThreadLock
    max_calls: int
    period: int

    @staticmethod
    def new(
        max_calls: int,
        period: int,
        lock: ThreadLock,
    ) -> ResultE[RateLimiter]:
        if max_calls > 0 and period >= 0:
            obj = RateLimiter(
                _Private(),
                [],
                lock,
                max_calls,
                period,
            )
            return Result.success(obj)
        error = ValueError("max_calls > 0 and period >= 0 must be true")
        return Result.failure(Exception(error))

    def _insort(self, time: int) -> Cmd[None]:
        return Cmd.wrap_impure(lambda: bisect.insort(self._last_calls_times, time))

    def _last_calls_len(self) -> Cmd[int]:
        return Cmd.wrap_impure(lambda: len(self._last_calls_times))

    def _update_call(self, now: Cmd[int]) -> Cmd[None]:
        def _action(unwrap: CmdUnwrapper) -> None:
            while True:
                unwrap.act(self._lock.acquire)
                oldest = unwrap.act(Cmd.wrap_impure(lambda: self._last_calls_times[0]))
                _now = unwrap.act(now)
                wait_time = self.period - (_now - oldest)
                if wait_time > 0:
                    unwrap.act(self._lock.release)
                    sleep(wait_time)
                    continue
                delete = Cmd.wrap_impure(lambda: self._last_calls_times.pop(0))
                delete_and_insert = delete + self._insort(_now)
                unwrap.act(delete_and_insert + self._lock.release)
                return

        wait_loop = Cmd.new_cmd(_action)
        return self._lock.execute_with_lock(
            self._last_calls_len().bind(
                lambda n: now.bind(lambda t: self._insort(t).map(lambda _: True))
                if n < self.max_calls
                else Cmd.wrap_value(False)
            )
        ).bind(lambda b: Cmd.wrap_value(None) if b else wait_loop)

    def call_or_wait(self, wrapped_cmd: Cmd[_T]) -> Cmd[_T]:
        now = DatetimeFactory.date_now().map(lambda d: round(d.date_time.timestamp()))
        return self._update_call(now) + wrapped_cmd
