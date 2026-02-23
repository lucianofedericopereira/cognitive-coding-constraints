# Source : https://github.com/aio-libs/aiohttp/blob/master/aiohttp/client.py (line 476)
# License: Apache-2.0
# Complexity: 95
# Tier   : tier4

async def _request(
    self,
    method: str,
    str_or_url: StrOrURL,
    *,
    params: Query = None,
    data: Any = None,
    json: Any = None,
    cookies: LooseCookies | None = None,
    headers: LooseHeaders | None = None,
    skip_auto_headers: Iterable[str] | None = None,
    auth: BasicAuth | None = None,
    allow_redirects: bool = True,
    max_redirects: int = 10,
    compress: str | bool = False,
    chunked: bool | None = None,
    expect100: bool = False,
    raise_for_status: (
        None | bool | Callable[[ClientResponse], Awaitable[None]]
    ) = None,
    read_until_eof: bool = True,
    proxy: StrOrURL | None = None,
    proxy_auth: BasicAuth | None = None,
    timeout: ClientTimeout | _SENTINEL | None = sentinel,
    ssl: SSLContext | bool | Fingerprint = True,
    server_hostname: str | None = None,
    proxy_headers: LooseHeaders | None = None,
    trace_request_ctx: object = None,
    read_bufsize: int | None = None,
    auto_decompress: bool | None = None,
    max_line_size: int | None = None,
    max_field_size: int | None = None,
    max_headers: int | None = None,
    middlewares: Sequence[ClientMiddlewareType] | None = None,
) -> ClientResponse:
    # NOTE: timeout clamps existing connect and read timeouts.  We cannot
    # set the default to None because we need to detect if the user wants
    # to use the existing timeouts by setting timeout to None.

    if self.closed:
        raise RuntimeError("Session is closed")

    if not isinstance(ssl, SSL_ALLOWED_TYPES):
        raise TypeError(
            "ssl should be SSLContext, Fingerprint, or bool, "
            f"got {ssl!r} instead."
        )

    if data is not None and json is not None:
        raise ValueError(
            "data and json parameters can not be used at the same time"
        )
    elif json is not None:
        if self._json_serialize_bytes is not None:
            data = payload.JsonBytesPayload(json, dumps=self._json_serialize_bytes)
        else:
            data = payload.JsonPayload(json, dumps=self._json_serialize)

    redirects = 0
    history: list[ClientResponse] = []
    version = self._version
    params = params or {}

    # Merge with default headers and transform to CIMultiDict
    headers = self._prepare_headers(headers)

    try:
        url = self._build_url(str_or_url)
    except ValueError as e:
        raise InvalidUrlClientError(str_or_url) from e

    assert self._connector is not None
    if url.scheme not in self._connector.allowed_protocol_schema_set:
        raise NonHttpUrlClientError(url)

    skip_headers: Iterable[istr] | None
    if skip_auto_headers is not None:
        skip_headers = {
            istr(i) for i in skip_auto_headers
        } | self._skip_auto_headers
    elif self._skip_auto_headers:
        skip_headers = self._skip_auto_headers
    else:
        skip_headers = None

    if proxy is None:
        proxy = self._default_proxy
    if proxy_auth is None:
        proxy_auth = self._default_proxy_auth

    if proxy is None:
        proxy_headers = None
    else:
        proxy_headers = self._prepare_headers(proxy_headers)
        try:
            proxy = URL(proxy)
        except ValueError as e:
            raise InvalidURL(proxy) from e

    if timeout is sentinel or timeout is None:
        real_timeout: ClientTimeout = self._timeout
    else:
        real_timeout = timeout
    # timeout is cumulative for all request operations
    # (request, redirects, responses, data consuming)
    tm = TimeoutHandle(
        self._loop, real_timeout.total, ceil_threshold=real_timeout.ceil_threshold
    )
    handle = tm.start()

    if read_bufsize is None:
        read_bufsize = self._read_bufsize

    if auto_decompress is None:
        auto_decompress = self._auto_decompress

    if max_line_size is None:
        max_line_size = self._max_line_size

    if max_field_size is None:
        max_field_size = self._max_field_size

    if max_headers is None:
        max_headers = self._max_headers

    traces = [
        Trace(
            self,
            trace_config,
            trace_config.trace_config_ctx(trace_request_ctx=trace_request_ctx),
        )
        for trace_config in self._trace_configs
    ]

    for trace in traces:
        await trace.send_request_start(method, url.update_query(params), headers)

    timer = tm.timer()
    try:
        with timer:
            # https://www.rfc-editor.org/rfc/rfc9112.html#name-retrying-requests
            retry_persistent_connection = (
                self._retry_connection and method in IDEMPOTENT_METHODS
            )
            while True:
                url, auth_from_url = strip_auth_from_url(url)
                if not url.raw_host:
                    # NOTE: Bail early, otherwise, causes `InvalidURL` through
                    # NOTE: `self._request_class()` below.
                    err_exc_cls = (
                        InvalidUrlRedirectClientError
                        if redirects
                        else InvalidUrlClientError
                    )
                    raise err_exc_cls(url)
                # If `auth` was passed for an already authenticated URL,
                # disallow only if this is the initial URL; this is to avoid issues
                # with sketchy redirects that are not the caller's responsibility
                if not history and (auth and auth_from_url):
                    raise ValueError(
                        "Cannot combine AUTH argument with "
                        "credentials encoded in URL"
                    )

                # Override the auth with the one from the URL only if we
                # have no auth, or if we got an auth from a redirect URL
                if auth is None or (history and auth_from_url is not None):
                    auth = auth_from_url

                if (
                    auth is None
                    and self._default_auth
                    and (
                        not self._base_url or self._base_url_origin == url.origin()
                    )
                ):
                    auth = self._default_auth

                # Try netrc if auth is still None and trust_env is enabled.
                if auth is None and self._trust_env and url.host is not None:
                    auth = await self._loop.run_in_executor(
                        None, self._get_netrc_auth, url.host
                    )

                # It would be confusing if we support explicit
                # Authorization header with auth argument
                if auth is not None and hdrs.AUTHORIZATION in headers:
                    raise ValueError(
                        "Cannot combine AUTHORIZATION header "
                        "with AUTH argument or credentials "
                        "encoded in URL"
                    )

                all_cookies = self._cookie_jar.filter_cookies(url)

                if cookies is not None:
                    tmp_cookie_jar = CookieJar(
                        quote_cookie=self._cookie_jar.quote_cookie
                    )
                    tmp_cookie_jar.update_cookies(cookies)
                    req_cookies = tmp_cookie_jar.filter_cookies(url)
                    if req_cookies:
                        all_cookies.load(req_cookies)

                proxy_: URL | None = None
                if proxy is not None:
                    proxy_ = URL(proxy)
                elif self._trust_env:
                    with suppress(LookupError):
                        proxy_, proxy_auth = await asyncio.to_thread(
                            get_env_proxy_for_url, url
                        )

                req = self._request_class(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    skip_auto_headers=skip_headers,
                    data=data,
                    cookies=all_cookies,
                    auth=auth,
                    version=version,
                    compress=compress,
                    chunked=chunked,
                    expect100=expect100,
                    loop=self._loop,
                    response_class=self._response_class,
                    proxy=proxy_,
                    proxy_auth=proxy_auth,
                    timer=timer,
                    session=self,
                    ssl=ssl,
                    server_hostname=server_hostname,
                    proxy_headers=proxy_headers,
                    traces=traces,
                    trust_env=self.trust_env,
                )

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

                # Apply middleware (if any) - per-request middleware overrides session middleware
                effective_middlewares = (
                    self._middlewares if middlewares is None else middlewares
                )

                if effective_middlewares:
                    handler = build_client_middlewares(
                        _connect_and_send_request, effective_middlewares
                    )
                else:
                    handler = _connect_and_send_request

                try:
                    resp = await handler(req)
                # Client connector errors should not be retried
                except (
                    ConnectionTimeoutError,
                    ClientConnectorError,
                    ClientConnectorCertificateError,
                    ClientConnectorSSLError,
                ):
                    raise
                except (ClientOSError, ServerDisconnectedError):
                    if retry_persistent_connection:
                        retry_persistent_connection = False
                        continue
                    raise
                except ClientError:
                    raise
                except OSError as exc:
                    if exc.errno is None and isinstance(exc, asyncio.TimeoutError):
                        raise
                    raise ClientOSError(*exc.args) from exc

                # Update cookies from raw headers to preserve duplicates
                if resp._raw_cookie_headers:
                    self._cookie_jar.update_cookies_from_headers(
                        resp._raw_cookie_headers, resp.url
                    )

                # redirects
                if resp.status in (301, 302, 303, 307, 308) and allow_redirects:
                    for trace in traces:
                        await trace.send_request_redirect(
                            method, url.update_query(params), headers, resp
                        )

                    redirects += 1
                    history.append(resp)
                    if max_redirects and redirects >= max_redirects:
                        if req._body is not None:
                            await req._body.close()
                        resp.close()
                        raise TooManyRedirects(
                            history[0].request_info, tuple(history)
                        )

                    # For 301 and 302, mimic IE, now changed in RFC
                    # https://github.com/kennethreitz/requests/pull/269
                    if (resp.status == 303 and resp.method != hdrs.METH_HEAD) or (
                        resp.status in (301, 302) and resp.method == hdrs.METH_POST
                    ):
                        method = hdrs.METH_GET
                        data = None
                        if headers.get(hdrs.CONTENT_LENGTH):
                            headers.pop(hdrs.CONTENT_LENGTH)
                    else:
                        # For 307/308, always preserve the request body
                        # For 301/302 with non-POST methods, preserve the request body
                        # https://www.rfc-editor.org/rfc/rfc9110#section-15.4.3-3.1
                        # Use the existing payload to avoid recreating it from a potentially consumed file
                        data = req._body

                    r_url = resp.headers.get(hdrs.LOCATION) or resp.headers.get(
                        hdrs.URI
                    )
                    if r_url is None:
                        # see github.com/aio-libs/aiohttp/issues/2022
                        break
                    else:
                        # reading from correct redirection
                        # response is forbidden
                        resp.release()

                    try:
                        parsed_redirect_url = URL(
                            r_url, encoded=not self._requote_redirect_url
                        )
                    except ValueError as e:
                        if req._body is not None:
                            await req._body.close()
                        resp.close()
                        raise InvalidUrlRedirectClientError(
                            r_url,
                            "Server attempted redirecting to a location that does not look like a URL",
                        ) from e

                    scheme = parsed_redirect_url.scheme
                    if scheme not in HTTP_AND_EMPTY_SCHEMA_SET:
                        if req._body is not None:
                            await req._body.close()
                        resp.close()
                        raise NonHttpUrlRedirectClientError(r_url)
                    elif not scheme:
                        parsed_redirect_url = url.join(parsed_redirect_url)

                    is_same_host_https_redirect = (
                        url.host == parsed_redirect_url.host
                        and parsed_redirect_url.scheme == "https"
                        and url.scheme == "http"
                    )

                    try:
                        redirect_origin = parsed_redirect_url.origin()
                    except ValueError as origin_val_err:
                        if req._body is not None:
                            await req._body.close()
                        resp.close()
                        raise InvalidUrlRedirectClientError(
                            parsed_redirect_url,
                            "Invalid redirect URL origin",
                        ) from origin_val_err

                    if (
                        not is_same_host_https_redirect
                        and url.origin() != redirect_origin
                    ):
                        auth = None
                        headers.pop(hdrs.AUTHORIZATION, None)

                    url = parsed_redirect_url
                    params = {}
                    resp.release()
                    continue

                break

        if req._body is not None:
            await req._body.close()
        # check response status
        if raise_for_status is None:
            raise_for_status = self._raise_for_status

        if raise_for_status is None:
            pass
        elif callable(raise_for_status):
            await raise_for_status(resp)
        elif raise_for_status:
            resp.raise_for_status()

        # register connection
        if handle is not None:
            if resp.connection is not None:
                resp.connection.add_callback(handle.cancel)
            else:
                handle.cancel()

        resp._history = tuple(history)

        for trace in traces:
            await trace.send_request_end(
                method, url.update_query(params), headers, resp
            )
        return resp

    except BaseException as e:
        # cleanup timer
        tm.close()
        if handle:
            handle.cancel()
            handle = None

        for trace in traces:
            await trace.send_request_exception(
                method, url.update_query(params), headers, e
            )
        raise