from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class Role(str, Enum):
    LIBRARIAN = "librarian"
    MEMBER = "member"


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True, nullable=True, default=None)
    first_name: str
    last_name: str
    hash_password: str
    is_active: bool = True
    role: Role = Role.MEMBER
    phone_number: str | None = None
