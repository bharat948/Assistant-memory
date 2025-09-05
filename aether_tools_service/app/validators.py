from jsonschema import validate, ValidationError
from typing import Dict, Any, Tuple

def validate_input(schema: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Validates a payload against a given JSON schema."""
    if not schema:
        return True, ""
    try:
        validate(instance=payload, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, e.message
