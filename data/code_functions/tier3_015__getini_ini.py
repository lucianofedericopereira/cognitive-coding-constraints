# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py (line 1719)
# License: MIT
# Complexity: 17
# Tier   : tier3

def _getini_ini(
    self,
    name: str,
    canonical_name: str,
    type: str,
    value: str | list[str],
    default: Any,
):
    """Handle config values read in INI mode.

    In INI mode, values are stored as str or list[str] only, and coerced
    from string based on the registered type.
    """
    # Note: some coercions are only required if we are reading from .ini
    # files, because the file format doesn't contain type information, but
    # when reading from toml (in ini mode) we will get either str or list of
    # str values (see load_config_dict_from_file). For example:
    #
    #   ini:
    #     a_line_list = "tests acceptance"
    #
    # in this case, we need to split the string to obtain a list of strings.
    #
    #   toml (ini mode):
    #     a_line_list = ["tests", "acceptance"]
    #
    # in this case, we already have a list ready to use.
    if type == "paths":
        dp = (
            self.inipath.parent
            if self.inipath is not None
            else self.invocation_params.dir
        )
        input_values = shlex.split(value) if isinstance(value, str) else value
        return [dp / x for x in input_values]
    elif type == "args":
        return shlex.split(value) if isinstance(value, str) else value
    elif type == "linelist":
        if isinstance(value, str):
            return [t for t in map(lambda x: x.strip(), value.split("\n")) if t]
        else:
            return value
    elif type == "bool":
        return _strtobool(str(value).strip())
    elif type == "string":
        return value
    elif type == "int":
        if not isinstance(value, str):
            raise TypeError(
                f"Expected an int string for option {name} of type integer, but got: {value!r}"
            ) from None
        return int(value)
    elif type == "float":
        if not isinstance(value, str):
            raise TypeError(
                f"Expected a float string for option {name} of type float, but got: {value!r}"
            ) from None
        return float(value)
    else:
        return self._getini_unknown_type(name, type, value)