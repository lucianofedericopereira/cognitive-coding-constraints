# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 4949)
# License: MIT
# Complexity: 42
# Tier   : tier4

def visit_select(
    self,
    select_stmt,
    asfrom=False,
    insert_into=False,
    fromhints=None,
    compound_index=None,
    select_wraps_for=None,
    lateral=False,
    from_linter=None,
    **kwargs,
):
    assert select_wraps_for is None, (
        "SQLAlchemy 1.4 requires use of "
        "the translate_select_structure hook for structural "
        "translations of SELECT objects"
    )
    if self._collect_params:
        self._add_to_params(select_stmt)

    # initial setup of SELECT.  the compile_state_factory may now
    # be creating a totally different SELECT from the one that was
    # passed in.  for ORM use this will convert from an ORM-state
    # SELECT to a regular "Core" SELECT.  other composed operations
    # such as computation of joins will be performed.

    kwargs["within_columns_clause"] = False

    compile_state = select_stmt._compile_state_factory(
        select_stmt, self, **kwargs
    )
    kwargs["ambiguous_table_name_map"] = (
        compile_state._ambiguous_table_name_map
    )

    select_stmt = compile_state.statement

    toplevel = not self.stack

    if toplevel and not self.compile_state:
        self.compile_state = compile_state

    is_embedded_select = compound_index is not None or insert_into

    # translate step for Oracle, SQL Server which often need to
    # restructure the SELECT to allow for LIMIT/OFFSET and possibly
    # other conditions
    if self.translate_select_structure:
        new_select_stmt = self.translate_select_structure(
            select_stmt, asfrom=asfrom, **kwargs
        )

        # if SELECT was restructured, maintain a link to the originals
        # and assemble a new compile state
        if new_select_stmt is not select_stmt:
            compile_state_wraps_for = compile_state
            select_wraps_for = select_stmt
            select_stmt = new_select_stmt

            compile_state = select_stmt._compile_state_factory(
                select_stmt, self, **kwargs
            )
            select_stmt = compile_state.statement

    entry = self._default_stack_entry if toplevel else self.stack[-1]

    populate_result_map = need_column_expressions = (
        toplevel
        or entry.get("need_result_map_for_compound", False)
        or entry.get("need_result_map_for_nested", False)
    )

    # indicates there is a CompoundSelect in play and we are not the
    # first select
    if compound_index:
        populate_result_map = False

    # this was first proposed as part of #3372; however, it is not
    # reached in current tests and could possibly be an assertion
    # instead.
    if not populate_result_map and "add_to_result_map" in kwargs:
        del kwargs["add_to_result_map"]

    froms = self._setup_select_stack(
        select_stmt, compile_state, entry, asfrom, lateral, compound_index
    )

    column_clause_args = kwargs.copy()
    column_clause_args.update(
        {"within_label_clause": False, "within_columns_clause": False}
    )

    text = "SELECT "  # we're off to a good start !

    if select_stmt._post_select_clause is not None:
        psc = self.process(select_stmt._post_select_clause, **kwargs)
        if psc is not None:
            text += psc + " "

    if select_stmt._hints:
        hint_text, byfrom = self._setup_select_hints(select_stmt)
        if hint_text:
            text += hint_text + " "
    else:
        byfrom = None

    if select_stmt._independent_ctes:
        self._dispatch_independent_ctes(select_stmt, kwargs)

    if select_stmt._prefixes:
        text += self._generate_prefixes(
            select_stmt, select_stmt._prefixes, **kwargs
        )

    text += self.get_select_precolumns(select_stmt, **kwargs)

    if select_stmt._pre_columns_clause is not None:
        pcc = self.process(select_stmt._pre_columns_clause, **kwargs)
        if pcc is not None:
            text += pcc + " "

    # the actual list of columns to print in the SELECT column list.
    inner_columns = [
        c
        for c in [
            self._label_select_column(
                select_stmt,
                column,
                populate_result_map,
                asfrom,
                column_clause_args,
                name=name,
                proxy_name=proxy_name,
                fallback_label_name=fallback_label_name,
                column_is_repeated=repeated,
                need_column_expressions=need_column_expressions,
            )
            for (
                name,
                proxy_name,
                fallback_label_name,
                column,
                repeated,
            ) in compile_state.columns_plus_names
        ]
        if c is not None
    ]

    if populate_result_map and select_wraps_for is not None:
        # if this select was generated from translate_select,
        # rewrite the targeted columns in the result map

        translate = dict(
            zip(
                [
                    name
                    for (
                        key,
                        proxy_name,
                        fallback_label_name,
                        name,
                        repeated,
                    ) in compile_state.columns_plus_names
                ],
                [
                    name
                    for (
                        key,
                        proxy_name,
                        fallback_label_name,
                        name,
                        repeated,
                    ) in compile_state_wraps_for.columns_plus_names
                ],
            )
        )

        self._result_columns = [
            ResultColumnsEntry(
                key, name, tuple(translate.get(o, o) for o in obj), type_
            )
            for key, name, obj, type_ in self._result_columns
        ]

    text = self._compose_select_body(
        text,
        select_stmt,
        compile_state,
        inner_columns,
        froms,
        byfrom,
        toplevel,
        kwargs,
    )

    if select_stmt._post_body_clause is not None:
        pbc = self.process(select_stmt._post_body_clause, **kwargs)
        if pbc:
            text += " " + pbc

    if select_stmt._statement_hints:
        per_dialect = [
            ht
            for (dialect_name, ht) in select_stmt._statement_hints
            if dialect_name in ("*", self.dialect.name)
        ]
        if per_dialect:
            text += " " + self.get_statement_hint_text(per_dialect)

    # In compound query, CTEs are shared at the compound level
    if self.ctes and (not is_embedded_select or toplevel):
        nesting_level = len(self.stack) if not toplevel else None
        text = self._render_cte_clause(nesting_level=nesting_level) + text

    if select_stmt._suffixes:
        text += " " + self._generate_prefixes(
            select_stmt, select_stmt._suffixes, **kwargs
        )

    self.stack.pop(-1)

    return text