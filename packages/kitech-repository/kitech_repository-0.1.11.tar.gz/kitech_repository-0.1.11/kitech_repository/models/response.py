"""API response model definitions."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiResponse(BaseModel):
    """Generic API response model."""

    success: bool
    message: str | None = None
    data: Any | None = None

    model_config = ConfigDict(populate_by_name=True)
