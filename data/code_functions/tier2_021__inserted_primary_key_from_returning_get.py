# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 2395)
# License: MIT
# Complexity: 9
# Tier   : tier2

def _inserted_primary_key_from_returning_getter(self):
    result = util.preloaded.engine_result

    assert self.compile_state is not None
    statement = self.compile_state.statement

    if TYPE_CHECKING:
        assert isinstance(statement, Insert)

    param_key_getter = self._within_exec_param_key_getter
    table = statement.table

    returning = self.implicit_returning
    assert returning is not None
    ret = {col: idx for idx, col in enumerate(returning)}

    getters = cast(
        "List[Tuple[Callable[[Any], Any], bool]]",
        [
            (
                (operator.itemgetter(ret[col]), True)
                if col in ret
                else (
                    operator.methodcaller(
                        "get", param_key_getter(col), None
                    ),
                    False,
                )
            )
            for col in table.primary_key
        ],
    )

    row_fn = result.result_tuple([col.key for col in table.primary_key])

    def get(row, parameters):
        return row_fn(
            getter(row) if use_row else getter(parameters)
            for getter, use_row in getters
        )

    return get