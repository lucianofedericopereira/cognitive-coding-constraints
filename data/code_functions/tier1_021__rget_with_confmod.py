# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py (line 695)
# License: MIT
# Complexity: 3
# Tier   : tier1

def _rget_with_confmod(
    self,
    name: str,
    path: pathlib.Path,
) -> tuple[types.ModuleType, Any]:
    modules = self._getconftestmodules(path)
    for mod in reversed(modules):
        try:
            return mod, getattr(mod, name)
        except AttributeError:
            continue
    raise KeyError(name)