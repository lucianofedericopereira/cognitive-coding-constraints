# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/assertion/rewrite.py (line 102)
# License: MIT
# Complexity: 12
# Tier   : tier3

def find_spec(
    self,
    name: str,
    path: Sequence[str | bytes] | None = None,
    target: types.ModuleType | None = None,
) -> importlib.machinery.ModuleSpec | None:
    if self._writing_pyc:
        return None
    state = self.config.stash[assertstate_key]
    if self._early_rewrite_bailout(name, state):
        return None
    state.trace(f"find_module called for: {name}")

    # Type ignored because mypy is confused about the `self` binding here.
    spec = self._find_spec(name, path)  # type: ignore

    if spec is None and path is not None:
        # With --import-mode=importlib, PathFinder cannot find spec without modifying `sys.path`,
        # causing inability to assert rewriting (#12659).
        # At this point, try using the file path to find the module spec.
        for _path_str in path:
            spec = importlib.util.spec_from_file_location(name, _path_str)
            if spec is not None:
                break

    if (
        # the import machinery could not find a file to import
        spec is None
        # this is a namespace package (without `__init__.py`)
        # there's nothing to rewrite there
        or spec.origin is None
        # we can only rewrite source files
        or not isinstance(spec.loader, importlib.machinery.SourceFileLoader)
        # if the file doesn't exist, we can't rewrite it
        or not os.path.exists(spec.origin)
    ):
        return None
    else:
        fn = spec.origin

    if not self._should_rewrite(name, fn, state):
        return None

    return importlib.util.spec_from_file_location(
        name,
        fn,
        loader=self,
        submodule_search_locations=spec.submodule_search_locations,
    )