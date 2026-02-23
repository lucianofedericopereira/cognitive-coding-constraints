# Source : https://github.com/Textualize/rich/blob/master/rich/console.py (line 1011)
# License: MIT
# Complexity: 16
# Tier   : tier3

def size(self) -> ConsoleDimensions:
    """Get the size of the console.

    Returns:
        ConsoleDimensions: A named tuple containing the dimensions.
    """

    if self._width is not None and self._height is not None:
        return ConsoleDimensions(self._width - self.legacy_windows, self._height)

    if self.is_dumb_terminal:
        return ConsoleDimensions(80, 25)

    width: Optional[int] = None
    height: Optional[int] = None

    streams = _STD_STREAMS_OUTPUT if WINDOWS else _STD_STREAMS
    for file_descriptor in streams:
        try:
            width, height = os.get_terminal_size(file_descriptor)
        except (AttributeError, ValueError, OSError):  # Probably not a terminal
            pass
        else:
            break

    columns = self._environ.get("COLUMNS")
    if columns is not None and columns.isdigit():
        width = int(columns)
    lines = self._environ.get("LINES")
    if lines is not None and lines.isdigit():
        height = int(lines)

    # get_terminal_size can report 0, 0 if run from pseudo-terminal
    width = width or 80
    height = height or 25
    return ConsoleDimensions(
        width - self.legacy_windows if self._width is None else self._width,
        height if self._height is None else self._height,
    )