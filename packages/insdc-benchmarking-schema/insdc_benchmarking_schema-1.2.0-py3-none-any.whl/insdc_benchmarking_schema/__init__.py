"""
INSDC Benchmarking Schema

A Python package providing JSON schema and validation utilities
for INSDC data transfer benchmarking results.
"""

__version__ = "1.2.0"

from .schema import get_schema, get_schema_path, get_example
from .validator import validate_result, validate_batch, ValidationError
from .models import BenchmarkResult

__all__ = [
    "get_schema",
    "get_schema_path",
    "get_example",
    "validate_result",
    "validate_batch",
    "ValidationError",
    "BenchmarkResult",
    "__version__",
]