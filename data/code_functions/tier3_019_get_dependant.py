# Source : https://github.com/fastapi/fastapi/blob/master/fastapi/dependencies/utils.py (line 254)
# License: MIT
# Complexity: 17
# Tier   : tier3

def get_dependant(
    *,
    path: str,
    call: Callable[..., Any],
    name: str | None = None,
    own_oauth_scopes: list[str] | None = None,
    parent_oauth_scopes: list[str] | None = None,
    use_cache: bool = True,
    scope: Literal["function", "request"] | None = None,
) -> Dependant:
    dependant = Dependant(
        call=call,
        name=name,
        path=path,
        use_cache=use_cache,
        scope=scope,
        own_oauth_scopes=own_oauth_scopes,
        parent_oauth_scopes=parent_oauth_scopes,
    )
    current_scopes = (parent_oauth_scopes or []) + (own_oauth_scopes or [])
    path_param_names = get_path_param_names(path)
    endpoint_signature = get_typed_signature(call)
    signature_params = endpoint_signature.parameters
    for param_name, param in signature_params.items():
        is_path_param = param_name in path_param_names
        param_details = analyze_param(
            param_name=param_name,
            annotation=param.annotation,
            value=param.default,
            is_path_param=is_path_param,
        )
        if param_details.depends is not None:
            assert param_details.depends.dependency
            if (
                (dependant.is_gen_callable or dependant.is_async_gen_callable)
                and dependant.computed_scope == "request"
                and param_details.depends.scope == "function"
            ):
                assert dependant.call
                raise DependencyScopeError(
                    f'The dependency "{dependant.call.__name__}" has a scope of '
                    '"request", it cannot depend on dependencies with scope "function".'
                )
            sub_own_oauth_scopes: list[str] = []
            if isinstance(param_details.depends, params.Security):
                if param_details.depends.scopes:
                    sub_own_oauth_scopes = list(param_details.depends.scopes)
            sub_dependant = get_dependant(
                path=path,
                call=param_details.depends.dependency,
                name=param_name,
                own_oauth_scopes=sub_own_oauth_scopes,
                parent_oauth_scopes=current_scopes,
                use_cache=param_details.depends.use_cache,
                scope=param_details.depends.scope,
            )
            dependant.dependencies.append(sub_dependant)
            continue
        if add_non_field_param_to_dependency(
            param_name=param_name,
            type_annotation=param_details.type_annotation,
            dependant=dependant,
        ):
            assert param_details.field is None, (
                f"Cannot specify multiple FastAPI annotations for {param_name!r}"
            )
            continue
        assert param_details.field is not None
        if isinstance(param_details.field.field_info, params.Body):
            dependant.body_params.append(param_details.field)
        else:
            add_param_to_fields(field=param_details.field, dependant=dependant)
    return dependant