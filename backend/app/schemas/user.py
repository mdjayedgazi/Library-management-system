from pydantic import EmailStr, Field
from sqlmodel import SQLModel

from app.models.user import Role


class UserResponse(SQLModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    role: Role
    is_active: bool
    phone_number: str | None = None


class UpdateUser(SQLModel):
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    email: EmailStr | None = Field(default=None)
    phone_number: str | None = Field(default=None)


class PasswordUpdate(SQLModel):
    current_password: str
    new_password: str
