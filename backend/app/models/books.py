from datetime import UTC, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class BookCategory(str, Enum):
    COMPUTER_SCIENCE = "computer_science"
    SCIENCE = "science"
    HISTORY = "history"
    BUSINESS_ECONOMICS = "business_economics"
    SELF_HELP = "self_help"
    FICTION = "fiction"
    CLASSIC_LITERATURE = "classic_literature"
    BIOGRAPHY = "biography"
    PSYCHOLOGY = "psychology"
    MATHEMATICS = "mathematics"


class Book(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    author: str
    category: BookCategory = BookCategory.FICTION
    description: str
    price: float
    total_copies: int = Field(default=5)
    available_copies: int = Field(default=3)
    cover_image: str | None = Field(nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
