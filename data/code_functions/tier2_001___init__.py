# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/engine/base.py (line 134)
# License: MIT
# Complexity: 8
# Tier   : tier2

def __init__(
    self,
    engine: Engine,
    connection: Optional[PoolProxiedConnection] = None,
    _has_events: Optional[bool] = None,
    _allow_revalidate: bool = True,
    _allow_autobegin: bool = True,
):
    """Construct a new Connection."""
    self.engine = engine
    self.dialect = dialect = engine.dialect

    if connection is None:
        try:
            self._dbapi_connection = engine.raw_connection()
        except dialect.loaded_dbapi.Error as err:
            Connection._handle_dbapi_exception_noconnection(
                err, dialect, engine
            )
            raise
    else:
        self._dbapi_connection = connection

    self._transaction = self._nested_transaction = None
    self.__savepoint_seq = 0
    self.__in_begin = False

    self.__can_reconnect = _allow_revalidate
    self._allow_autobegin = _allow_autobegin
    self._echo = self.engine._should_log_info()

    if _has_events is None:
        # if _has_events is sent explicitly as False,
        # then don't join the dispatch of the engine; we don't
        # want to handle any of the engine's events in that case.
        self.dispatch = self.dispatch._join(engine.dispatch)
    self._has_events = _has_events or (
        _has_events is None and engine._has_events
    )

    self._execution_options = engine._execution_options

    if self._has_events or self.engine._has_events:
        self.dispatch.engine_connect(self)