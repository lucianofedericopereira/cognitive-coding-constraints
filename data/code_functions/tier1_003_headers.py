# Source : https://github.com/encode/httpx/blob/master/httpx/_client.py (line 306)
# License: BSD-3
# Complexity: 1
# Tier   : tier1

def headers(self, headers: HeaderTypes) -> None:
    client_headers = Headers(
        {
            b"Accept": b"*/*",
            b"Accept-Encoding": ACCEPT_ENCODING.encode("ascii"),
            b"Connection": b"keep-alive",
            b"User-Agent": USER_AGENT.encode("ascii"),
        }
    )
    client_headers.update(headers)
    self._headers = client_headers