# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 3849)
# License: MIT
# Complexity: 37
# Tier   : tier4

def visit_bindparam(
    self,
    bindparam,
    within_columns_clause=False,
    literal_binds=False,
    skip_bind_expression=False,
    literal_execute=False,
    render_postcompile=False,
    is_upsert_set=False,
    **kwargs,
):
    # Detect parametrized bindparams in upsert SET clause for issue #13130
    if (
        is_upsert_set
        and bindparam.value is None
        and bindparam.callable is None
        and self._insertmanyvalues is not None
    ):
        self._insertmanyvalues = self._insertmanyvalues._replace(
            has_upsert_bound_parameters=True
        )

    if not skip_bind_expression:
        impl = bindparam.type.dialect_impl(self.dialect)
        if impl._has_bind_expression:
            bind_expression = impl.bind_expression(bindparam)
            wrapped = self.process(
                bind_expression,
                skip_bind_expression=True,
                within_columns_clause=within_columns_clause,
                literal_binds=literal_binds and not bindparam.expanding,
                literal_execute=literal_execute,
                render_postcompile=render_postcompile,
                **kwargs,
            )
            if bindparam.expanding:
                # for postcompile w/ expanding, move the "wrapped" part
                # of this into the inside

                m = re.match(
                    r"^(.*)\(__\[POSTCOMPILE_(\S+?)\]\)(.*)$", wrapped
                )
                assert m, "unexpected format for expanding parameter"
                wrapped = "(__[POSTCOMPILE_%s~~%s~~REPL~~%s~~])" % (
                    m.group(2),
                    m.group(1),
                    m.group(3),
                )

                if literal_binds:
                    ret = self.render_literal_bindparam(
                        bindparam,
                        within_columns_clause=True,
                        bind_expression_template=wrapped,
                        **kwargs,
                    )
                    return f"({ret})"

            return wrapped

    if not literal_binds:
        literal_execute = (
            literal_execute
            or bindparam.literal_execute
            or (within_columns_clause and self.ansi_bind_rules)
        )
        post_compile = literal_execute or bindparam.expanding
    else:
        post_compile = False

    if literal_binds:
        ret = self.render_literal_bindparam(
            bindparam, within_columns_clause=True, **kwargs
        )
        if bindparam.expanding:
            ret = f"({ret})"
        return ret

    name = self._truncate_bindparam(bindparam)

    if name in self.binds:
        existing = self.binds[name]
        if existing is not bindparam:
            if (
                (existing.unique or bindparam.unique)
                and not existing.proxy_set.intersection(
                    bindparam.proxy_set
                )
                and not existing._cloned_set.intersection(
                    bindparam._cloned_set
                )
            ):
                raise exc.CompileError(
                    "Bind parameter '%s' conflicts with "
                    "unique bind parameter of the same name" % name
                )
            elif existing.expanding != bindparam.expanding:
                raise exc.CompileError(
                    "Can't reuse bound parameter name '%s' in both "
                    "'expanding' (e.g. within an IN expression) and "
                    "non-expanding contexts.  If this parameter is to "
                    "receive a list/array value, set 'expanding=True' on "
                    "it for expressions that aren't IN, otherwise use "
                    "a different parameter name." % (name,)
                )
            elif existing._is_crud or bindparam._is_crud:
                if existing._is_crud and bindparam._is_crud:
                    # TODO: this condition is not well understood.
                    # see tests in test/sql/test_update.py
                    raise exc.CompileError(
                        "Encountered unsupported case when compiling an "
                        "INSERT or UPDATE statement.  If this is a "
                        "multi-table "
                        "UPDATE statement, please provide string-named "
                        "arguments to the "
                        "values() method with distinct names; support for "
                        "multi-table UPDATE statements that "
                        "target multiple tables for UPDATE is very "
                        "limited",
                    )
                else:
                    raise exc.CompileError(
                        f"bindparam() name '{bindparam.key}' is reserved "
                        "for automatic usage in the VALUES or SET "
                        "clause of this "
                        "insert/update statement.   Please use a "
                        "name other than column name when using "
                        "bindparam() "
                        "with insert() or update() (for example, "
                        f"'b_{bindparam.key}')."
                    )

    self.binds[bindparam.key] = self.binds[name] = bindparam

    # if we are given a cache key that we're going to match against,
    # relate the bindparam here to one that is most likely present
    # in the "extracted params" portion of the cache key.  this is used
    # to set up a positional mapping that is used to determine the
    # correct parameters for a subsequent use of this compiled with
    # a different set of parameter values.   here, we accommodate for
    # parameters that may have been cloned both before and after the cache
    # key was been generated.
    ckbm_tuple = self._cache_key_bind_match

    if ckbm_tuple:
        ckbm, cksm = ckbm_tuple
        for bp in bindparam._cloned_set:
            if bp.key in cksm:
                cb = cksm[bp.key]
                ckbm[cb].append(bindparam)

    if bindparam.isoutparam:
        self.has_out_parameters = True

    if post_compile:
        if render_postcompile:
            self._render_postcompile = True

        if literal_execute:
            self.literal_execute_params |= {bindparam}
        else:
            self.post_compile_params |= {bindparam}

    ret = self.bindparam_string(
        name,
        post_compile=post_compile,
        expanding=bindparam.expanding,
        bindparam_type=bindparam.type,
        **kwargs,
    )

    if bindparam.expanding:
        ret = f"({ret})"

    return ret