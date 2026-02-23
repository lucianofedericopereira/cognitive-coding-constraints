# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 2675)
# License: MIT
# Complexity: 17
# Tier   : tier3

def visit_column(
    self,
    column: ColumnClause[Any],
    add_to_result_map: Optional[_ResultMapAppender] = None,
    include_table: bool = True,
    result_map_targets: Tuple[Any, ...] = (),
    ambiguous_table_name_map: Optional[_AmbiguousTableNameMap] = None,
    **kwargs: Any,
) -> str:
    name = orig_name = column.name
    if name is None:
        name = self._fallback_column_name(column)

    is_literal = column.is_literal
    if not is_literal and isinstance(name, elements._truncated_label):
        name = self._truncated_identifier("colident", name)

    if add_to_result_map is not None:
        targets = (column, name, column.key) + result_map_targets
        if column._tq_label:
            targets += (column._tq_label,)

        add_to_result_map(name, orig_name, targets, column.type)

    if is_literal:
        # note we are not currently accommodating for
        # literal_column(quoted_name('ident', True)) here
        name = self.escape_literal_column(name)
    else:
        name = self.preparer.quote(name)
    table = column.table
    if table is None or not include_table or not table.named_with_column:
        return name
    else:
        effective_schema = self.preparer.schema_for_object(table)

        if effective_schema:
            schema_prefix = (
                self.preparer.quote_schema(effective_schema) + "."
            )
        else:
            schema_prefix = ""

        if TYPE_CHECKING:
            assert isinstance(table, NamedFromClause)
        tablename = table.name

        if (
            not effective_schema
            and ambiguous_table_name_map
            and tablename in ambiguous_table_name_map
        ):
            tablename = ambiguous_table_name_map[tablename]

        if isinstance(tablename, elements._truncated_label):
            tablename = self._truncated_identifier("alias", tablename)

        return schema_prefix + self.preparer.quote(tablename) + "." + name