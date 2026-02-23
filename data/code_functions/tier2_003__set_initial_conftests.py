# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py (line 568)
# License: MIT
# Complexity: 6
# Tier   : tier2

def _set_initial_conftests(
    self,
    args: Sequence[str | pathlib.Path],
    pyargs: bool,
    noconftest: bool,
    rootpath: pathlib.Path,
    confcutdir: pathlib.Path | None,
    invocation_dir: pathlib.Path,
    importmode: ImportMode | str,
    *,
    consider_namespace_packages: bool,
) -> None:
    """Load initial conftest files given a preparsed "namespace".

    As conftest files may add their own command line options which have
    arguments ('--my-opt somepath') we might get some false positives.
    All builtin and 3rd party plugins will have been loaded, however, so
    common options will not confuse our logic here.
    """
    self._confcutdir = (
        absolutepath(invocation_dir / confcutdir) if confcutdir else None
    )
    self._noconftest = noconftest
    self._using_pyargs = pyargs
    foundanchor = False
    for initial_path in args:
        path = str(initial_path)
        # remove node-id syntax
        i = path.find("::")
        if i != -1:
            path = path[:i]
        anchor = absolutepath(invocation_dir / path)

        # Ensure we do not break if what appears to be an anchor
        # is in fact a very long option (#10169, #11394).
        if safe_exists(anchor):
            self._try_load_conftest(
                anchor,
                importmode,
                rootpath,
                consider_namespace_packages=consider_namespace_packages,
            )
            foundanchor = True
    if not foundanchor:
        self._try_load_conftest(
            invocation_dir,
            importmode,
            rootpath,
            consider_namespace_packages=consider_namespace_packages,
        )