# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/python.py (line 757)
# License: MIT
# Complexity: 6
# Tier   : tier2

def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
    if not safe_getattr(self.obj, "__test__", True):
        return []
    if hasinit(self.obj):
        assert self.parent is not None
        self.warn(
            PytestCollectionWarning(
                f"cannot collect test class {self.obj.__name__!r} because it has a "
                f"__init__ constructor (from: {self.parent.nodeid})"
            )
        )
        return []
    elif hasnew(self.obj):
        assert self.parent is not None
        self.warn(
            PytestCollectionWarning(
                f"cannot collect test class {self.obj.__name__!r} because it has a "
                f"__new__ constructor (from: {self.parent.nodeid})"
            )
        )
        return []

    self._register_setup_class_fixture()
    self._register_setup_method_fixture()

    self.session._fixturemanager.parsefactories(self.newinstance(), self.nodeid)

    return super().collect()