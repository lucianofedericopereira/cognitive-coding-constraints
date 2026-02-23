# Source : https://github.com/fastapi/fastapi/blob/master/fastapi/routing.py (line 341)
# License: MIT
# Complexity: 27
# Tier   : tier4

async def app(request: Request) -> Response:
    response: Response | None = None
    file_stack = request.scope.get("fastapi_middleware_astack")
    assert isinstance(file_stack, AsyncExitStack), (
        "fastapi_middleware_astack not found in request scope"
    )

    # Extract endpoint context for error messages
    endpoint_ctx = (
        _extract_endpoint_context(dependant.call)
        if dependant.call
        else EndpointContext()
    )

    if dependant.path:
        # For mounted sub-apps, include the mount path prefix
        mount_path = request.scope.get("root_path", "").rstrip("/")
        endpoint_ctx["path"] = f"{request.method} {mount_path}{dependant.path}"

    # Read body and auto-close files
    try:
        body: Any = None
        if body_field:
            if is_body_form:
                body = await request.form()
                file_stack.push_async_callback(body.close)
            else:
                body_bytes = await request.body()
                if body_bytes:
                    json_body: Any = Undefined
                    content_type_value = request.headers.get("content-type")
                    if not content_type_value:
                        json_body = await request.json()
                    else:
                        message = email.message.Message()
                        message["content-type"] = content_type_value
                        if message.get_content_maintype() == "application":
                            subtype = message.get_content_subtype()
                            if subtype == "json" or subtype.endswith("+json"):
                                json_body = await request.json()
                    if json_body != Undefined:
                        body = json_body
                    else:
                        body = body_bytes
    except json.JSONDecodeError as e:
        validation_error = RequestValidationError(
            [
                {
                    "type": "json_invalid",
                    "loc": ("body", e.pos),
                    "msg": "JSON decode error",
                    "input": {},
                    "ctx": {"error": e.msg},
                }
            ],
            body=e.doc,
            endpoint_ctx=endpoint_ctx,
        )
        raise validation_error from e
    except HTTPException:
        # If a middleware raises an HTTPException, it should be raised again
        raise
    except Exception as e:
        http_error = HTTPException(
            status_code=400, detail="There was an error parsing the body"
        )
        raise http_error from e

    # Solve dependencies and run path operation function, auto-closing dependencies
    errors: list[Any] = []
    async_exit_stack = request.scope.get("fastapi_inner_astack")
    assert isinstance(async_exit_stack, AsyncExitStack), (
        "fastapi_inner_astack not found in request scope"
    )
    solved_result = await solve_dependencies(
        request=request,
        dependant=dependant,
        body=body,
        dependency_overrides_provider=dependency_overrides_provider,
        async_exit_stack=async_exit_stack,
        embed_body_fields=embed_body_fields,
    )
    errors = solved_result.errors
    if not errors:
        raw_response = await run_endpoint_function(
            dependant=dependant,
            values=solved_result.values,
            is_coroutine=is_coroutine,
        )
        if isinstance(raw_response, Response):
            if raw_response.background is None:
                raw_response.background = solved_result.background_tasks
            response = raw_response
        else:
            response_args: dict[str, Any] = {
                "background": solved_result.background_tasks
            }
            # If status_code was set, use it, otherwise use the default from the
            # response class, in the case of redirect it's 307
            current_status_code = (
                status_code if status_code else solved_result.response.status_code
            )
            if current_status_code is not None:
                response_args["status_code"] = current_status_code
            if solved_result.response.status_code:
                response_args["status_code"] = solved_result.response.status_code
            # Use the fast path (dump_json) when no custom response
            # class was set and a response field with a TypeAdapter
            # exists. Serializes directly to JSON bytes via Pydantic's
            # Rust core, skipping the intermediate Python dict +
            # json.dumps() step.
            use_dump_json = response_field is not None and isinstance(
                response_class, DefaultPlaceholder
            )
            content = await serialize_response(
                field=response_field,
                response_content=raw_response,
                include=response_model_include,
                exclude=response_model_exclude,
                by_alias=response_model_by_alias,
                exclude_unset=response_model_exclude_unset,
                exclude_defaults=response_model_exclude_defaults,
                exclude_none=response_model_exclude_none,
                is_coroutine=is_coroutine,
                endpoint_ctx=endpoint_ctx,
                dump_json=use_dump_json,
            )
            if use_dump_json:
                response = Response(
                    content=content,
                    media_type="application/json",
                    **response_args,
                )
            else:
                response = actual_response_class(content, **response_args)
            if not is_body_allowed_for_status_code(response.status_code):
                response.body = b""
            response.headers.raw.extend(solved_result.response.headers.raw)
    if errors:
        validation_error = RequestValidationError(
            errors, body=body, endpoint_ctx=endpoint_ctx
        )
        raise validation_error

    # Return response
    assert response
    return response