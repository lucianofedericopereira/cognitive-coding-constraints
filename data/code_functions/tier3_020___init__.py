# Source : https://github.com/pydantic/pydantic/blob/main/pydantic/fields.py (line 228)
# License: MIT
# Complexity: 12
# Tier   : tier3

def __init__(self, **kwargs: Unpack[_FieldInfoInputs]) -> None:
    """This class should generally not be initialized directly; instead, use the `pydantic.fields.Field` function
    or one of the constructor classmethods.

    See the signature of `pydantic.fields.Field` for more details about the expected arguments.
    """
    # Tracking the explicitly set attributes is necessary to correctly merge `Field()` functions
    # (e.g. with `Annotated[int, Field(alias='a'), Field(alias=None)]`, even though `None` is the default value,
    # we need to track that `alias=None` was explicitly set):
    self._attributes_set = {k: v for k, v in kwargs.items() if v is not _Unset and k not in self.metadata_lookup}
    kwargs = {k: _DefaultValues.get(k) if v is _Unset else v for k, v in kwargs.items()}  # type: ignore
    self.annotation = kwargs.get('annotation')

    # Note: in theory, the second `pop()` arguments are not required below, as defaults are already set from `_DefaultsValues`.
    default = kwargs.pop('default', PydanticUndefined)
    if default is Ellipsis:
        self.default = PydanticUndefined
        self._attributes_set.pop('default', None)
    else:
        self.default = default

    self.default_factory = kwargs.pop('default_factory', None)

    if self.default is not PydanticUndefined and self.default_factory is not None:
        raise TypeError('cannot specify both default and default_factory')

    self.alias = kwargs.pop('alias', None)
    self.validation_alias = kwargs.pop('validation_alias', None)
    self.serialization_alias = kwargs.pop('serialization_alias', None)
    alias_is_set = any(alias is not None for alias in (self.alias, self.validation_alias, self.serialization_alias))
    self.alias_priority = kwargs.pop('alias_priority', None) or 2 if alias_is_set else None
    self.title = kwargs.pop('title', None)
    self.field_title_generator = kwargs.pop('field_title_generator', None)
    self.description = kwargs.pop('description', None)
    self.examples = kwargs.pop('examples', None)
    self.exclude = kwargs.pop('exclude', None)
    self.exclude_if = kwargs.pop('exclude_if', None)
    self.discriminator = kwargs.pop('discriminator', None)
    # For compatibility with FastAPI<=0.110.0, we preserve the existing value if it is not overridden
    self.deprecated = kwargs.pop('deprecated', getattr(self, 'deprecated', None))
    self.repr = kwargs.pop('repr', True)
    self.json_schema_extra = kwargs.pop('json_schema_extra', None)
    self.validate_default = kwargs.pop('validate_default', None)
    self.frozen = kwargs.pop('frozen', None)
    # currently only used on dataclasses
    self.init = kwargs.pop('init', None)
    self.init_var = kwargs.pop('init_var', None)
    self.kw_only = kwargs.pop('kw_only', None)

    self.metadata = self._collect_metadata(kwargs)  # type: ignore

    # Private attributes:
    self._qualifiers: set[Qualifier] = set()
    # Used to rebuild FieldInfo instances:
    self._complete = True
    self._original_annotation: Any = PydanticUndefined
    self._original_assignment: Any = PydanticUndefined
    # Used to track whether the `FieldInfo` instance represents the data about a field (and is exposed in `model_fields`/`__pydantic_fields__`),
    # or if it is the result of the `Field()` function being used as metadata in an `Annotated` type/as an assignment
    # (not an ideal pattern, see https://github.com/pydantic/pydantic/issues/11122):
    self._final = False