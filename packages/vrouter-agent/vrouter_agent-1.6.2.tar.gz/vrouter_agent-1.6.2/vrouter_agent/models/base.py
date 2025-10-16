"""
Base models with common fields and utilities for SQLModel schemas.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import uuid


class BaseModel(SQLModel):
    """Base model with common timestamp fields"""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class UUIDBaseModel(BaseModel):
    """Base model with UUID support"""

    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


class TimestampMixin(SQLModel):
    """Mixin for models that need timestamp fields only"""

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
