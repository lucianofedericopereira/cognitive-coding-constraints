# Source : https://github.com/tornadoweb/tornado/blob/master/tornado/ioloop.py (line 441)
# License: Apache-2.0
# Complexity: 1
# Tier   : tier1

def start(self) -> None:
    """Starts the I/O loop.

    The loop will run until one of the callbacks calls `stop()`, which
    will make the loop stop after the current event iteration completes.
    """
    raise NotImplementedError()