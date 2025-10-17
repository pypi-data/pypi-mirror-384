"""Validation utilities"""

import jsonschema
from typing import Dict, Any, List
from .schema import get_schema


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_result(result: Dict[str, Any], raise_on_error: bool = True) -> tuple[bool, List[str]]:
    """
    Validate a benchmark result against the schema

    Args:
        result: Dictionary containing benchmark result data
        raise_on_error: If True, raise ValidationError on validation failure

    Returns:
        tuple: (is_valid, error_messages)

    Raises:
        ValidationError: If validation fails and raise_on_error is True

    Example:
        >>> from insdc_benchmarking_schema import validate_result
        >>> result = {
        ...     "timestamp": "2025-01-15T14:30:00Z",
        ...     "site": "nci",
        ...     "protocol": "globus",
        ...     # ... other fields
        ... }
        >>> is_valid, errors = validate_result(result, raise_on_error=False)
        >>> if not is_valid:
        ...     print(f"Validation errors: {errors}")
    """
    schema = get_schema()
    errors = []

    try:
        jsonschema.validate(instance=result, schema=schema)
        return True, []
    except jsonschema.ValidationError as e:
        error_msg = f"{e.message} at path: {'.'.join(str(p) for p in e.path)}"
        errors.append(error_msg)

        if raise_on_error:
            raise ValidationError(error_msg) from e
        return False, errors
    except jsonschema.SchemaError as e:
        error_msg = f"Schema error: {e.message}"
        errors.append(error_msg)

        if raise_on_error:
            raise ValidationError(error_msg) from e
        return False, errors


def validate_batch(results: List[Dict[str, Any]]) -> tuple[int, int, List[tuple[int, str]]]:
    """
    Validate a batch of results

    Args:
        results: List of result dictionaries

    Returns:
        tuple: (valid_count, invalid_count, [(index, error_message), ...])
    """
    valid = 0
    invalid = 0
    errors = []

    for i, result in enumerate(results):
        is_valid, error_msgs = validate_result(result, raise_on_error=False)
        if is_valid:
            valid += 1
        else:
            invalid += 1
            for msg in error_msgs:
                errors.append((i, msg))

    return valid, invalid, errors