# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py (line 905)
# License: MIT
# Complexity: 6
# Tier   : tier2

def _get_plugin_specs_as_list(
    specs: None | types.ModuleType | str | Sequence[str],
) -> list[str]:
    """Parse a plugins specification into a list of plugin names."""
    # None means empty.
    if specs is None:
        return []
    # Workaround for #3899 - a submodule which happens to be called "pytest_plugins".
    if isinstance(specs, types.ModuleType):
        return []
    # Comma-separated list.
    if isinstance(specs, str):
        return specs.split(",") if specs else []
    # Direct specification.
    if isinstance(specs, collections.abc.Sequence):
        return list(specs)
    raise UsageError(
        f"Plugins may be specified as a sequence or a ','-separated string of plugin names. Got: {specs!r}"
    )