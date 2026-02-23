# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 1428)
# License: MIT
# Complexity: 30
# Tier   : tier4

def __init__(
    self,
    dialect: Dialect,
    statement: Optional[ClauseElement],
    cache_key: Optional[CacheKey] = None,
    column_keys: Optional[Sequence[str]] = None,
    for_executemany: bool = False,
    linting: Linting = NO_LINTING,
    _supporting_against: Optional[SQLCompiler] = None,
    **kwargs: Any,
):
    """Construct a new :class:`.SQLCompiler` object.

    :param dialect: :class:`.Dialect` to be used

    :param statement: :class:`_expression.ClauseElement` to be compiled

    :param column_keys:  a list of column names to be compiled into an
     INSERT or UPDATE statement.

    :param for_executemany: whether INSERT / UPDATE statements should
     expect that they are to be invoked in an "executemany" style,
     which may impact how the statement will be expected to return the
     values of defaults and autoincrement / sequences and similar.
     Depending on the backend and driver in use, support for retrieving
     these values may be disabled which means SQL expressions may
     be rendered inline, RETURNING may not be rendered, etc.

    :param kwargs: additional keyword arguments to be consumed by the
     superclass.

    """
    self.column_keys = column_keys

    self.cache_key = cache_key

    if cache_key:
        cksm = {b.key: b for b in cache_key[1]}
        ckbm = {b: [b] for b in cache_key[1]}
        self._cache_key_bind_match = (ckbm, cksm)

    # compile INSERT/UPDATE defaults/sequences to expect executemany
    # style execution, which may mean no pre-execute of defaults,
    # or no RETURNING
    self.for_executemany = for_executemany

    self.linting = linting

    # a dictionary of bind parameter keys to BindParameter
    # instances.
    self.binds = {}

    # a dictionary of BindParameter instances to "compiled" names
    # that are actually present in the generated SQL
    self.bind_names = util.column_dict()

    # stack which keeps track of nested SELECT statements
    self.stack = []

    self._result_columns = []

    # true if the paramstyle is positional
    self.positional = dialect.positional
    if self.positional:
        self._numeric_binds = nb = dialect.paramstyle.startswith("numeric")
        if nb:
            self._numeric_binds_identifier_char = (
                "$" if dialect.paramstyle == "numeric_dollar" else ":"
            )

        self.compilation_bindtemplate = _pyformat_template
    else:
        self.compilation_bindtemplate = BIND_TEMPLATES[dialect.paramstyle]

    self.ctes = None

    self.label_length = (
        dialect.label_length or dialect.max_identifier_length
    )

    # a map which tracks "anonymous" identifiers that are created on
    # the fly here
    self.anon_map = prefix_anon_map()

    # a map which tracks "truncated" names based on
    # dialect.label_length or dialect.max_identifier_length
    self.truncated_names: Dict[Tuple[str, str], str] = {}
    self._truncated_counters: Dict[str, int] = {}
    if not cache_key:
        self._collect_params = True
        self._collected_params = util.EMPTY_DICT
    else:
        self._collect_params = False  # type: ignore[misc]

    Compiled.__init__(self, dialect, statement, **kwargs)

    if self.isinsert or self.isupdate or self.isdelete:
        if TYPE_CHECKING:
            assert isinstance(statement, UpdateBase)

        if self.isinsert or self.isupdate:
            if TYPE_CHECKING:
                assert isinstance(statement, ValuesBase)
            if statement._inline:
                self.inline = True
            elif self.for_executemany and (
                not self.isinsert
                or (
                    self.dialect.insert_executemany_returning
                    and statement._return_defaults
                )
            ):
                self.inline = True

    self.bindtemplate = BIND_TEMPLATES[dialect.paramstyle]

    if _supporting_against:
        self.__dict__.update(
            {
                k: v
                for k, v in _supporting_against.__dict__.items()
                if k
                not in {
                    "state",
                    "dialect",
                    "preparer",
                    "positional",
                    "_numeric_binds",
                    "compilation_bindtemplate",
                    "bindtemplate",
                }
            }
        )

    if self.state is CompilerState.STRING_APPLIED:
        if self.positional:
            if self._numeric_binds:
                self._process_numeric()
            else:
                self._process_positional()

        if self._render_postcompile:
            parameters = self.construct_params(
                escape_names=False,
                _no_postcompile=True,
            )

            self._process_parameters_for_postcompile(
                parameters, _populate_self=True
            )