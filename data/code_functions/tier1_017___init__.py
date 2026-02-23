# Source : https://github.com/tornadoweb/tornado/blob/master/tornado/httpclient.py (line 743)
# License: Apache-2.0
# Complexity: 1
# Tier   : tier1

def __init__(
    self, request: HTTPRequest, defaults: Optional[Dict[str, Any]]
) -> None:
    self.request = request
    self.defaults = defaults