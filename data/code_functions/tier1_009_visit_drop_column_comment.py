# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 7294)
# License: MIT
# Complexity: 1
# Tier   : tier1

def visit_drop_column_comment(self, drop, **kw):
    return "COMMENT ON COLUMN %s IS NULL" % self.preparer.format_column(
        drop.element, use_table=True
    )