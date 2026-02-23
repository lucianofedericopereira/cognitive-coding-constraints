# Source : https://github.com/aio-libs/aiohttp/blob/master/aiohttp/client.py (line 715)
# License: Apache-2.0
# Complexity: 6
# Tier   : tier2

async def _connect_and_send_request(
    req: ClientRequest,
) -> ClientResponse:
    # connection timeout
    assert self._connector is not None
    try:
        conn = await self._connector.connect(
            req, traces=traces, timeout=real_timeout
        )
    except asyncio.TimeoutError as exc:
        raise ConnectionTimeoutError(
            f"Connection timeout to host {req.url}"
        ) from exc

    assert conn.protocol is not None
    conn.protocol.set_response_params(
        timer=timer,
        skip_payload=req.method in EMPTY_BODY_METHODS,
        read_until_eof=read_until_eof,
        auto_decompress=auto_decompress,
        read_timeout=real_timeout.sock_read,
        read_bufsize=read_bufsize,
        timeout_ceil_threshold=self._connector._timeout_ceil_threshold,
        max_line_size=max_line_size,
        max_field_size=max_field_size,
        max_headers=max_headers,
    )
    try:
        resp = await req._send(conn)
        try:
            await resp.start(conn)
        except BaseException:
            resp.close()
            raise
    except BaseException:
        conn.close()
        raise
    return resp