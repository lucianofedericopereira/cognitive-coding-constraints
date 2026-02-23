# Source : https://github.com/pydantic/pydantic/blob/main/pydantic/_internal/_generate_schema.py (line 2728)
# License: MIT
# Complexity: 1
# Tier   : tier1

def get_schema_from_ref(self, ref: str) -> CoreSchema | None:
    """Resolve the schema from the given reference."""
    return self._definitions.get(ref)