# Source : https://github.com/tornadoweb/tornado/blob/master/tornado/web.py (line 3183)
# License: Apache-2.0
# Complexity: 1
# Tier   : tier1

def get_version(cls, settings: Dict[str, Any], path: str) -> Optional[str]:
    """Generate the version string to be used in static URLs.

    ``settings`` is the `Application.settings` dictionary and ``path``
    is the relative location of the requested asset on the filesystem.
    The returned value should be a string, or ``None`` if no version
    could be determined.

    .. versionchanged:: 3.1
       This method was previously recommended for subclasses to override;
       `get_content_version` is now preferred as it allows the base
       class to handle caching of the result.
    """
    abs_path = cls.get_absolute_path(settings["static_path"], path)
    return cls._get_cached_version(abs_path)