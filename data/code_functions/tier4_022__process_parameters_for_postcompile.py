# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 2096)
# License: MIT
# Complexity: 34
# Tier   : tier4

def _process_parameters_for_postcompile(
    self,
    parameters: _MutableCoreSingleExecuteParams,
    _populate_self: bool = False,
) -> ExpandedState:
    """handle special post compile parameters.

    These include:

    * "expanding" parameters -typically IN tuples that are rendered
      on a per-parameter basis for an otherwise fixed SQL statement string.

    * literal_binds compiled with the literal_execute flag.  Used for
      things like SQL Server "TOP N" where the driver does not accommodate
      N as a bound parameter.

    """

    expanded_parameters = {}
    new_positiontup: Optional[List[str]]

    pre_expanded_string = self._pre_expanded_string
    if pre_expanded_string is None:
        pre_expanded_string = self.string

    if self.positional:
        new_positiontup = []

        pre_expanded_positiontup = self._pre_expanded_positiontup
        if pre_expanded_positiontup is None:
            pre_expanded_positiontup = self.positiontup

    else:
        new_positiontup = pre_expanded_positiontup = None

    processors = self._bind_processors
    single_processors = cast(
        "Mapping[str, _BindProcessorType[Any]]", processors
    )
    tuple_processors = cast(
        "Mapping[str, Sequence[_BindProcessorType[Any]]]", processors
    )

    new_processors: Dict[str, _BindProcessorType[Any]] = {}

    replacement_expressions: Dict[str, Any] = {}
    to_update_sets: Dict[str, Any] = {}

    # notes:
    # *unescaped* parameter names in:
    # self.bind_names, self.binds, self._bind_processors, self.positiontup
    #
    # *escaped* parameter names in:
    # construct_params(), replacement_expressions

    numeric_positiontup: Optional[List[str]] = None

    if self.positional and pre_expanded_positiontup is not None:
        names: Iterable[str] = pre_expanded_positiontup
        if self._numeric_binds:
            numeric_positiontup = []
    else:
        names = self.bind_names.values()

    ebn = self.escaped_bind_names
    for name in names:
        escaped_name = ebn.get(name, name) if ebn else name
        parameter = self.binds[name]

        if parameter in self.literal_execute_params:
            if escaped_name not in replacement_expressions:
                replacement_expressions[escaped_name] = (
                    self.render_literal_bindparam(
                        parameter,
                        render_literal_value=parameters.pop(escaped_name),
                    )
                )
            continue

        if parameter in self.post_compile_params:
            if escaped_name in replacement_expressions:
                to_update = to_update_sets[escaped_name]
                values = None
            else:
                # we are removing the parameter from parameters
                # because it is a list value, which is not expected by
                # TypeEngine objects that would otherwise be asked to
                # process it. the single name is being replaced with
                # individual numbered parameters for each value in the
                # param.
                #
                # note we are also inserting *escaped* parameter names
                # into the given dictionary.   default dialect will
                # use these param names directly as they will not be
                # in the escaped_bind_names dictionary.
                values = parameters.pop(name)

                leep_res = self._literal_execute_expanding_parameter(
                    escaped_name, parameter, values
                )
                (to_update, replacement_expr) = leep_res

                to_update_sets[escaped_name] = to_update
                replacement_expressions[escaped_name] = replacement_expr

            if not parameter.literal_execute:
                parameters.update(to_update)
                if parameter.type._is_tuple_type:
                    assert values is not None
                    new_processors.update(
                        (
                            "%s_%s_%s" % (name, i, j),
                            tuple_processors[name][j - 1],
                        )
                        for i, tuple_element in enumerate(values, 1)
                        for j, _ in enumerate(tuple_element, 1)
                        if name in tuple_processors
                        and tuple_processors[name][j - 1] is not None
                    )
                else:
                    new_processors.update(
                        (key, single_processors[name])
                        for key, _ in to_update
                        if name in single_processors
                    )
                if numeric_positiontup is not None:
                    numeric_positiontup.extend(
                        name for name, _ in to_update
                    )
                elif new_positiontup is not None:
                    # to_update has escaped names, but that's ok since
                    # these are new names, that aren't in the
                    # escaped_bind_names dict.
                    new_positiontup.extend(name for name, _ in to_update)
                expanded_parameters[name] = [
                    expand_key for expand_key, _ in to_update
                ]
        elif new_positiontup is not None:
            new_positiontup.append(name)

    def process_expanding(m):
        key = m.group(1)
        expr = replacement_expressions[key]

        # if POSTCOMPILE included a bind_expression, render that
        # around each element
        if m.group(2):
            tok = m.group(2).split("~~")
            be_left, be_right = tok[1], tok[3]
            expr = ", ".join(
                "%s%s%s" % (be_left, exp, be_right)
                for exp in expr.split(", ")
            )
        return expr

    statement = re.sub(
        self._post_compile_pattern, process_expanding, pre_expanded_string
    )

    if numeric_positiontup is not None:
        assert new_positiontup is not None
        param_pos = {
            key: f"{self._numeric_binds_identifier_char}{num}"
            for num, key in enumerate(
                numeric_positiontup, self.next_numeric_pos
            )
        }
        # Can't use format here since % chars are not escaped.
        statement = self._pyformat_pattern.sub(
            lambda m: param_pos[m.group(1)], statement
        )
        new_positiontup.extend(numeric_positiontup)

    expanded_state = ExpandedState(
        statement,
        parameters,
        new_processors,
        new_positiontup,
        expanded_parameters,
    )

    if _populate_self:
        # this is for the "render_postcompile" flag, which is not
        # otherwise used internally and is for end-user debugging and
        # special use cases.
        self._pre_expanded_string = pre_expanded_string
        self._pre_expanded_positiontup = pre_expanded_positiontup
        self.string = expanded_state.statement
        self.positiontup = (
            list(expanded_state.positiontup or ())
            if self.positional
            else None
        )
        self._post_compile_expanded_state = expanded_state

    return expanded_state