# Source : https://github.com/pydantic/pydantic/blob/main/pydantic/_internal/_generate_schema.py (line 1955)
# License: MIT
# Complexity: 16
# Tier   : tier3

def _arguments_schema(
    self, function: ValidateCallSupportedTypes, parameters_callback: ParametersCallback | None = None
) -> core_schema.ArgumentsSchema:
    """Generate schema for a Signature."""
    mode_lookup: dict[_ParameterKind, Literal['positional_only', 'positional_or_keyword', 'keyword_only']] = {
        Parameter.POSITIONAL_ONLY: 'positional_only',
        Parameter.POSITIONAL_OR_KEYWORD: 'positional_or_keyword',
        Parameter.KEYWORD_ONLY: 'keyword_only',
    }

    sig = _typing_extra.signature_no_eval(function)
    globalns, localns = self._types_namespace
    type_hints = _typing_extra.get_function_type_hints(function, globalns=globalns, localns=localns)

    arguments_list: list[core_schema.ArgumentsParameter] = []
    var_args_schema: core_schema.CoreSchema | None = None
    var_kwargs_schema: core_schema.CoreSchema | None = None
    var_kwargs_mode: core_schema.VarKwargsMode | None = None

    for i, (name, p) in enumerate(sig.parameters.items()):
        if p.annotation is sig.empty:
            annotation = typing.cast(Any, Any)
        else:
            annotation = type_hints[name]

        if parameters_callback is not None:
            result = parameters_callback(i, name, annotation)
            if result == 'skip':
                continue

        parameter_mode = mode_lookup.get(p.kind)
        if parameter_mode is not None:
            arg_schema = self._generate_parameter_schema(
                name, annotation, AnnotationSource.FUNCTION, p.default, parameter_mode
            )
            arguments_list.append(arg_schema)
        elif p.kind == Parameter.VAR_POSITIONAL:
            var_args_schema = self.generate_schema(annotation)
        else:
            assert p.kind == Parameter.VAR_KEYWORD, p.kind

            unpack_type = _typing_extra.unpack_type(annotation)
            if unpack_type is not None:
                origin = get_origin(unpack_type) or unpack_type
                if not is_typeddict(origin):
                    raise PydanticUserError(
                        f'Expected a `TypedDict` class inside `Unpack[...]`, got {unpack_type!r}',
                        code='unpack-typed-dict',
                    )
                non_pos_only_param_names = {
                    name for name, p in sig.parameters.items() if p.kind != Parameter.POSITIONAL_ONLY
                }
                overlapping_params = non_pos_only_param_names.intersection(origin.__annotations__)
                if overlapping_params:
                    raise PydanticUserError(
                        f'Typed dictionary {origin.__name__!r} overlaps with parameter'
                        f'{"s" if len(overlapping_params) >= 2 else ""} '
                        f'{", ".join(repr(p) for p in sorted(overlapping_params))}',
                        code='overlapping-unpack-typed-dict',
                    )

                var_kwargs_mode = 'unpacked-typed-dict'
                var_kwargs_schema = self._typed_dict_schema(unpack_type, get_origin(unpack_type))
            else:
                var_kwargs_mode = 'uniform'
                var_kwargs_schema = self.generate_schema(annotation)

    return core_schema.arguments_schema(
        arguments_list,
        var_args_schema=var_args_schema,
        var_kwargs_mode=var_kwargs_mode,
        var_kwargs_schema=var_kwargs_schema,
        validate_by_name=self._config_wrapper.validate_by_name,
    )