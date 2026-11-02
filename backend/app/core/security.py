from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    email: str,
    user_id: int,
    role: str,
) -> str:
    data = {
        "sub": email,
        "id": user_id,
        "role": role,
        "exp": datetime.now(UTC)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
