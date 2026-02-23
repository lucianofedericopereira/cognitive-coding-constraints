# Source : https://github.com/pydantic/pydantic/blob/main/pydantic/_internal/_generate_schema.py (line 2225)
# License: MIT
# Complexity: 18
# Tier   : tier3

def _apply_single_annotation(
    self,
    schema: core_schema.CoreSchema,
    metadata: Any,
    check_unsupported_field_info_attributes: bool = True,
) -> core_schema.CoreSchema:
    FieldInfo = import_cached_field_info()

    if isinstance(metadata, FieldInfo):
        if (
            check_unsupported_field_info_attributes
            # HACK: we don't want to emit the warning for `FieldInfo` subclasses, because FastAPI does weird manipulations
            # with its subclasses and their annotations:
            and type(metadata) is FieldInfo
        ):
            for attr, value in (unsupported_attributes := self._get_unsupported_field_info_attributes(metadata)):
                warnings.warn(
                    f'The {attr!r} attribute with value {value!r} was provided to the `Field()` function, '
                    f'which has no effect in the context it was used. {attr!r} is field-specific metadata, '
                    'and can only be attached to a model field using `Annotated` metadata or by assignment. '
                    'This may have happened because an `Annotated` type alias using the `type` statement was '
                    'used, or if the `Field()` function was attached to a single member of a union type.',
                    category=UnsupportedFieldAttributeWarning,
                )

            if (
                metadata.default_factory_takes_validated_data
                and self.model_type_stack.get() is None
                and 'defaut_factory' not in unsupported_attributes
            ):
                warnings.warn(
                    "A 'default_factory' taking validated data as an argument was provided to the `Field()` function, "
                    'but no validated data is available in the context it was used.',
                    category=UnsupportedFieldAttributeWarning,
                )

        for field_metadata in metadata.metadata:
            schema = self._apply_single_annotation(schema, field_metadata)

        if metadata.discriminator is not None:
            schema = self._apply_discriminator_to_union(schema, metadata.discriminator)
        return schema

    if schema['type'] == 'nullable':
        # for nullable schemas, metadata is automatically applied to the inner schema
        inner = schema.get('schema', core_schema.any_schema())
        inner = self._apply_single_annotation(inner, metadata)
        if inner:
            schema['schema'] = inner
        return schema

    original_schema = schema
    ref = schema.get('ref')
    if ref is not None:
        schema = schema.copy()
        new_ref = ref + f'_{repr(metadata)}'
        if (existing := self.defs.get_schema_from_ref(new_ref)) is not None:
            return existing
        schema['ref'] = new_ref  # pyright: ignore[reportGeneralTypeIssues]
    elif schema['type'] == 'definition-ref':
        ref = schema['schema_ref']
        if (referenced_schema := self.defs.get_schema_from_ref(ref)) is not None:
            schema = referenced_schema.copy()
            new_ref = ref + f'_{repr(metadata)}'
            if (existing := self.defs.get_schema_from_ref(new_ref)) is not None:
                return existing
            schema['ref'] = new_ref  # pyright: ignore[reportGeneralTypeIssues]

    maybe_updated_schema = _known_annotated_metadata.apply_known_metadata(metadata, schema)

    if maybe_updated_schema is not None:
        return maybe_updated_schema
    return original_schema