# Source : https://github.com/aio-libs/aiohttp/blob/master/aiohttp/connector.py (line 1312)
# License: Apache-2.0
# Complexity: 22
# Tier   : tier4

async def _start_tls_connection(
    self,
    underlying_transport: asyncio.Transport,
    req: ClientRequest,
    timeout: "ClientTimeout",
    client_error: type[Exception] = ClientConnectorError,
) -> tuple[asyncio.BaseTransport, ResponseHandler]:
    """Wrap the raw TCP transport with TLS."""
    tls_proto = self._factory()  # Create a brand new proto for TLS
    sslcontext = self._get_ssl_context(req)
    if TYPE_CHECKING:
        # _start_tls_connection is unreachable in the current code path
        # if sslcontext is None.
        assert sslcontext is not None

    try:
        async with ceil_timeout(
            timeout.sock_connect, ceil_threshold=timeout.ceil_threshold
        ):
            try:
                # ssl_shutdown_timeout is only available in Python 3.11+
                if sys.version_info >= (3, 11) and self._ssl_shutdown_timeout:
                    tls_transport = await self._loop.start_tls(
                        underlying_transport,
                        tls_proto,
                        sslcontext,
                        server_hostname=req.server_hostname or req.url.raw_host,
                        ssl_handshake_timeout=timeout.total,
                        ssl_shutdown_timeout=self._ssl_shutdown_timeout,
                    )
                else:
                    tls_transport = await self._loop.start_tls(
                        underlying_transport,
                        tls_proto,
                        sslcontext,
                        server_hostname=req.server_hostname or req.url.raw_host,
                        ssl_handshake_timeout=timeout.total,
                    )
            except BaseException:
                # We need to close the underlying transport since
                # `start_tls()` probably failed before it had a
                # chance to do this:
                if self._ssl_shutdown_timeout == 0:
                    underlying_transport.abort()
                else:
                    underlying_transport.close()
                raise
            if isinstance(tls_transport, asyncio.Transport):
                fingerprint = self._get_fingerprint(req)
                if fingerprint:
                    try:
                        fingerprint.check(tls_transport)
                    except ServerFingerprintMismatch:
                        tls_transport.close()
                        if not self._cleanup_closed_disabled:
                            self._cleanup_closed_transports.append(tls_transport)
                        raise
    except cert_errors as exc:
        raise ClientConnectorCertificateError(req.connection_key, exc) from exc
    except ssl_errors as exc:
        raise ClientConnectorSSLError(req.connection_key, exc) from exc
    except OSError as exc:
        if exc.errno is None and isinstance(exc, asyncio.TimeoutError):
            raise
        raise client_error(req.connection_key, exc) from exc
    except TypeError as type_err:
        # Example cause looks like this:
        # TypeError: transport <asyncio.sslproto._SSLProtocolTransport
        # object at 0x7f760615e460> is not supported by start_tls()

        raise ClientConnectionError(
            "Cannot initialize a TLS-in-TLS connection to host "
            f"{req.url.host!s}:{req.url.port:d} through an underlying connection "
            f"to an HTTPS proxy {req.proxy!s} ssl:{req.ssl or 'default'} "
            f"[{type_err!s}]"
        ) from type_err
    else:
        if tls_transport is None:
            msg = "Failed to start TLS (possibly caused by closing transport)"
            raise client_error(req.connection_key, OSError(msg))
        tls_proto.connection_made(
            tls_transport
        )  # Kick the state machine of the new TLS protocol

    return tls_transport, tls_proto