"""
Transaction models for FastAPI SQLModel.
"""

from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from .base import BaseModel


class Transaction(SQLModel, table=True):
    
    __tablename__ = "transactions"
    """Model representing a transaction in the system."""
    id: Optional[int] = Field(default=None, primary_key=True)
    txid: str
    timestamp: datetime = Field(default=datetime.now(timezone.utc))
    stream: str

    def __str__(self) -> str:
        return f"ID:{self.id}, TXID:{self.txid}, Timestamp:{self.timestamp}"

 

