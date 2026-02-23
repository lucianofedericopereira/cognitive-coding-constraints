# Source : https://github.com/pydantic/pydantic/blob/main/pydantic/fields.py (line 577)
# License: MIT
# Complexity: 14
# Tier   : tier3

def merge_field_infos(*field_infos: FieldInfo, **overrides: Any) -> FieldInfo:
    """Merge `FieldInfo` instances keeping only explicitly set attributes.

    Later `FieldInfo` instances override earlier ones.

    Returns:
        FieldInfo: A merged FieldInfo instance.
    """
    if len(field_infos) == 1:
        # No merging necessary, but we still need to make a copy and apply the overrides
        field_info = field_infos[0]._copy()
        field_info._attributes_set.update(overrides)

        default_override = overrides.pop('default', PydanticUndefined)
        if default_override is Ellipsis:
            default_override = PydanticUndefined
        if default_override is not PydanticUndefined:
            field_info.default = default_override

        for k, v in overrides.items():
            setattr(field_info, k, v)
        return field_info  # type: ignore

    merged_field_info_kwargs: dict[str, Any] = {}
    metadata = {}
    for field_info in field_infos:
        attributes_set = field_info._attributes_set.copy()

        try:
            json_schema_extra = attributes_set.pop('json_schema_extra')
            existing_json_schema_extra = merged_field_info_kwargs.get('json_schema_extra')

            if existing_json_schema_extra is None:
                merged_field_info_kwargs['json_schema_extra'] = json_schema_extra
            if isinstance(existing_json_schema_extra, dict):
                if isinstance(json_schema_extra, dict):
                    merged_field_info_kwargs['json_schema_extra'] = {
                        **existing_json_schema_extra,
                        **json_schema_extra,
                    }
                if callable(json_schema_extra):
                    warn(
                        'Composing `dict` and `callable` type `json_schema_extra` is not supported.'
                        'The `callable` type is being ignored.'
                        "If you'd like support for this behavior, please open an issue on pydantic.",
                        PydanticJsonSchemaWarning,
                    )
            elif callable(json_schema_extra):
                # if ever there's a case of a callable, we'll just keep the last json schema extra spec
                merged_field_info_kwargs['json_schema_extra'] = json_schema_extra
        except KeyError:
            pass

        # later FieldInfo instances override everything except json_schema_extra from earlier FieldInfo instances
        merged_field_info_kwargs.update(attributes_set)

        for x in field_info.metadata:
            if not isinstance(x, FieldInfo):
                metadata[type(x)] = x

    merged_field_info_kwargs.update(overrides)
    field_info = FieldInfo(**merged_field_info_kwargs)
    field_info.metadata = list(metadata.values())
    return field_info