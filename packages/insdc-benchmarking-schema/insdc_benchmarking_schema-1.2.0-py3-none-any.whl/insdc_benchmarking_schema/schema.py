"""Schema access utilities"""

import json
from pathlib import Path
from typing import Dict, Any

SCHEMA_VERSION = "1.2.0"


def get_schema_path() -> Path:
    """Get path to the JSON schema file"""
    return Path(__file__).parent / "data" / "result-schema-v1.2.json"


def get_schema() -> Dict[str, Any]:
    """
    Load and return the JSON schema

    Returns:
        dict: The JSON schema as a dictionary

    Example:
        >>> from insdc_benchmarking_schema import get_schema
        >>> schema = get_schema()
        >>> print(schema['title'])
        'INSDC Benchmarking Result v1.2'
    """
    with open(get_schema_path(), 'r') as f:
        return json.load(f)


def get_example() -> Dict[str, Any]:
    """Load and return an example valid result"""
    example_path = Path(__file__).parent / "examples" / "example_result.json"
    with open(example_path, 'r') as f:
        return json.load(f)