# Source : https://github.com/Textualize/rich/blob/master/rich/console.py (line 163)
# License: MIT
# Complexity: 12
# Tier   : tier3

def update(
    self,
    *,
    width: Union[int, NoChange] = NO_CHANGE,
    min_width: Union[int, NoChange] = NO_CHANGE,
    max_width: Union[int, NoChange] = NO_CHANGE,
    justify: Union[Optional[JustifyMethod], NoChange] = NO_CHANGE,
    overflow: Union[Optional[OverflowMethod], NoChange] = NO_CHANGE,
    no_wrap: Union[Optional[bool], NoChange] = NO_CHANGE,
    highlight: Union[Optional[bool], NoChange] = NO_CHANGE,
    markup: Union[Optional[bool], NoChange] = NO_CHANGE,
    height: Union[Optional[int], NoChange] = NO_CHANGE,
) -> "ConsoleOptions":
    """Update values, return a copy."""
    options = self.copy()
    if not isinstance(width, NoChange):
        options.min_width = options.max_width = max(0, width)
    if not isinstance(min_width, NoChange):
        options.min_width = min_width
    if not isinstance(max_width, NoChange):
        options.max_width = max_width
    if not isinstance(justify, NoChange):
        options.justify = justify
    if not isinstance(overflow, NoChange):
        options.overflow = overflow
    if not isinstance(no_wrap, NoChange):
        options.no_wrap = no_wrap
    if not isinstance(highlight, NoChange):
        options.highlight = highlight
    if not isinstance(markup, NoChange):
        options.markup = markup
    if not isinstance(height, NoChange):
        if height is not None:
            options.max_height = height
        options.height = None if height is None else max(0, height)
    return options