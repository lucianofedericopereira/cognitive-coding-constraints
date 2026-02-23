# Source : https://github.com/Textualize/rich/blob/master/rich/console.py (line 1351)
# License: MIT
# Complexity: 7
# Tier   : tier2

def render_lines(
    self,
    renderable: RenderableType,
    options: Optional[ConsoleOptions] = None,
    *,
    style: Optional[Style] = None,
    pad: bool = True,
    new_lines: bool = False,
) -> List[List[Segment]]:
    """Render objects in to a list of lines.

    The output of render_lines is useful when further formatting of rendered console text
    is required, such as the Panel class which draws a border around any renderable object.

    Args:
        renderable (RenderableType): Any object renderable in the console.
        options (Optional[ConsoleOptions], optional): Console options, or None to use self.options. Default to ``None``.
        style (Style, optional): Optional style to apply to renderables. Defaults to ``None``.
        pad (bool, optional): Pad lines shorter than render width. Defaults to ``True``.
        new_lines (bool, optional): Include "\n" characters at end of lines.

    Returns:
        List[List[Segment]]: A list of lines, where a line is a list of Segment objects.
    """
    with self._lock:
        render_options = options or self.options
        _rendered = self.render(renderable, render_options)
        if style:
            _rendered = Segment.apply_style(_rendered, style)

        render_height = render_options.height
        if render_height is not None:
            render_height = max(0, render_height)

        lines = list(
            islice(
                Segment.split_and_crop_lines(
                    _rendered,
                    render_options.max_width,
                    include_new_lines=new_lines,
                    pad=pad,
                    style=style,
                ),
                None,
                render_height,
            )
        )
        if render_options.height is not None:
            extra_lines = render_options.height - len(lines)
            if extra_lines > 0:
                pad_line = [
                    (
                        [
                            Segment(" " * render_options.max_width, style),
                            Segment("\n"),
                        ]
                        if new_lines
                        else [Segment(" " * render_options.max_width, style)]
                    )
                ]
                lines.extend(pad_line * extra_lines)

        return lines