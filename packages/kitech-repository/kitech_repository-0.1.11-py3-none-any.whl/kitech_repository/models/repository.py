"""Repository model definitions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Repository(BaseModel):
    """Repository model."""

    id: int
    name: str
    description: str | None = None
    is_public: bool = Field(alias="isPublic")
    owner_id: str = Field(alias="ownerId")
    owner_name: str = Field(alias="ownerName")
    user_role: str | None = Field(alias="userRole", default="VIEWER")  # OWNER, ADMIN, VIEWER, NONE
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)
