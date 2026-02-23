# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/runner.py (line 231)
# License: MIT
# Complexity: 7
# Tier   : tier2

def call_and_report(
    item: Item, when: Literal["setup", "call", "teardown"], log: bool = True, **kwds
) -> TestReport:
    ihook = item.ihook
    if when == "setup":
        runtest_hook: Callable[..., None] = ihook.pytest_runtest_setup
    elif when == "call":
        runtest_hook = ihook.pytest_runtest_call
    elif when == "teardown":
        runtest_hook = ihook.pytest_runtest_teardown
    else:
        assert False, f"Unhandled runtest hook case: {when}"

    call = CallInfo.from_call(
        lambda: runtest_hook(item=item, **kwds),
        when=when,
        reraise=get_reraise_exceptions(item.config),
    )
    report: TestReport = ihook.pytest_runtest_makereport(item=item, call=call)
    if log:
        ihook.pytest_runtest_logreport(report=report)
    if check_interactive_exception(call, report):
        ihook.pytest_exception_interact(node=item, call=call, report=report)
    return report