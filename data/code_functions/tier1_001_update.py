# Source : https://github.com/Textualize/rich/blob/master/rich/console.py (line 420)
# License: MIT
# Complexity: 4
# Tier   : tier1

def update(
    self, *renderables: RenderableType, style: Optional[StyleType] = None
) -> None:
    """Update the screen.

    Args:
        renderable (RenderableType, optional): Optional renderable to replace current renderable,
            or None for no change. Defaults to None.
        style: (Style, optional): Replacement style, or None for no change. Defaults to None.
    """
    if renderables:
        self.screen.renderable = (
            Group(*renderables) if len(renderables) > 1 else renderables[0]
        )
    if style is not None:
        self.screen.style = style
    self.console.print(self.screen, end="")