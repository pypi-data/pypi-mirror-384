import copy
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict


def generate_choices_from_enum(enum_class: Enum) -> tuple:
    return tuple((enum.value, enum.value) for enum in enum_class)


def get_values_from_enums(enum: Enum) -> list:
    """
    Get values from enum
    :param enum: Enum
    :return: Values
    """
    return [e.value for e in enum]


def get_current_utc_datetime() -> datetime:
    """
    Get current UTC datetime
    :return: Current UTC datetime
    """
    return datetime.now(timezone.utc)


def mask_sensitive_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive data in payload for logging purposes
    :param payload: dict containing payload data
    :return: dict with sensitive data masked
    """
    # Create a deep copy to avoid modifying the original payload
    masked_payload = copy.deepcopy(payload)

    return mask_recursive(masked_payload)


def mask_recursive(obj: Any) -> Any:
    """
    Recursively mask sensitive data in nested structures
    """
    sensitive_keys = [
        'access_token',
        'refresh_token',
        'password',
        'secret',
        'authorization',
        'bearer'
    ]

    if isinstance(obj, dict):
        for key, value in obj.items():
            # Check if key contains any sensitive terms (case-insensitive)
            if any(sensitive_key.lower() in key.lower() for sensitive_key in sensitive_keys):
                if isinstance(value, str) and len(value) > 8:
                    # Keep first 4 and last 4 characters, mask the middle
                    obj[key] = f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
                else:
                    obj[key] = "***MASKED***"
            else:
                obj[key] = mask_recursive(value)

    elif isinstance(obj, list):
        return [mask_recursive(item) for item in obj]

    return obj
