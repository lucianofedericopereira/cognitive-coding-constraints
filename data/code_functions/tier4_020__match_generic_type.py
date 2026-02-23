# Source : https://github.com/pydantic/pydantic/blob/main/pydantic/_internal/_generate_schema.py (line 1142)
# License: MIT
# Complexity: 21
# Tier   : tier4

def _match_generic_type(self, obj: Any, origin: Any) -> CoreSchema:  # noqa: C901
    # Need to handle generic dataclasses before looking for the schema properties because attribute accesses
    # on _GenericAlias delegate to the origin type, so lose the information about the concrete parametrization
    # As a result, currently, there is no way to cache the schema for generic dataclasses. This may be possible
    # to resolve by modifying the value returned by `Generic.__class_getitem__`, but that is a dangerous game.
    if dataclasses.is_dataclass(origin):
        return self._dataclass_schema(obj, origin)  # pyright: ignore[reportArgumentType]
    if _typing_extra.is_namedtuple(origin):
        return self._namedtuple_schema(obj, origin)

    schema = self._generate_schema_from_get_schema_method(origin, obj)
    if schema is not None:
        return schema

    if typing_objects.is_typealiastype(origin):
        return self._type_alias_type_schema(obj)
    elif is_union_origin(origin):
        return self._union_schema(obj)
    elif origin in TUPLE_TYPES:
        return self._tuple_schema(obj)
    elif origin in LIST_TYPES:
        return self._list_schema(self._get_first_arg_or_any(obj))
    elif origin in SET_TYPES:
        return self._set_schema(self._get_first_arg_or_any(obj))
    elif origin in FROZEN_SET_TYPES:
        return self._frozenset_schema(self._get_first_arg_or_any(obj))
    elif origin in DICT_TYPES:
        return self._dict_schema(*self._get_first_two_args_or_any(obj))
    elif origin in PATH_TYPES:
        return self._path_schema(origin, self._get_first_arg_or_any(obj))
    elif origin in DEQUE_TYPES:
        return self._deque_schema(self._get_first_arg_or_any(obj))
    elif origin in MAPPING_TYPES:
        return self._mapping_schema(origin, *self._get_first_two_args_or_any(obj))
    elif origin in COUNTER_TYPES:
        return self._mapping_schema(origin, self._get_first_arg_or_any(obj), int)
    elif is_typeddict(origin):
        return self._typed_dict_schema(obj, origin)
    elif origin in TYPE_TYPES:
        return self._subclass_schema(obj)
    elif origin in SEQUENCE_TYPES:
        return self._sequence_schema(self._get_first_arg_or_any(obj))
    elif origin in ITERABLE_TYPES:
        return self._iterable_schema(obj)
    elif origin in PATTERN_TYPES:
        return self._pattern_schema(obj)

    if self._arbitrary_types:
        return self._arbitrary_type_schema(origin)
    return self._unknown_type_schema(obj)