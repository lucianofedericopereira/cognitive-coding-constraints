# Source : https://github.com/Textualize/rich/blob/master/rich/table.py (line 253)
# License: MIT
# Complexity: 1
# Tier   : tier1

def grid(
    cls,
    *headers: Union[Column, str],
    padding: PaddingDimensions = 0,
    collapse_padding: bool = True,
    pad_edge: bool = False,
    expand: bool = False,
) -> "Table":
    """Get a table with no lines, headers, or footer.

    Args:
        *headers (Union[Column, str]): Column headers, either as a string, or :class:`~rich.table.Column` instance.
        padding (PaddingDimensions, optional): Get padding around cells. Defaults to 0.
        collapse_padding (bool, optional): Enable collapsing of padding around cells. Defaults to True.
        pad_edge (bool, optional): Enable padding around edges of table. Defaults to False.
        expand (bool, optional): Expand the table to fit the available space if ``True``, otherwise the table width will be auto-calculated. Defaults to False.

    Returns:
        Table: A table instance.
    """
    return cls(
        *headers,
        box=None,
        padding=padding,
        collapse_padding=collapse_padding,
        show_header=False,
        show_footer=False,
        show_edge=False,
        pad_edge=pad_edge,
        expand=expand,
    )