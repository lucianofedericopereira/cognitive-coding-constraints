# Source : https://github.com/Textualize/rich/blob/master/rich/console.py (line 1506)
# License: MIT
# Complexity: 12
# Tier   : tier3

def _collect_renderables(
    self,
    objects: Iterable[Any],
    sep: str,
    end: str,
    *,
    justify: Optional[JustifyMethod] = None,
    emoji: Optional[bool] = None,
    markup: Optional[bool] = None,
    highlight: Optional[bool] = None,
) -> List[ConsoleRenderable]:
    """Combine a number of renderables and text into one renderable.

    Args:
        objects (Iterable[Any]): Anything that Rich can render.
        sep (str): String to write between print data.
        end (str): String to write at end of print data.
        justify (str, optional): One of "left", "right", "center", or "full". Defaults to ``None``.
        emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default.
        markup (Optional[bool], optional): Enable markup, or ``None`` to use console default.
        highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default.

    Returns:
        List[ConsoleRenderable]: A list of things to render.
    """
    renderables: List[ConsoleRenderable] = []
    _append = renderables.append
    text: List[Text] = []
    append_text = text.append

    append = _append
    if justify in ("left", "center", "right"):

        def align_append(renderable: RenderableType) -> None:
            _append(Align(renderable, cast(AlignMethod, justify)))

        append = align_append

    _highlighter: HighlighterType = _null_highlighter
    if highlight or (highlight is None and self._highlight):
        _highlighter = self.highlighter

    def check_text() -> None:
        if text:
            sep_text = Text(sep, justify=justify, end=end)
            append(sep_text.join(text))
            text.clear()

    for renderable in objects:
        renderable = rich_cast(renderable)
        if isinstance(renderable, str):
            append_text(
                self.render_str(
                    renderable,
                    emoji=emoji,
                    markup=markup,
                    highlight=highlight,
                    highlighter=_highlighter,
                )
            )
        elif isinstance(renderable, Text):
            append_text(renderable)
        elif isinstance(renderable, ConsoleRenderable):
            check_text()
            append(renderable)
        elif is_expandable(renderable):
            check_text()
            append(Pretty(renderable, highlighter=_highlighter))
        else:
            append_text(_highlighter(str(renderable)))

    check_text()

    if self.style is not None:
        style = self.get_style(self.style)
        renderables = [Styled(renderable, style) for renderable in renderables]

    return renderables