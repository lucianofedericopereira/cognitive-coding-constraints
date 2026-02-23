# Source : https://github.com/aio-libs/aiohttp/blob/master/aiohttp/connector.py (line 1044)
# License: Apache-2.0
# Complexity: 17
# Tier   : tier3

async def _resolve_host(
    self, host: str, port: int, traces: Sequence["Trace"] | None = None
) -> list[ResolveResult]:
    """Resolve host and return list of addresses."""
    if is_ip_address(host):
        return [
            {
                "hostname": host,
                "host": host,
                "port": port,
                "family": self._family,
                "proto": 0,
                "flags": 0,
            }
        ]

    if not self._use_dns_cache:
        if traces:
            for trace in traces:
                await trace.send_dns_resolvehost_start(host)

        res = await self._resolver.resolve(host, port, family=self._family)

        if traces:
            for trace in traces:
                await trace.send_dns_resolvehost_end(host)

        return res

    key = (host, port)
    if key in self._cached_hosts and not self._cached_hosts.expired(key):
        # get result early, before any await (#4014)
        result = self._cached_hosts.next_addrs(key)

        if traces:
            for trace in traces:
                await trace.send_dns_cache_hit(host)
        return result

    futures: set[asyncio.Future[None]]
    #
    # If multiple connectors are resolving the same host, we wait
    # for the first one to resolve and then use the result for all of them.
    # We use a throttle to ensure that we only resolve the host once
    # and then use the result for all the waiters.
    #
    if key in self._throttle_dns_futures:
        # get futures early, before any await (#4014)
        futures = self._throttle_dns_futures[key]
        future: asyncio.Future[None] = self._loop.create_future()
        futures.add(future)
        if traces:
            for trace in traces:
                await trace.send_dns_cache_hit(host)
        try:
            await future
        finally:
            futures.discard(future)
        return self._cached_hosts.next_addrs(key)

    # update dict early, before any await (#4014)
    self._throttle_dns_futures[key] = futures = set()
    # In this case we need to create a task to ensure that we can shield
    # the task from cancellation as cancelling this lookup should not cancel
    # the underlying lookup or else the cancel event will get broadcast to
    # all the waiters across all connections.
    #
    coro = self._resolve_host_with_throttle(key, host, port, futures, traces)
    loop = asyncio.get_running_loop()
    if sys.version_info >= (3, 12):
        # Optimization for Python 3.12, try to send immediately
        resolved_host_task = asyncio.Task(coro, loop=loop, eager_start=True)
    else:
        resolved_host_task = loop.create_task(coro)

    if not resolved_host_task.done():
        self._resolve_host_tasks.add(resolved_host_task)
        resolved_host_task.add_done_callback(self._resolve_host_tasks.discard)

    try:
        return await asyncio.shield(resolved_host_task)
    except asyncio.CancelledError:

        def drop_exception(fut: "asyncio.Future[list[ResolveResult]]") -> None:
            with suppress(Exception, asyncio.CancelledError):
                fut.result()

        resolved_host_task.add_done_callback(drop_exception)
        raise