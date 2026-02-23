# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/python.py (line 1584)
# License: MIT
# Complexity: 7
# Tier   : tier2

def __init__(
    self,
    name: str,
    parent,
    config: Config | None = None,
    callspec: CallSpec2 | None = None,
    callobj=NOTSET,
    keywords: Mapping[str, Any] | None = None,
    session: Session | None = None,
    fixtureinfo: FuncFixtureInfo | None = None,
    originalname: str | None = None,
) -> None:
    super().__init__(name, parent, config=config, session=session)

    if callobj is not NOTSET:
        self._obj = callobj
        self._instance = getattr(callobj, "__self__", None)

    #: Original function name, without any decorations (for example
    #: parametrization adds a ``"[...]"`` suffix to function names), used to access
    #: the underlying function object from ``parent`` (in case ``callobj`` is not given
    #: explicitly).
    #:
    #: .. versionadded:: 3.0
    self.originalname = originalname or name

    # Note: when FunctionDefinition is introduced, we should change ``originalname``
    # to a readonly property that returns FunctionDefinition.name.

    self.own_markers.extend(get_unpacked_marks(self.obj))
    if callspec:
        self.callspec = callspec
        self.own_markers.extend(callspec.marks)

    # todo: this is a hell of a hack
    # https://github.com/pytest-dev/pytest/issues/4569
    # Note: the order of the updates is important here; indicates what
    # takes priority (ctor argument over function attributes over markers).
    # Take own_markers only; NodeKeywords handles parent traversal on its own.
    self.keywords.update((mark.name, mark) for mark in self.own_markers)
    self.keywords.update(self.obj.__dict__)
    if keywords:
        self.keywords.update(keywords)

    if fixtureinfo is None:
        fm = self.session._fixturemanager
        fixtureinfo = fm.getfixtureinfo(self, self.obj, self.cls)
    self._fixtureinfo: FuncFixtureInfo = fixtureinfo
    self.fixturenames = fixtureinfo.names_closure
    self._initrequest()