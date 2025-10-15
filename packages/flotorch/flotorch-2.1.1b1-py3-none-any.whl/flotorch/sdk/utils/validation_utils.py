import json
from typing import Any

TYPE_MAP = {
    "string": str,
    "integer": int,
    "boolean": bool,
    "object": dict,
    "number": (int, float),  # Supports both int and float
}

def validate_data_against_schema(data: Any, schema: dict) -> bool:
    """
    Validate data against a JSON schema.

    Args:
        data: The data to validate (can be dict, str, or any JSON-serializable type)
        schema: The JSON schema to validate against

    Returns:
        bool: True if validation passes, False otherwise
    """
    if not schema:
        return True

    try:
        parsed_data = json.loads(data) if isinstance(data, str) else data
    except json.JSONDecodeError:
        return False

    required_fields = set(schema.get("required", []))
    if not isinstance(parsed_data, dict):
        return False

    missing_fields = required_fields - parsed_data.keys()
    if missing_fields:
        return False

    for field, spec in schema.get("properties", {}).items():
        if field not in parsed_data:
            continue

        expected_type = spec.get("type")
        expected_python_type = TYPE_MAP.get(expected_type)
        value = parsed_data[field]

        if expected_python_type and not isinstance(value, expected_python_type):
            return False

    return True
