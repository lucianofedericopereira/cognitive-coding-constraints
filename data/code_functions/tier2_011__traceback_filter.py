# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/python.py (line 1690)
# License: MIT
# Complexity: 9
# Tier   : tier2

def _traceback_filter(self, excinfo: ExceptionInfo[BaseException]) -> Traceback:
    if hasattr(self, "_obj") and not self.config.getoption("fulltrace", False):
        code = _pytest._code.Code.from_function(get_real_func(self.obj))
        path, firstlineno = code.path, code.firstlineno
        traceback = excinfo.traceback
        ntraceback = traceback.cut(path=path, firstlineno=firstlineno)
        if ntraceback == traceback:
            ntraceback = ntraceback.cut(path=path)
            if ntraceback == traceback:
                ntraceback = ntraceback.filter(filter_traceback)
                if not ntraceback:
                    ntraceback = traceback
        ntraceback = ntraceback.filter(excinfo)

        # issue364: mark all but first and last frames to
        # only show a single-line message for each frame.
        if self.config.getoption("tbstyle", "auto") == "auto":
            if len(ntraceback) > 2:
                ntraceback = Traceback(
                    (
                        ntraceback[0],
                        *(t.with_repr_style("short") for t in ntraceback[1:-1]),
                        ntraceback[-1],
                    )
                )

        return ntraceback
    return excinfo.traceback