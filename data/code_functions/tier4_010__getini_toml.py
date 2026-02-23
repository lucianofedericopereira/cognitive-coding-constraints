# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py (line 1780)
# License: MIT
# Complexity: 21
# Tier   : tier4

def _getini_toml(
    self,
    name: str,
    canonical_name: str,
    type: str,
    value: object,
    default: Any,
):
    """Handle TOML config values with strict type validation and no coercion.

    In TOML mode, values already have native types from TOML parsing.
    We validate types match expectations exactly, including list items.
    """
    value_type = builtins.type(value).__name__
    if type == "paths":
        # Expect a list of strings.
        if not isinstance(value, list):
            raise TypeError(
                f"{self.inipath}: config option '{name}' expects a list for type 'paths', "
                f"got {value_type}: {value!r}"
            )
        for i, item in enumerate(value):
            if not isinstance(item, str):
                item_type = builtins.type(item).__name__
                raise TypeError(
                    f"{self.inipath}: config option '{name}' expects a list of strings, "
                    f"but item at index {i} is {item_type}: {item!r}"
                )
        dp = (
            self.inipath.parent
            if self.inipath is not None
            else self.invocation_params.dir
        )
        return [dp / x for x in value]
    elif type in {"args", "linelist"}:
        # Expect a list of strings.
        if not isinstance(value, list):
            raise TypeError(
                f"{self.inipath}: config option '{name}' expects a list for type '{type}', "
                f"got {value_type}: {value!r}"
            )
        for i, item in enumerate(value):
            if not isinstance(item, str):
                item_type = builtins.type(item).__name__
                raise TypeError(
                    f"{self.inipath}: config option '{name}' expects a list of strings, "
                    f"but item at index {i} is {item_type}: {item!r}"
                )
        return list(value)
    elif type == "bool":
        # Expect a boolean.
        if not isinstance(value, bool):
            raise TypeError(
                f"{self.inipath}: config option '{name}' expects a bool, "
                f"got {value_type}: {value!r}"
            )
        return value
    elif type == "int":
        # Expect an integer (but not bool, which is a subclass of int).
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(
                f"{self.inipath}: config option '{name}' expects an int, "
                f"got {value_type}: {value!r}"
            )
        return value
    elif type == "float":
        # Expect a float or integer only.
        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(
                f"{self.inipath}: config option '{name}' expects a float, "
                f"got {value_type}: {value!r}"
            )
        return value
    elif type == "string":
        # Expect a string.
        if not isinstance(value, str):
            raise TypeError(
                f"{self.inipath}: config option '{name}' expects a string, "
                f"got {value_type}: {value!r}"
            )
        return value
    else:
        return self._getini_unknown_type(name, type, value)