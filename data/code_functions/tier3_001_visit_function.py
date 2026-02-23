# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 3099)
# License: MIT
# Complexity: 12
# Tier   : tier3

def visit_function(
    self,
    func: Function[Any],
    add_to_result_map: Optional[_ResultMapAppender] = None,
    **kwargs: Any,
) -> str:
    if self._collect_params:
        self._add_to_params(func)
    if add_to_result_map is not None:
        add_to_result_map(func.name, func.name, (func.name,), func.type)

    disp = getattr(self, "visit_%s_func" % func.name.lower(), None)

    text: str

    if disp:
        text = disp(func, **kwargs)
    else:
        name = FUNCTIONS.get(func._deannotate().__class__, None)
        if name:
            if func._has_args:
                name += "%(expr)s"
        else:
            name = func.name
            name = (
                self.preparer.quote(name)
                if self.preparer._requires_quotes_illegal_chars(name)
                or isinstance(name, elements.quoted_name)
                else name
            )
            name = name + "%(expr)s"
        text = ".".join(
            [
                (
                    self.preparer.quote(tok)
                    if self.preparer._requires_quotes_illegal_chars(tok)
                    or isinstance(name, elements.quoted_name)
                    else tok
                )
                for tok in func.packagenames
            ]
            + [name]
        ) % {"expr": self.function_argspec(func, **kwargs)}

    if func._with_ordinality:
        text += " WITH ORDINALITY"
    return text