# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 889)
# License: MIT
# Complexity: 8
# Tier   : tier2

def __init__(
    self,
    dialect: Dialect,
    statement: Optional[ClauseElement],
    schema_translate_map: Optional[SchemaTranslateMapType] = None,
    render_schema_translate: bool = False,
    compile_kwargs: Mapping[str, Any] = util.immutabledict(),
):
    """Construct a new :class:`.Compiled` object.

    :param dialect: :class:`.Dialect` to compile against.

    :param statement: :class:`_expression.ClauseElement` to be compiled.

    :param schema_translate_map: dictionary of schema names to be
     translated when forming the resultant SQL

     .. seealso::

        :ref:`schema_translating`

    :param compile_kwargs: additional kwargs that will be
     passed to the initial call to :meth:`.Compiled.process`.


    """
    self.dialect = dialect
    self.preparer = self.dialect.identifier_preparer
    if schema_translate_map:
        self.schema_translate_map = schema_translate_map
        self.preparer = self.preparer._with_schema_translate(
            schema_translate_map
        )

    if statement is not None:
        self.state = CompilerState.COMPILING
        self.statement = statement
        self.can_execute = statement.supports_execution
        self._annotations = statement._annotations
        if self.can_execute:
            if TYPE_CHECKING:
                assert isinstance(statement, Executable)
            self.execution_options = statement._execution_options
        self.string = self.process(self.statement, **compile_kwargs)

        if render_schema_translate:
            assert schema_translate_map is not None
            self.string = self.preparer._render_schema_translates(
                self.string, schema_translate_map
            )

        self.state = CompilerState.STRING_APPLIED
    else:
        self.state = CompilerState.NO_STATEMENT

    self._gen_time = perf_counter()