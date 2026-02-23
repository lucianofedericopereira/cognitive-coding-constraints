# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 2365)
# License: MIT
# Complexity: 7
# Tier   : tier2

def get(lastrowid, parameters):
    """given cursor.lastrowid value and the parameters used for INSERT,
    return a "row" that represents the primary key, either by
    using the "lastrowid" or by extracting values from the parameters
    that were sent along with the INSERT.

    """
    if lastrowid_processor is not None:
        lastrowid = lastrowid_processor(lastrowid)

    if lastrowid is None:
        return row_fn(getter(parameters) for getter, col in getters)
    else:
        return row_fn(
            (
                (
                    autoinc_getter(lastrowid, parameters)
                    if autoinc_getter is not None
                    else lastrowid
                )
                if col is autoinc_col
                else getter(parameters)
            )
            for getter, col in getters
        )