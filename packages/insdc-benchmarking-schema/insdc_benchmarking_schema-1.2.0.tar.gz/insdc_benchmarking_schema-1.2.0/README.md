# INSDC Benchmarking Schema

Python package providing JSON schema and validation for INSDC benchmarking results.

## Installation

```bash
pip install insdc-benchmarking-schema
```

## Quick Start

```python
from insdc_benchmarking_schema import BenchmarkResult

result = BenchmarkResult(
    timestamp="2025-01-15T14:30:00Z",
    site="nci",
    protocol="globus",
    repository="ENA",
    dataset_id="SRR12345678",
    duration_sec=42.7,
    file_size_bytes=104857600,
    average_speed_mbps=950.5,
    status="success",
    checksum_md5="d41d8cd98f00b204e9800998ecf8427e"
)

print(result.model_dump_json(indent=2))
```

See full documentation in the repository.
