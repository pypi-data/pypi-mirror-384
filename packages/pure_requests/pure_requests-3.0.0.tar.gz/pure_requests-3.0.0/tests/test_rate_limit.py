from fa_purity import (
    Cmd,
    Unsafe,
)
from fa_purity.lock import (
    ThreadLock,
)
from pure_requests.rate_limit import (
    RateLimiter,
)
from time import (
    time,
)


def test_rate_limit() -> None:
    x = [0]

    def _action() -> None:
        x[0] = x[0] + 1

    increment = Cmd.wrap_impure(_action)
    _limited = ThreadLock.new().map(
        lambda lock: RateLimiter.new(1, 1, lock).alt(Unsafe.raise_exception).to_union()
    )
    limited = Unsafe.compute(_limited)
    start = time()
    Unsafe.compute(limited.call_or_wait(increment))  # immediate
    Unsafe.compute(limited.call_or_wait(increment))  # 1s later
    Unsafe.compute(limited.call_or_wait(increment))  # 2s later
    finish = time()
    assert finish - start >= 2
