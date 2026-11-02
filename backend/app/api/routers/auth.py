from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.core.database import db_Dependency
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.dependencies.auth import user_dependency
from app.models.user import Role, User
from app.schemas.auth import Token, UserCreate
from app.schemas.user import PasswordUpdate, UpdateUser, UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    new_user: UserCreate,
    db: db_Dependency,
):
    email = new_user.email.lower()

    statement = select(User).where(
        or_(
            User.username == new_user.username,
            User.email == email,
        )
    )

    existing_user = (await db.exec(statement)).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    user = User(
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        email=email,
        username=new_user.username,
        hash_password=get_password_hash(new_user.password),
        role=Role.MEMBER,
    )

    db.add(user)

    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        ) from exc

    return user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_Dependency,
):
    statement = select(User).where(User.username == form_data.username)

    user = (await db.exec(statement)).first()

    if user is None or not verify_password(
        form_data.password,
        user.hash_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        username=user.username,
        user_id=user.id,
        role=user.role.value,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.patch("/edituser", response_model=UserResponse)
async def update_user(
    current_user: user_dependency,
    update_data: UpdateUser,
    db: db_Dependency,
):
    data = update_data.model_dump(exclude_unset=True)

    # Lowercase email before updating to maintain consistency
    if "email" in data and data["email"] is not None:
        data["email"] = data["email"].lower()

    for key, value in data.items():
        setattr(current_user, key, value)

    db.add(current_user)

    try:
        await db.commit()
        await db.refresh(current_user)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        ) from exc

    return current_user


@router.patch("/changepassword")
async def update_password(
    current_user: user_dependency,
    update_pass: PasswordUpdate,
    db: db_Dependency,
):
    if not verify_password(
        update_pass.current_password,
        current_user.hash_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    current_user.hash_password = get_password_hash(update_pass.new_password)

    db.add(current_user)

    await db.commit()

    return {
        "message": "Password updated successfully",
    }
