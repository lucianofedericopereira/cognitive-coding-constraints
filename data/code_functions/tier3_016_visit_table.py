# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 5530)
# License: MIT
# Complexity: 14
# Tier   : tier3

def visit_table(
    self,
    table,
    asfrom=False,
    iscrud=False,
    ashint=False,
    fromhints=None,
    use_schema=True,
    from_linter=None,
    ambiguous_table_name_map=None,
    enclosing_alias=None,
    within_tstring=False,
    **kwargs,
):
    if from_linter:
        from_linter.froms[table] = table.fullname

    if asfrom or ashint or within_tstring:
        effective_schema = self.preparer.schema_for_object(table)

        if use_schema and effective_schema:
            ret = (
                self.preparer.quote_schema(effective_schema)
                + "."
                + self.preparer.quote(table.name)
            )
        else:
            ret = self.preparer.quote(table.name)

            if (
                (
                    enclosing_alias is None
                    or enclosing_alias.element is not table
                )
                and not effective_schema
                and ambiguous_table_name_map
                and table.name in ambiguous_table_name_map
            ):
                anon_name = self._truncated_identifier(
                    "alias", ambiguous_table_name_map[table.name]
                )

                ret = ret + self.get_render_as_alias_suffix(
                    self.preparer.format_alias(None, anon_name)
                )

        if fromhints and table in fromhints:
            ret = self.format_from_hint_text(
                ret, table, fromhints[table], iscrud
            )
        return ret
    else:
        return ""