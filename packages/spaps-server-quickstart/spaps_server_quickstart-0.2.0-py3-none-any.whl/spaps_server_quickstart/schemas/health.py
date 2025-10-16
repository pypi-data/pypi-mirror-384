"""
Health response schema shared across Sweet Potato services.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service status indicator.")
    service: str = Field(default="service", description="Service identifier.")
    version: str = Field(default="unknown", description="Application version.")
    database_ready: bool = Field(
        default=False,
        description="Whether the database responded to the readiness probes.",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional service-specific health details.",
    )
