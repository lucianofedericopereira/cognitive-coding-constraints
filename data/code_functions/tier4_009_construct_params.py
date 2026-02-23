# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 1905)
# License: MIT
# Complexity: 33
# Tier   : tier4

def construct_params(
    self,
    params: Optional[_CoreSingleExecuteParams] = None,
    extracted_parameters: Optional[Sequence[BindParameter[Any]]] = None,
    escape_names: bool = True,
    _group_number: Optional[int] = None,
    _check: bool = True,
    _no_postcompile: bool = False,
    _collected_params: _CoreSingleExecuteParams | None = None,
) -> _MutableCoreSingleExecuteParams:
    """return a dictionary of bind parameter keys and values"""
    if _collected_params is not None:
        assert not self._collect_params
    elif self._collect_params:
        _collected_params = self._collected_params

    if _collected_params:
        if not params:
            params = _collected_params
        else:
            params = {**_collected_params, **params}

    if self._render_postcompile and not _no_postcompile:
        assert self._post_compile_expanded_state is not None
        if not params:
            return dict(self._post_compile_expanded_state.parameters)
        else:
            raise exc.InvalidRequestError(
                "can't construct new parameters when render_postcompile "
                "is used; the statement is hard-linked to the original "
                "parameters.  Use construct_expanded_state to generate a "
                "new statement and parameters."
            )

    has_escaped_names = escape_names and bool(self.escaped_bind_names)

    if extracted_parameters:
        # related the bound parameters collected in the original cache key
        # to those collected in the incoming cache key.  They will not have
        # matching names but they will line up positionally in the same
        # way.   The parameters present in self.bind_names may be clones of
        # these original cache key params in the case of DML but the .key
        # will be guaranteed to match.
        if self.cache_key is None:
            raise exc.CompileError(
                "This compiled object has no original cache key; "
                "can't pass extracted_parameters to construct_params"
            )
        else:
            orig_extracted = self.cache_key[1]

        ckbm_tuple = self._cache_key_bind_match
        assert ckbm_tuple is not None
        ckbm, _ = ckbm_tuple
        resolved_extracted = {
            bind: extracted
            for b, extracted in zip(orig_extracted, extracted_parameters)
            for bind in ckbm[b]
        }
    else:
        resolved_extracted = None

    if params:
        pd = {}
        for bindparam, name in self.bind_names.items():
            escaped_name = (
                self.escaped_bind_names.get(name, name)
                if has_escaped_names
                else name
            )

            if bindparam.key in params:
                pd[escaped_name] = params[bindparam.key]
            elif name in params:
                pd[escaped_name] = params[name]

            elif _check and bindparam.required:
                if _group_number:
                    raise exc.InvalidRequestError(
                        "A value is required for bind parameter %r, "
                        "in parameter group %d"
                        % (bindparam.key, _group_number),
                        code="cd3x",
                    )
                else:
                    raise exc.InvalidRequestError(
                        "A value is required for bind parameter %r"
                        % bindparam.key,
                        code="cd3x",
                    )
            else:
                if resolved_extracted:
                    value_param = resolved_extracted.get(
                        bindparam, bindparam
                    )
                else:
                    value_param = bindparam

                if bindparam.callable:
                    pd[escaped_name] = value_param.effective_value
                else:
                    pd[escaped_name] = value_param.value
        return pd
    else:
        pd = {}
        for bindparam, name in self.bind_names.items():
            escaped_name = (
                self.escaped_bind_names.get(name, name)
                if has_escaped_names
                else name
            )

            if _check and bindparam.required:
                if _group_number:
                    raise exc.InvalidRequestError(
                        "A value is required for bind parameter %r, "
                        "in parameter group %d"
                        % (bindparam.key, _group_number),
                        code="cd3x",
                    )
                else:
                    raise exc.InvalidRequestError(
                        "A value is required for bind parameter %r"
                        % bindparam.key,
                        code="cd3x",
                    )

            if resolved_extracted:
                value_param = resolved_extracted.get(bindparam, bindparam)
            else:
                value_param = bindparam

            if bindparam.callable:
                pd[escaped_name] = value_param.effective_value
            else:
                pd[escaped_name] = value_param.value

        return pd