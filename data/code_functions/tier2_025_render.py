# Source : https://github.com/Textualize/rich/blob/master/rich/console.py (line 1300)
# License: MIT
# Complexity: 9
# Tier   : tier2

def render(
    self, renderable: RenderableType, options: Optional[ConsoleOptions] = None
) -> Iterable[Segment]:
    """Render an object in to an iterable of `Segment` instances.

    This method contains the logic for rendering objects with the console protocol.
    You are unlikely to need to use it directly, unless you are extending the library.

    Args:
        renderable (RenderableType): An object supporting the console protocol, or
            an object that may be converted to a string.
        options (ConsoleOptions, optional): An options object, or None to use self.options. Defaults to None.

    Returns:
        Iterable[Segment]: An iterable of segments that may be rendered.
    """

    _options = options or self.options
    if _options.max_width < 1:
        # No space to render anything. This prevents potential recursion errors.
        return
    render_iterable: RenderResult

    renderable = rich_cast(renderable)
    if hasattr(renderable, "__rich_console__") and not isclass(renderable):
        render_iterable = renderable.__rich_console__(self, _options)
    elif isinstance(renderable, str):
        text_renderable = self.render_str(
            renderable, highlight=_options.highlight, markup=_options.markup
        )
        render_iterable = text_renderable.__rich_console__(self, _options)
    else:
        raise errors.NotRenderableError(
            f"Unable to render {renderable!r}; "
            "A str, Segment or object with __rich_console__ method is required"
        )

    try:
        iter_render = iter(render_iterable)
    except TypeError:
        raise errors.NotRenderableError(
            f"object {render_iterable!r} is not renderable"
        )
    _Segment = Segment
    _options = _options.reset_height()
    for render_output in iter_render:
        if isinstance(render_output, _Segment):
            yield render_output
        else:
            yield from self.render(render_output, _options)