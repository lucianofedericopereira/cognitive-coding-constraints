# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 2448)
# License: MIT
# Complexity: 8
# Tier   : tier2

def visit_override_binds(self, override_binds, **kw):
    """SQL compile the nested element of an _OverrideBinds with
    bindparams swapped out.

    The _OverrideBinds is not normally expected to be compiled; it
    is meant to be used when an already cached statement is to be used,
    the compilation was already performed, and only the bound params should
    be swapped in at execution time.

    However, there are test cases that exericise this object, and
    additionally the ORM subquery loader is known to feed in expressions
    which include this construct into new queries (discovered in #11173),
    so it has to do the right thing at compile time as well.

    """

    # get SQL text first
    sqltext = override_binds.element._compiler_dispatch(self, **kw)

    # for a test compile that is not for caching, change binds after the
    # fact.  note that we don't try to
    # swap the bindparam as we compile, because our element may be
    # elsewhere in the statement already (e.g. a subquery or perhaps a
    # CTE) and was already visited / compiled. See
    # test_relationship_criteria.py ->
    #    test_selectinload_local_criteria_subquery
    for k in override_binds.translate:
        if k not in self.binds:
            continue
        bp = self.binds[k]

        # so this would work, just change the value of bp in place.
        # but we dont want to mutate things outside.
        # bp.value = override_binds.translate[bp.key]
        # continue

        # instead, need to replace bp with new_bp or otherwise accommodate
        # in all internal collections
        new_bp = bp._with_value(
            override_binds.translate[bp.key],
            maintain_key=True,
            required=False,
        )

        name = self.bind_names[bp]
        self.binds[k] = self.binds[name] = new_bp
        self.bind_names[new_bp] = name
        self.bind_names.pop(bp, None)

        if bp in self.post_compile_params:
            self.post_compile_params |= {new_bp}
        if bp in self.literal_execute_params:
            self.literal_execute_params |= {new_bp}

        ckbm_tuple = self._cache_key_bind_match
        if ckbm_tuple:
            ckbm, cksm = ckbm_tuple
            for bp in bp._cloned_set:
                if bp.key in cksm:
                    cb = cksm[bp.key]
                    ckbm[cb].append(new_bp)

    return sqltext