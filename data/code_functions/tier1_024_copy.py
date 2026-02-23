# Source : https://github.com/Textualize/rich/blob/master/rich/text.py (line 443)
# License: MIT
# Complexity: 1
# Tier   : tier1

def copy(self) -> "Text":
    """Return a copy of this instance."""
    copy_self = Text(
        self.plain,
        style=self.style,
        justify=self.justify,
        overflow=self.overflow,
        no_wrap=self.no_wrap,
        end=self.end,
        tab_size=self.tab_size,
    )
    copy_self._spans[:] = self._spans
    return copy_self