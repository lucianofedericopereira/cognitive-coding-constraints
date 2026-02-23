# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/orm/session.py (line 4460)
# License: MIT
# Complexity: 3
# Tier   : tier1

def _is_clean(self) -> bool:
    return (
        not self.identity_map.check_modified()
        and not self._deleted
        and not self._new
    )