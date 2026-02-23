# Source : https://github.com/aio-libs/aiohttp/blob/master/aiohttp/connector.py (line 759)
# License: Apache-2.0
# Complexity: 8
# Tier   : tier2

def _release(
    self,
    key: "ConnectionKey",
    protocol: ResponseHandler,
    *,
    should_close: bool = False,
) -> None:
    if self._closed:
        # acquired connection is already released on connector closing
        return

    self._release_acquired(key, protocol)

    if self._force_close or should_close or protocol.should_close:
        transport = protocol.transport
        protocol.close()
        if key.is_ssl and not self._cleanup_closed_disabled:
            self._cleanup_closed_transports.append(transport)
        return

    self._conns[key].append((protocol, monotonic()))

    if self._cleanup_handle is None:
        self._cleanup_handle = helpers.weakref_handle(
            self,
            "_cleanup",
            self._keepalive_timeout,
            self._loop,
            timeout_ceil_threshold=self._timeout_ceil_threshold,
        )