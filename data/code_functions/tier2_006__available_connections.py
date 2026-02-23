# Source : https://github.com/aio-libs/aiohttp/blob/master/aiohttp/connector.py (line 528)
# License: Apache-2.0
# Complexity: 6
# Tier   : tier2

def _available_connections(self, key: "ConnectionKey") -> int:
    """
    Return number of available connections.

    The limit, limit_per_host and the connection key are taken into account.

    If it returns less than 1 means that there are no connections
    available.
    """
    # check total available connections
    # If there are no limits, this will always return 1
    total_remain = 1

    if self._limit and (total_remain := self._limit - len(self._acquired)) <= 0:
        return total_remain

    # check limit per host
    if host_remain := self._limit_per_host:
        if acquired := self._acquired_per_host.get(key):
            host_remain -= len(acquired)
        if total_remain > host_remain:
            return host_remain

    return total_remain