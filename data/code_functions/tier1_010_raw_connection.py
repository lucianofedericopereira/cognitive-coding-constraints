# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/engine/base.py (line 3259)
# License: MIT
# Complexity: 1
# Tier   : tier1

def raw_connection(self) -> PoolProxiedConnection:
    """Return a "raw" DBAPI connection from the connection pool.

    The returned object is a proxied version of the DBAPI
    connection object used by the underlying driver in use.
    The object will have all the same behavior as the real DBAPI
    connection, except that its ``close()`` method will result in the
    connection being returned to the pool, rather than being closed
    for real.

    This method provides direct DBAPI connection access for
    special situations when the API provided by
    :class:`_engine.Connection`
    is not needed.   When a :class:`_engine.Connection` object is already
    present, the DBAPI connection is available using
    the :attr:`_engine.Connection.connection` accessor.

    .. seealso::

        :ref:`dbapi_connections`

    """
    return self.pool.connect()