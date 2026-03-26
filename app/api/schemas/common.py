"""Shared schema primitives: pagination, error envelopes, and health."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""

    limit: int = Field(50, ge=1, le=200, description="Max items per page")
    offset: int = Field(0, ge=0, description="Number of items to skip")


class PaginatedResponse(BaseModel, Generic[T]):
    """Envelope for paginated list responses."""

    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    """Standard error body."""

    detail: str
    code: str | None = None
    extra: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class MessageResponse(BaseModel):
    """Generic success message."""

    message: str
