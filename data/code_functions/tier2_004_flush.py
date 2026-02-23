# Source : https://github.com/tornadoweb/tornado/blob/master/tornado/web.py (line 1199)
# License: Apache-2.0
# Complexity: 10
# Tier   : tier2

def flush(self, include_footers: bool = False) -> "Future[None]":
    """Flushes the current output buffer to the network.

    .. versionchanged:: 4.0
       Now returns a `.Future` if no callback is given.

    .. versionchanged:: 6.0

       The ``callback`` argument was removed.
    """
    assert self.request.connection is not None
    chunk = b"".join(self._write_buffer)
    self._write_buffer = []
    if not self._headers_written:
        self._headers_written = True
        for transform in self._transforms:
            assert chunk is not None
            (
                self._status_code,
                self._headers,
                chunk,
            ) = transform.transform_first_chunk(
                self._status_code, self._headers, chunk, include_footers
            )
        # Ignore the chunk and only write the headers for HEAD requests
        if self.request.method == "HEAD":
            chunk = b""

        # Finalize the cookie headers (which have been stored in a side
        # object so an outgoing cookie could be overwritten before it
        # is sent).
        if hasattr(self, "_new_cookie"):
            for cookie in self._new_cookie.values():
                self.add_header("Set-Cookie", cookie.OutputString(None))

        start_line = httputil.ResponseStartLine("", self._status_code, self._reason)
        return self.request.connection.write_headers(
            start_line, self._headers, chunk
        )
    else:
        for transform in self._transforms:
            chunk = transform.transform_chunk(chunk, include_footers)
        # Ignore the chunk and only write the headers for HEAD requests
        if self.request.method != "HEAD":
            return self.request.connection.write(chunk)
        else:
            future = Future()  # type: Future[None]
            future.set_result(None)
            return future