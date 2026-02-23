# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/runner.py (line 336)
# License: MIT
# Complexity: 4
# Tier   : tier1

def from_call(
    cls,
    func: Callable[[], TResult],
    when: Literal["collect", "setup", "call", "teardown"],
    reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
) -> CallInfo[TResult]:
    """Call func, wrapping the result in a CallInfo.

    :param func:
        The function to call. Called without arguments.
    :type func: Callable[[], _pytest.runner.TResult]
    :param when:
        The phase in which the function is called.
    :param reraise:
        Exception or exceptions that shall propagate if raised by the
        function, instead of being wrapped in the CallInfo.
    """
    excinfo = None
    instant = timing.Instant()
    try:
        result: TResult | None = func()
    except BaseException:
        excinfo = ExceptionInfo.from_current()
        if reraise is not None and isinstance(excinfo.value, reraise):
            raise
        result = None
    duration = instant.elapsed()
    return cls(
        start=duration.start.time,
        stop=duration.stop.time,
        duration=duration.seconds,
        when=when,
        result=result,
        excinfo=excinfo,
        _ispytest=True,
    )