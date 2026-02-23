# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 3672)
# License: MIT
# Complexity: 1
# Tier   : tier1

def _like_percent_literal(self):
    return elements.literal_column("'%'", type_=sqltypes.STRINGTYPE)