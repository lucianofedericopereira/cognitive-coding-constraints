# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 7528)
# License: MIT
# Complexity: 3
# Tier   : tier1

def define_constraint_cascades(
    self, constraint: ForeignKeyConstraint
) -> str:
    text = ""
    if constraint.ondelete is not None:
        text += self.define_constraint_ondelete_cascade(constraint)

    if constraint.onupdate is not None:
        text += self.define_constraint_onupdate_cascade(constraint)
    return text