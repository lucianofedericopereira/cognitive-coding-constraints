# Source : https://github.com/pydantic/pydantic/blob/main/pydantic/_internal/_generate_schema.py (line 395)
# License: MIT
# Complexity: 11
# Tier   : tier3

def _enum_schema(self, enum_type: type[Enum]) -> CoreSchema:
    cases: list[Any] = list(enum_type.__members__.values())

    enum_ref = get_type_ref(enum_type)
    description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
    if (
        description == 'An enumeration.'
    ):  # This is the default value provided by enum.EnumMeta.__new__; don't use it
        description = None
    js_updates = {'title': enum_type.__name__, 'description': description}
    js_updates = {k: v for k, v in js_updates.items() if v is not None}

    sub_type: Literal['str', 'int', 'float'] | None = None
    if issubclass(enum_type, int):
        sub_type = 'int'
        value_ser_type: core_schema.SerSchema = core_schema.simple_ser_schema('int')
    elif issubclass(enum_type, str):
        # this handles `StrEnum` (3.11 only), and also `Foobar(str, Enum)`
        sub_type = 'str'
        value_ser_type = core_schema.simple_ser_schema('str')
    elif issubclass(enum_type, float):
        sub_type = 'float'
        value_ser_type = core_schema.simple_ser_schema('float')
    else:
        # TODO this is an ugly hack, how do we trigger an Any schema for serialization?
        value_ser_type = core_schema.plain_serializer_function_ser_schema(lambda x: x)

    if cases:

        def get_json_schema(schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            json_schema = handler(schema)
            original_schema = handler.resolve_ref_schema(json_schema)
            original_schema.update(js_updates)
            return json_schema

        # we don't want to add the missing to the schema if it's the default one
        default_missing = getattr(enum_type._missing_, '__func__', None) is Enum._missing_.__func__  # pyright: ignore[reportFunctionMemberAccess]
        enum_schema = core_schema.enum_schema(
            enum_type,
            cases,
            sub_type=sub_type,
            missing=None if default_missing else enum_type._missing_,
            ref=enum_ref,
            metadata={'pydantic_js_functions': [get_json_schema]},
        )

        if self._config_wrapper.use_enum_values:
            enum_schema = core_schema.no_info_after_validator_function(
                attrgetter('value'), enum_schema, serialization=value_ser_type
            )

        return enum_schema

    else:

        def get_json_schema_no_cases(_, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            json_schema = handler(core_schema.enum_schema(enum_type, cases, sub_type=sub_type, ref=enum_ref))
            original_schema = handler.resolve_ref_schema(json_schema)
            original_schema.update(js_updates)
            return json_schema

        # Use an isinstance check for enums with no cases.
        # The most important use case for this is creating TypeVar bounds for generics that should
        # be restricted to enums. This is more consistent than it might seem at first, since you can only
        # subclass enum.Enum (or subclasses of enum.Enum) if all parent classes have no cases.
        # We use the get_json_schema function when an Enum subclass has been declared with no cases
        # so that we can still generate a valid json schema.
        return core_schema.is_instance_schema(
            enum_type,
            metadata={'pydantic_js_functions': [get_json_schema_no_cases]},
        )