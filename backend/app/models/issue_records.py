from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class IssueRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    book_id: int = Field(foreign_key="book.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    issue_date: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
    due_date: datetime = Field(nullable=False)
    return_date: datetime | None = Field(default=None, nullable=True)

    status: str = Field(default="issued", nullable=False)
    fine_amount: float = Field(default=0.0, ge=0, nullable=False)
    fine_paid: bool = Field(default=False, nullable=False)
