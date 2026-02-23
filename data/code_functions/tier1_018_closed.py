# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/engine/base.py (line 553)
# License: MIT
# Complexity: 2
# Tier   : tier1

def closed(self) -> bool:
    """Return True if this connection is closed."""

    return self._dbapi_connection is None and not self.__can_reconnect