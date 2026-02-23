# Source : https://github.com/fastapi/fastapi/blob/master/fastapi/dependencies/utils.py (line 751)
# License: MIT
# Complexity: 20
# Tier   : tier3

def request_params_to_args(
    fields: Sequence[ModelField],
    received_params: Mapping[str, Any] | QueryParams | Headers,
) -> tuple[dict[str, Any], list[Any]]:
    values: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []

    if not fields:
        return values, errors

    first_field = fields[0]
    fields_to_extract = fields
    single_not_embedded_field = False
    default_convert_underscores = True
    if len(fields) == 1 and lenient_issubclass(
        first_field.field_info.annotation, BaseModel
    ):
        fields_to_extract = get_cached_model_fields(first_field.field_info.annotation)
        single_not_embedded_field = True
        # If headers are in a Pydantic model, the way to disable convert_underscores
        # would be with Header(convert_underscores=False) at the Pydantic model level
        default_convert_underscores = getattr(
            first_field.field_info, "convert_underscores", True
        )

    params_to_process: dict[str, Any] = {}

    processed_keys = set()

    for field in fields_to_extract:
        alias = None
        if isinstance(received_params, Headers):
            # Handle fields extracted from a Pydantic Model for a header, each field
            # doesn't have a FieldInfo of type Header with the default convert_underscores=True
            convert_underscores = getattr(
                field.field_info, "convert_underscores", default_convert_underscores
            )
            if convert_underscores:
                alias = get_validation_alias(field)
                if alias == field.name:
                    alias = alias.replace("_", "-")
        value = _get_multidict_value(field, received_params, alias=alias)
        if value is not None:
            params_to_process[get_validation_alias(field)] = value
        processed_keys.add(alias or get_validation_alias(field))

    for key in received_params.keys():
        if key not in processed_keys:
            if hasattr(received_params, "getlist"):
                value = received_params.getlist(key)
                if isinstance(value, list) and (len(value) == 1):
                    params_to_process[key] = value[0]
                else:
                    params_to_process[key] = value
            else:
                params_to_process[key] = received_params.get(key)

    if single_not_embedded_field:
        field_info = first_field.field_info
        assert isinstance(field_info, params.Param), (
            "Params must be subclasses of Param"
        )
        loc: tuple[str, ...] = (field_info.in_.value,)
        v_, errors_ = _validate_value_with_model_field(
            field=first_field, value=params_to_process, values=values, loc=loc
        )
        return {first_field.name: v_}, errors_

    for field in fields:
        value = _get_multidict_value(field, received_params)
        field_info = field.field_info
        assert isinstance(field_info, params.Param), (
            "Params must be subclasses of Param"
        )
        loc = (field_info.in_.value, get_validation_alias(field))
        v_, errors_ = _validate_value_with_model_field(
            field=field, value=value, values=values, loc=loc
        )
        if errors_:
            errors.extend(errors_)
        else:
            values[field.name] = v_
    return values, errors