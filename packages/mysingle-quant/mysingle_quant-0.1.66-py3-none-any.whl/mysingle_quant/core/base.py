from datetime import UTC, datetime

from beanie import Document, Insert, PydanticObjectId, Save, Update, before_event
from pydantic import BaseModel, ConfigDict, Field


class BaseDoc(Document):
    """Base Document model."""


class BaseDocWithUserId(BaseDoc):
    """Base User Document model."""

    user_id: PydanticObjectId


class BaseTimeDoc(BaseDoc):
    """Base Document model with created_at and updated_at fields."""

    created_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))

    @before_event([Insert, Save])
    def set_created_at(self):
        self.created_at = datetime.now(UTC)
        self.updated_at = self.created_at

    @before_event([Update])
    def set_updated_at(self):
        self.updated_at = datetime.now(UTC)


class BaseTimeDocWithUserId(BaseTimeDoc):
    """Base User Document model with created_at and updated_at fields."""

    user_id: PydanticObjectId


class BaseResponseSchema(BaseModel):
    id: PydanticObjectId = Field(..., alias="_id")

    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
