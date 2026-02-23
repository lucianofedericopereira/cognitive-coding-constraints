# Source : https://github.com/tornadoweb/tornado/blob/master/tornado/web.py (line 1326)
# License: Apache-2.0
# Complexity: 10
# Tier   : tier2

def send_error(self, status_code: int = 500, **kwargs: Any) -> None:
    """Sends the given HTTP error code to the browser.

    If `flush()` has already been called, it is not possible to send
    an error, so this method will simply terminate the response.
    If output has been written but not yet flushed, it will be discarded
    and replaced with the error page.

    Override `write_error()` to customize the error page that is returned.
    Additional keyword arguments are passed through to `write_error`.
    """
    if self._headers_written:
        gen_log.error("Cannot send error response after headers written")
        if not self._finished:
            # If we get an error between writing headers and finishing,
            # we are unlikely to be able to finish due to a
            # Content-Length mismatch. Try anyway to release the
            # socket.
            try:
                self.finish()
            except Exception:
                gen_log.error("Failed to flush partial response", exc_info=True)
        return
    self.clear()

    reason = kwargs.get("reason")
    if "exc_info" in kwargs:
        exception = kwargs["exc_info"][1]
        if isinstance(exception, HTTPError) and exception.reason:
            reason = exception.reason
    self.set_status(status_code, reason=reason)
    try:
        if status_code != 304:
            self.write_error(status_code, **kwargs)
    except Exception:
        app_log.error("Uncaught exception in write_error", exc_info=True)
    if not self._finished:
        self.finish()