# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 3831)
# License: MIT
# Complexity: 1
# Tier   : tier1

def visit_regexp_replace_op_binary(
    self, binary: BinaryExpression[Any], operator: Any, **kw: Any
) -> str:
    raise exc.CompileError(
        "%s dialect does not support regular expression replacements"
        % self.dialect.name
    )