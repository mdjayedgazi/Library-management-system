from sqlmodel import Field, SQLModel

from app.models.books import BookCategory


class Create_Books(SQLModel):
    title: str = Field(max_length=150)
    author: str = Field(max_length=150)
    description: str = Field(max_length=220)
    price: float = Field(default=0, ge=0)
    total_copies: int = Field(default=1, ge=0)  # keep the intended version
    category: BookCategory = BookCategory.FICTION


class Update_Books(SQLModel):
    title: str | None = Field(default=None, max_length=150)
    author: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=220)
    price: float | None = Field(default=None, ge=0)
    total_copies: int | None = Field(default=None, ge=0)
    category: BookCategory | None = Field(default=None)


class IssueBook(SQLModel):
    book_id: int
    user_id: int
