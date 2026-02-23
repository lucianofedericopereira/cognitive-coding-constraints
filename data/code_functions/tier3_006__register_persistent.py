# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/orm/session.py (line 3396)
# License: MIT
# Complexity: 18
# Tier   : tier3

def _register_persistent(self, states: Set[InstanceState[Any]]) -> None:
    """Register all persistent objects from a flush.

    This is used both for pending objects moving to the persistent
    state as well as already persistent objects.

    """

    pending_to_persistent = self.dispatch.pending_to_persistent or None
    for state in states:
        mapper = _state_mapper(state)

        # prevent against last minute dereferences of the object
        obj = state.obj()
        if obj is not None:
            instance_key = mapper._identity_key_from_state(state)

            if (
                _none_set.intersection(instance_key[1])
                and not mapper.allow_partial_pks
                or _none_set.issuperset(instance_key[1])
            ):
                raise exc.FlushError(
                    "Instance %s has a NULL identity key.  If this is an "
                    "auto-generated value, check that the database table "
                    "allows generation of new primary key values, and "
                    "that the mapped Column object is configured to "
                    "expect these generated values.  Ensure also that "
                    "this flush() is not occurring at an inappropriate "
                    "time, such as within a load() event."
                    % state_str(state)
                )

            if state.key is None:
                state.key = instance_key
            elif state.key != instance_key:
                # primary key switch. use safe_discard() in case another
                # state has already replaced this one in the identity
                # map (see test/orm/test_naturalpks.py ReversePKsTest)
                self.identity_map.safe_discard(state)
                trans = self._transaction
                assert trans is not None
                if state in trans._key_switches:
                    orig_key = trans._key_switches[state][0]
                else:
                    orig_key = state.key
                trans._key_switches[state] = (
                    orig_key,
                    instance_key,
                )
                state.key = instance_key

            # there can be an existing state in the identity map
            # that is replaced when the primary keys of two instances
            # are swapped; see test/orm/test_naturalpks.py -> test_reverse
            old = self.identity_map.replace(state)
            if (
                old is not None
                and mapper._identity_key_from_state(old) == instance_key
                and old.obj() is not None
            ):
                util.warn(
                    "Identity map already had an identity for %s, "
                    "replacing it with newly flushed object.   Are there "
                    "load operations occurring inside of an event handler "
                    "within the flush?" % (instance_key,)
                )
            state._orphaned_outside_of_session = False

    statelib.InstanceState._commit_all_states(
        ((state, state.dict) for state in states), self.identity_map
    )

    self._register_altered(states)

    if pending_to_persistent is not None:
        for state in states.intersection(self._new):
            pending_to_persistent(self, state)

    # remove from new last, might be the last strong ref
    for state in set(states).intersection(self._new):
        self._new.pop(state)