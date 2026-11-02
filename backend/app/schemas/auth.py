from pydantic import EmailStr
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str


class Token(SQLModel):
    access_token: str
    token_type: str
