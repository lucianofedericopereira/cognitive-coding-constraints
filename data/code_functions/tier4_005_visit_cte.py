# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 4212)
# License: MIT
# Complexity: 45
# Tier   : tier4

def visit_cte(
    self,
    cte: CTE,
    asfrom: bool = False,
    ashint: bool = False,
    fromhints: Optional[_FromHintsType] = None,
    visiting_cte: Optional[CTE] = None,
    from_linter: Optional[FromLinter] = None,
    cte_opts: selectable._CTEOpts = selectable._CTEOpts(False),
    **kwargs: Any,
) -> Optional[str]:
    self_ctes = self._init_cte_state()
    assert self_ctes is self.ctes

    kwargs["visiting_cte"] = cte

    cte_name = cte.name

    if isinstance(cte_name, elements._truncated_label):
        cte_name = self._truncated_identifier("alias", cte_name)

    is_new_cte = True
    embedded_in_current_named_cte = False

    _reference_cte = cte._get_reference_cte()

    nesting = cte.nesting or cte_opts.nesting

    # check for CTE already encountered
    if _reference_cte in self.level_name_by_cte:
        cte_level, _, existing_cte_opts = self.level_name_by_cte[
            _reference_cte
        ]
        assert _ == cte_name

        cte_level_name = (cte_level, cte_name)
        existing_cte = self.ctes_by_level_name[cte_level_name]

        # check if we are receiving it here with a specific
        # "nest_here" location; if so, move it to this location

        if cte_opts.nesting:
            if existing_cte_opts.nesting:
                raise exc.CompileError(
                    "CTE is stated as 'nest_here' in "
                    "more than one location"
                )

            old_level_name = (cte_level, cte_name)
            cte_level = len(self.stack) if nesting else 1
            cte_level_name = new_level_name = (cte_level, cte_name)

            del self.ctes_by_level_name[old_level_name]
            self.ctes_by_level_name[new_level_name] = existing_cte
            self.level_name_by_cte[_reference_cte] = new_level_name + (
                cte_opts,
            )

    else:
        cte_level = len(self.stack) if nesting else 1
        cte_level_name = (cte_level, cte_name)

        if cte_level_name in self.ctes_by_level_name:
            existing_cte = self.ctes_by_level_name[cte_level_name]
        else:
            existing_cte = None

    if existing_cte is not None:
        embedded_in_current_named_cte = visiting_cte is existing_cte

        # we've generated a same-named CTE that we are enclosed in,
        # or this is the same CTE.  just return the name.
        if cte is existing_cte._restates or cte is existing_cte:
            is_new_cte = False
        elif existing_cte is cte._restates:
            # we've generated a same-named CTE that is
            # enclosed in us - we take precedence, so
            # discard the text for the "inner".
            del self_ctes[existing_cte]

            existing_cte_reference_cte = existing_cte._get_reference_cte()

            assert existing_cte_reference_cte is _reference_cte
            assert existing_cte_reference_cte is existing_cte

            del self.level_name_by_cte[existing_cte_reference_cte]
        else:
            if (
                # if the two CTEs have the same hash, which we expect
                # here means that one/both is an annotated of the other
                (hash(cte) == hash(existing_cte))
                # or...
                or (
                    (
                        # if they are clones, i.e. they came from the ORM
                        # or some other visit method
                        cte._is_clone_of is not None
                        or existing_cte._is_clone_of is not None
                    )
                    # and are deep-copy identical
                    and cte.compare(existing_cte)
                )
            ):
                # then consider these two CTEs the same
                is_new_cte = False
            else:
                # otherwise these are two CTEs that either will render
                # differently, or were indicated separately by the user,
                # with the same name
                raise exc.CompileError(
                    "Multiple, unrelated CTEs found with "
                    "the same name: %r" % cte_name
                )

    if not asfrom and not is_new_cte:
        return None

    if cte._cte_alias is not None:
        pre_alias_cte = cte._cte_alias
        cte_pre_alias_name = cte._cte_alias.name
        if isinstance(cte_pre_alias_name, elements._truncated_label):
            cte_pre_alias_name = self._truncated_identifier(
                "alias", cte_pre_alias_name
            )
    else:
        pre_alias_cte = cte
        cte_pre_alias_name = None

    if is_new_cte:
        self.ctes_by_level_name[cte_level_name] = cte
        self.level_name_by_cte[_reference_cte] = cte_level_name + (
            cte_opts,
        )

        if pre_alias_cte not in self.ctes:
            self.visit_cte(pre_alias_cte, **kwargs)

        if not cte_pre_alias_name and cte not in self_ctes:
            if cte.recursive:
                self.ctes_recursive = True
            text = self.preparer.format_alias(cte, cte_name)
            if cte.recursive or cte.element.name_cte_columns:
                col_source = cte.element

                # TODO: can we get at the .columns_plus_names collection
                # that is already (or will be?) generated for the SELECT
                # rather than calling twice?
                recur_cols = [
                    # TODO: proxy_name is not technically safe,
                    # see test_cte->
                    # test_with_recursive_no_name_currently_buggy.  not
                    # clear what should be done with such a case
                    fallback_label_name or proxy_name
                    for (
                        _,
                        proxy_name,
                        fallback_label_name,
                        c,
                        repeated,
                    ) in (col_source._generate_columns_plus_names(True))
                    if not repeated
                ]

                text += "(%s)" % (
                    ", ".join(
                        self.preparer.format_label_name(
                            ident, anon_map=self.anon_map
                        )
                        for ident in recur_cols
                    )
                )

            assert kwargs.get("subquery", False) is False

            if not self.stack:
                # toplevel, this is a stringify of the
                # cte directly.  just compile the inner
                # the way alias() does.
                return cte.element._compiler_dispatch(
                    self, asfrom=asfrom, **kwargs
                )
            else:
                prefixes = self._generate_prefixes(
                    cte, cte._prefixes, **kwargs
                )
                inner = cte.element._compiler_dispatch(
                    self, asfrom=True, **kwargs
                )

                text += " AS %s\n(%s)" % (prefixes, inner)

            if cte._suffixes:
                text += " " + self._generate_prefixes(
                    cte, cte._suffixes, **kwargs
                )

            self_ctes[cte] = text

    if asfrom:
        if from_linter:
            from_linter.froms[cte._de_clone()] = cte_name

        if not is_new_cte and embedded_in_current_named_cte:
            return self.preparer.format_alias(cte, cte_name)

        if cte_pre_alias_name:
            text = self.preparer.format_alias(cte, cte_pre_alias_name)
            if self.preparer._requires_quotes(cte_name):
                cte_name = self.preparer.quote(cte_name)
            text += self.get_render_as_alias_suffix(cte_name)
            return text  # type: ignore[no-any-return]
        else:
            return self.preparer.format_alias(cte, cte_name)

    return None