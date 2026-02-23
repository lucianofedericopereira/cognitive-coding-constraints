# Source : https://github.com/encode/httpx/blob/master/httpx/_client.py (line 239)
# License: BSD-3
# Complexity: 6
# Tier   : tier2

def _get_proxy_map(
    self, proxy: ProxyTypes | None, allow_env_proxies: bool
) -> dict[str, Proxy | None]:
    if proxy is None:
        if allow_env_proxies:
            return {
                key: None if url is None else Proxy(url=url)
                for key, url in get_environment_proxies().items()
            }
        return {}
    else:
        proxy = Proxy(url=proxy) if isinstance(proxy, (str, URL)) else proxy
        return {"all://": proxy}