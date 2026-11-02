from datetime import UTC, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class Status(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Reservation(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    book_id: int = Field(default=None, foreign_key="book.id")
    user_id: int = Field(default=None, foreign_key="user.id")
    reservation_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: Status = Status.PENDING
