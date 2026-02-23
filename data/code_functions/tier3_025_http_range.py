# Source : https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web_request.py (line 566)
# License: Apache-2.0
# Complexity: 11
# Tier   : tier3

def http_range(self) -> "slice[int, int, int]":
    """The content of Range HTTP header.

    Return a slice instance.

    """
    rng = self._headers.get(hdrs.RANGE)
    start, end = None, None
    if rng is not None:
        try:
            pattern = r"^bytes=(\d*)-(\d*)$"
            start, end = re.findall(pattern, rng, re.ASCII)[0]
        except IndexError:  # pattern was not found in header
            raise ValueError("range not in acceptable format")

        end = int(end) if end else None
        start = int(start) if start else None

        if start is None and end is not None:
            # end with no start is to return tail of content
            start = -end
            end = None

        if start is not None and end is not None:
            # end is inclusive in range header, exclusive for slice
            end += 1

            if start >= end:
                raise ValueError("start cannot be after end")

        if start is end is None:  # No valid range supplied
            raise ValueError("No start or end of range specified")

    return slice(start, end, 1)