# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 7305)
# License: MIT
# Complexity: 10
# Tier   : tier2

def get_identity_options(self, identity_options: IdentityOptions) -> str:
    text = []
    if identity_options.increment is not None:
        text.append("INCREMENT BY %d" % identity_options.increment)
    if identity_options.start is not None:
        text.append("START WITH %d" % identity_options.start)
    if identity_options.minvalue is not None:
        text.append("MINVALUE %d" % identity_options.minvalue)
    if identity_options.maxvalue is not None:
        text.append("MAXVALUE %d" % identity_options.maxvalue)
    if identity_options.nominvalue is not None:
        text.append("NO MINVALUE")
    if identity_options.nomaxvalue is not None:
        text.append("NO MAXVALUE")
    if identity_options.cache is not None:
        text.append("CACHE %d" % identity_options.cache)
    if identity_options.cycle is not None:
        text.append("CYCLE" if identity_options.cycle else "NO CYCLE")
    return " ".join(text)