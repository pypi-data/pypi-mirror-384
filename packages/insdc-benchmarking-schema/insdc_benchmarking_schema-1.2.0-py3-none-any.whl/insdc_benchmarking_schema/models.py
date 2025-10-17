"""Pydantic models for type-safe result handling"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime


class BenchmarkResult(BaseModel):
    """
    Pydantic model for INSDC benchmark results

    Example:
        >>> from insdc_benchmarking_schema import BenchmarkResult
        >>> result = BenchmarkResult(
        ...     timestamp="2025-01-15T14:30:00Z",
        ...     site="nci",
        ...     protocol="globus",
        ...     repository="ENA",
        ...     dataset_id="SRR12345678",
        ...     duration_sec=42.7,
        ...     file_size_bytes=104857600,
        ...     average_speed_mbps=950.5,
        ...     status="success",
        ...     checksum_md5="d41d8cd98f00b204e9800998ecf8427e"
        ... )
        >>> print(result.json(indent=2))
    """

    # Required fields
    timestamp: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
    site: str = Field(..., min_length=1)
    protocol: Literal["ftp", "aspera", "globus", "wget", "sra-toolkit", "ena-downloader", "http-browser", "other"]
    repository: Literal["ENA", "SRA", "DDBJ"]
    dataset_id: str = Field(..., pattern=r'^[SED]RR[0-9]+$')
    duration_sec: float = Field(..., ge=0)
    file_size_bytes: int = Field(..., ge=0)
    average_speed_mbps: float = Field(..., ge=0)
    status: Literal["success", "fail", "partial"]
    checksum_md5: str = Field(..., pattern=r'^[a-f0-9]{32}$')

    # Optional fields
    cpu_usage_percent: Optional[float] = Field(None, ge=0, le=100)
    memory_usage_mb: Optional[float] = Field(None, ge=0)
    checksum_sha256: Optional[str] = Field(None, pattern=r'^[a-f0-9]{64}$')
    write_speed_mbps: Optional[float] = Field(None, ge=0)
    network_latency_ms: Optional[float] = Field(None, ge=0)
    packet_loss_percent: Optional[float] = Field(None, ge=0, le=100)
    network_path: Optional[List[str]] = None
    error_message: Optional[str] = None
    tool_version: Optional[str] = None
    notes: Optional[str] = None

    @validator('site', 'protocol')
    def to_lowercase(cls, v):
        """Normalize to lowercase"""
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-01-15T14:30:00Z",
                "site": "nci",
                "protocol": "globus",
                "repository": "ENA",
                "dataset_id": "SRR12345678",
                "duration_sec": 42.7,
                "file_size_bytes": 104857600,
                "average_speed_mbps": 950.5,
                "status": "success",
                "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
            }
        }