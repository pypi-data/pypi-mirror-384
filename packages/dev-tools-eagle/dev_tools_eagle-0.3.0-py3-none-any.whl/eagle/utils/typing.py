from typing import get_type_hints, TypedDict

def initialize_nested(schema, data: dict) -> dict:
    """
    Recursively initialize nested fields in a schema with default values.

    Args:
        schema: The schema to initialize.
        data (dict): The input data to update.

    Returns:
        dict: The initialized data.
    """
    initialized = {}
    type_hints = get_type_hints(schema)
    for key, hint in type_hints.items():
        if isinstance(hint, type) and issubclass(hint, dict):
            # Recursively initialize nested TypedDict
            initialized[key] = initialize_nested(hint, data.get(key, {}))
        else:
            # Use provided value or default from schema
            initialized[key] = data.get(key, getattr(schema, key, None))
    return initialized
