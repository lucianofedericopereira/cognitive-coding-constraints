# Source : https://github.com/Textualize/rich/blob/master/rich/table.py (line 589)
# License: MIT
# Complexity: 14
# Tier   : tier3

def _collapse_widths(
    cls, widths: List[int], wrapable: List[bool], max_width: int
) -> List[int]:
    """Reduce widths so that the total is under max_width.

    Args:
        widths (List[int]): List of widths.
        wrapable (List[bool]): List of booleans that indicate if a column may shrink.
        max_width (int): Maximum width to reduce to.

    Returns:
        List[int]: A new list of widths.
    """
    total_width = sum(widths)
    excess_width = total_width - max_width
    if any(wrapable):
        while total_width and excess_width > 0:
            max_column = max(
                width for width, allow_wrap in zip(widths, wrapable) if allow_wrap
            )
            second_max_column = max(
                width if allow_wrap and width != max_column else 0
                for width, allow_wrap in zip(widths, wrapable)
            )
            column_difference = max_column - second_max_column
            ratios = [
                (1 if (width == max_column and allow_wrap) else 0)
                for width, allow_wrap in zip(widths, wrapable)
            ]
            if not any(ratios) or not column_difference:
                break
            max_reduce = [min(excess_width, column_difference)] * len(widths)
            widths = ratio_reduce(excess_width, ratios, max_reduce, widths)

            total_width = sum(widths)
            excess_width = total_width - max_width
    return widths