# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 7363)
# License: MIT
# Complexity: 8
# Tier   : tier2

def get_column_specification(
    self, column: Column[Any], **kwargs: Any
) -> str:
    colspec = (
        self.preparer.format_column(column)
        + " "
        + self.dialect.type_compiler_instance.process(
            column.type, type_expression=column
        )
    )
    default = self.get_column_default_string(column)
    if default is not None:
        colspec += " DEFAULT " + default

    if column.computed is not None:
        colspec += " " + self.process(column.computed)

    if (
        column.identity is not None
        and self.dialect.supports_identity_columns
    ):
        colspec += " " + self.process(column.identity)

    if not column.nullable and (
        not column.identity or not self.dialect.supports_identity_columns
    ):
        colspec += " NOT NULL"
    return colspec