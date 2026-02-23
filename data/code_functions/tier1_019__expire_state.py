# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/orm/session.py (line 3329)
# License: MIT
# Complexity: 3
# Tier   : tier1

def _expire_state(
    self,
    state: InstanceState[Any],
    attribute_names: Optional[Iterable[str]],
) -> None:
    self._validate_persistent(state)
    if attribute_names:
        state._expire_attributes(state.dict, attribute_names)
    else:
        # pre-fetch the full cascade since the expire is going to
        # remove associations
        cascaded = list(
            state.manager.mapper.cascade_iterator("refresh-expire", state)
        )
        self._conditional_expire(state)
        for o, m, st_, dct_ in cascaded:
            self._conditional_expire(st_)