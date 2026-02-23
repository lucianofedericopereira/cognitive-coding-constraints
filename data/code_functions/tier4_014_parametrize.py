# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/python.py (line 1207)
# License: MIT
# Complexity: 24
# Tier   : tier4

def parametrize(
    self,
    argnames: str | Sequence[str],
    argvalues: Iterable[ParameterSet | Sequence[object] | object],
    indirect: bool | Sequence[str] = False,
    ids: Iterable[object | None] | Callable[[Any], object | None] | None = None,
    scope: _ScopeName | None = None,
    *,
    _param_mark: Mark | None = None,
) -> None:
    """Add new invocations to the underlying test function using the list
    of argvalues for the given argnames. Parametrization is performed
    during the collection phase. If you need to setup expensive resources
    see about setting ``indirect`` to do it at test setup time instead.

    Can be called multiple times per test function (but only on different
    argument names), in which case each call parametrizes all previous
    parametrizations, e.g.

    ::

        unparametrized:         t
        parametrize ["x", "y"]: t[x], t[y]
        parametrize [1, 2]:     t[x-1], t[x-2], t[y-1], t[y-2]

    :param argnames:
        A comma-separated string denoting one or more argument names, or
        a list/tuple of argument strings.

    :param argvalues:
        The list of argvalues determines how often a test is invoked with
        different argument values.

        If only one argname was specified argvalues is a list of values.
        If N argnames were specified, argvalues must be a list of
        N-tuples, where each tuple-element specifies a value for its
        respective argname.

        .. versionchanged:: 9.1

            Passing a non-:class:`~collections.abc.Collection` iterable
            (such as a generator or iterator) is deprecated. See
            :ref:`parametrize-iterators` for details.

    :param indirect:
        A list of arguments' names (subset of argnames) or a boolean.
        If True the list contains all names from the argnames. Each
        argvalue corresponding to an argname in this list will
        be passed as request.param to its respective argname fixture
        function so that it can perform more expensive setups during the
        setup phase of a test rather than at collection time.

    :param ids:
        Sequence of (or generator for) ids for ``argvalues``,
        or a callable to return part of the id for each argvalue.

        With sequences (and generators like ``itertools.count()``) the
        returned ids should be of type ``string``, ``int``, ``float``,
        ``bool``, or ``None``.
        They are mapped to the corresponding index in ``argvalues``.
        ``None`` means to use the auto-generated id.

        .. versionadded:: 8.4
            :ref:`hidden-param` means to hide the parameter set
            from the test name. Can only be used at most 1 time, as
            test names need to be unique.

        If it is a callable it will be called for each entry in
        ``argvalues``, and the return value is used as part of the
        auto-generated id for the whole set (where parts are joined with
        dashes ("-")).
        This is useful to provide more specific ids for certain items, e.g.
        dates.  Returning ``None`` will use an auto-generated id.

        If no ids are provided they will be generated automatically from
        the argvalues.

    :param scope:
        If specified it denotes the scope of the parameters.
        The scope is used for grouping tests by parameter instances.
        It will also override any fixture-function defined scope, allowing
        to set a dynamic scope using test context or configuration.
    """
    nodeid = self.definition.nodeid

    argnames, parametersets = ParameterSet._for_parametrize(
        argnames,
        argvalues,
        self.function,
        self.config,
        nodeid=self.definition.nodeid,
    )
    del argvalues

    if "request" in argnames:
        fail(
            f"{nodeid}: 'request' is a reserved name and cannot be used in @pytest.mark.parametrize",
            pytrace=False,
        )

    if scope is not None:
        scope_ = Scope.from_user(
            scope, descr=f"parametrize() call in {self.function.__name__}"
        )
    else:
        scope_ = _find_parametrized_scope(argnames, self._arg2fixturedefs, indirect)

    self._validate_if_using_arg_names(argnames, indirect)

    # Use any already (possibly) generated ids with parametrize Marks.
    if _param_mark and _param_mark._param_ids_from:
        generated_ids = _param_mark._param_ids_from._param_ids_generated
        if generated_ids is not None:
            ids = generated_ids

    ids = self._resolve_parameter_set_ids(
        argnames, ids, parametersets, nodeid=self.definition.nodeid
    )

    # Store used (possibly generated) ids with parametrize Marks.
    if _param_mark and _param_mark._param_ids_from and generated_ids is None:
        object.__setattr__(_param_mark._param_ids_from, "_param_ids_generated", ids)

    # Calculate directness.
    arg_directness = _resolve_args_directness(
        argnames, indirect, self.definition.nodeid
    )
    self._params_directness.update(arg_directness)

    # Add direct parametrizations as fixturedefs to arg2fixturedefs by
    # registering artificial "pseudo" FixtureDef's such that later at test
    # setup time we can rely on FixtureDefs to exist for all argnames.
    node = None
    # For scopes higher than function, a "pseudo" FixtureDef might have
    # already been created for the scope. We thus store and cache the
    # FixtureDef on the node related to the scope.
    if scope_ is Scope.Function:
        name2pseudofixturedef = None
    else:
        collector = self.definition.parent
        assert collector is not None
        node = get_scope_node(collector, scope_)
        if node is None:
            # If used class scope and there is no class, use module-level
            # collector (for now).
            if scope_ is Scope.Class:
                assert isinstance(collector, Module)
                node = collector
            # If used package scope and there is no package, use session
            # (for now).
            elif scope_ is Scope.Package:
                node = collector.session
            else:
                assert False, f"Unhandled missing scope: {scope}"
        default: dict[str, FixtureDef[Any]] = {}
        name2pseudofixturedef = node.stash.setdefault(
            name2pseudofixturedef_key, default
        )
    for argname in argnames:
        if arg_directness[argname] == "indirect":
            continue
        if name2pseudofixturedef is not None and argname in name2pseudofixturedef:
            fixturedef = name2pseudofixturedef[argname]
        else:
            fixturedef = FixtureDef(
                config=self.config,
                baseid="",
                argname=argname,
                func=get_direct_param_fixture_func,
                scope=scope_,
                params=None,
                ids=None,
                _ispytest=True,
            )
            if name2pseudofixturedef is not None:
                name2pseudofixturedef[argname] = fixturedef
        self._arg2fixturedefs[argname] = [fixturedef]

    # Create the new calls: if we are parametrize() multiple times (by applying the decorator
    # more than once) then we accumulate those calls generating the cartesian product
    # of all calls.
    newcalls = []
    for callspec in self._calls or [CallSpec2()]:
        for param_index, (param_id, param_set) in enumerate(
            zip(ids, parametersets, strict=True)
        ):
            newcallspec = callspec.setmulti(
                argnames=argnames,
                valset=param_set.values,
                id=param_id,
                marks=param_set.marks,
                scope=scope_,
                param_index=param_index,
                nodeid=nodeid,
            )
            newcalls.append(newcallspec)
    self._calls = newcalls