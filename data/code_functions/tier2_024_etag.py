# Source : https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web_response.py (line 297)
# License: Apache-2.0
# Complexity: 10
# Tier   : tier2

def etag(self, value: ETag | str | None) -> None:
    if value is None:
        self._headers.pop(hdrs.ETAG, None)
    elif (isinstance(value, str) and value == ETAG_ANY) or (
        isinstance(value, ETag) and value.value == ETAG_ANY
    ):
        self._headers[hdrs.ETAG] = ETAG_ANY
    elif isinstance(value, str):
        validate_etag_value(value)
        self._headers[hdrs.ETAG] = f'"{value}"'
    elif isinstance(value, ETag) and isinstance(value.value, str):  # type: ignore[redundant-expr]
        validate_etag_value(value.value)
        hdr_value = f'W/"{value.value}"' if value.is_weak else f'"{value.value}"'
        self._headers[hdrs.ETAG] = hdr_value
    else:
        raise ValueError(
            f"Unsupported etag type: {type(value)}. "
            f"etag must be str, ETag or None"
        )