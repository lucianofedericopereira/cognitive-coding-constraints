# Source : https://github.com/fastapi/fastapi/blob/master/fastapi/routing.py (line 572)
# License: MIT
# Complexity: 23
# Tier   : tier4

def __init__(
    self,
    path: str,
    endpoint: Callable[..., Any],
    *,
    response_model: Any = Default(None),
    status_code: int | None = None,
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[params.Depends] | None = None,
    summary: str | None = None,
    description: str | None = None,
    response_description: str = "Successful Response",
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: bool | None = None,
    name: str | None = None,
    methods: set[str] | list[str] | None = None,
    operation_id: str | None = None,
    response_model_include: IncEx | None = None,
    response_model_exclude: IncEx | None = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    dependency_overrides_provider: Any | None = None,
    callbacks: list[BaseRoute] | None = None,
    openapi_extra: dict[str, Any] | None = None,
    generate_unique_id_function: Callable[["APIRoute"], str]
    | DefaultPlaceholder = Default(generate_unique_id),
) -> None:
    self.path = path
    self.endpoint = endpoint
    if isinstance(response_model, DefaultPlaceholder):
        return_annotation = get_typed_return_annotation(endpoint)
        if lenient_issubclass(return_annotation, Response):
            response_model = None
        else:
            response_model = return_annotation
    self.response_model = response_model
    self.summary = summary
    self.response_description = response_description
    self.deprecated = deprecated
    self.operation_id = operation_id
    self.response_model_include = response_model_include
    self.response_model_exclude = response_model_exclude
    self.response_model_by_alias = response_model_by_alias
    self.response_model_exclude_unset = response_model_exclude_unset
    self.response_model_exclude_defaults = response_model_exclude_defaults
    self.response_model_exclude_none = response_model_exclude_none
    self.include_in_schema = include_in_schema
    self.response_class = response_class
    self.dependency_overrides_provider = dependency_overrides_provider
    self.callbacks = callbacks
    self.openapi_extra = openapi_extra
    self.generate_unique_id_function = generate_unique_id_function
    self.tags = tags or []
    self.responses = responses or {}
    self.name = get_name(endpoint) if name is None else name
    self.path_regex, self.path_format, self.param_convertors = compile_path(path)
    if methods is None:
        methods = ["GET"]
    self.methods: set[str] = {method.upper() for method in methods}
    if isinstance(generate_unique_id_function, DefaultPlaceholder):
        current_generate_unique_id: Callable[[APIRoute], str] = (
            generate_unique_id_function.value
        )
    else:
        current_generate_unique_id = generate_unique_id_function
    self.unique_id = self.operation_id or current_generate_unique_id(self)
    # normalize enums e.g. http.HTTPStatus
    if isinstance(status_code, IntEnum):
        status_code = int(status_code)
    self.status_code = status_code
    if self.response_model:
        assert is_body_allowed_for_status_code(status_code), (
            f"Status code {status_code} must not have a response body"
        )
        response_name = "Response_" + self.unique_id
        self.response_field = create_model_field(
            name=response_name,
            type_=self.response_model,
            mode="serialization",
        )
    else:
        self.response_field = None  # type: ignore
    self.dependencies = list(dependencies or [])
    self.description = description or inspect.cleandoc(self.endpoint.__doc__ or "")
    # if a "form feed" character (page break) is found in the description text,
    # truncate description text to the content preceding the first "form feed"
    self.description = self.description.split("\f")[0].strip()
    response_fields = {}
    for additional_status_code, response in self.responses.items():
        assert isinstance(response, dict), "An additional response must be a dict"
        model = response.get("model")
        if model:
            assert is_body_allowed_for_status_code(additional_status_code), (
                f"Status code {additional_status_code} must not have a response body"
            )
            response_name = f"Response_{additional_status_code}_{self.unique_id}"
            response_field = create_model_field(
                name=response_name, type_=model, mode="serialization"
            )
            response_fields[additional_status_code] = response_field
    if response_fields:
        self.response_fields: dict[int | str, ModelField] = response_fields
    else:
        self.response_fields = {}

    assert callable(endpoint), "An endpoint must be a callable"
    self.dependant = get_dependant(
        path=self.path_format, call=self.endpoint, scope="function"
    )
    for depends in self.dependencies[::-1]:
        self.dependant.dependencies.insert(
            0,
            get_parameterless_sub_dependant(depends=depends, path=self.path_format),
        )
    self._flat_dependant = get_flat_dependant(self.dependant)
    self._embed_body_fields = _should_embed_body_fields(
        self._flat_dependant.body_params
    )
    self.body_field = get_body_field(
        flat_dependant=self._flat_dependant,
        name=self.unique_id,
        embed_body_fields=self._embed_body_fields,
    )
    self.app = request_response(self.get_route_handler())