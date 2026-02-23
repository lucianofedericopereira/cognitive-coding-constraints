# Source : https://github.com/tornadoweb/tornado/blob/master/tornado/ioloop.py (line 361)
# License: Apache-2.0
# Complexity: 2
# Tier   : tier1

def initialize(self, make_current: bool = True) -> None:
    if make_current:
        self._make_current()