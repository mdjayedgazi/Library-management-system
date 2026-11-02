from collections.abc import Sequence

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.core.database import db_Dependency
from app.dependencies.auth import user_dependency
from app.models.books import Book
from app.models.issue_records import IssueRecord
from app.models.reservations import Reservation, Status

router = APIRouter(
    prefix="/books",
    tags=["Books"],
)


@router.get("/all", response_model=list[Book])
async def get_all_books(
    db: db_Dependency,
) -> Sequence[Book]:
    result = await db.exec(select(Book))
    return result.all()


@router.get("/{book_id}", response_model=Book)
async def get_book(
    book_id: int,
    db: db_Dependency,
) -> Book:
    result = await db.exec(
        select(Book).where(Book.id == book_id)
    )
    book = result.first()

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    return book


@router.post("/reserve/{book_id}", status_code=status.HTTP_201_CREATED)
async def reserve_book(
    book_id: int,
    user: user_dependency,
    db: db_Dependency,
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )

    result = await db.exec(select(Book).where(Book.id == book_id))
    book = result.first()

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    reservation_model = Reservation(
        book_id=book_id,
        user_id=user.id,
    )

    db.add(reservation_model)
    await db.commit()
    await db.refresh(reservation_model)

    return {
        "message": "Book reserved successfully",
    }


@router.put("/reserve/cancel/{reservation_id}")
async def cancel_reservation(
    reservation_id: int,
    user: user_dependency,
    db: db_Dependency,
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )

    result = await db.exec(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.first()

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    if reservation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot cancel this reservation",
        )

    reservation.status = Status.REJECTED

    await db.commit()
    await db.refresh(reservation)

    return {
        "message": "Reservation cancelled successfully",
    }


@router.get("/reservation/my", response_model=list[Reservation])
async def my_reservations(
    user: user_dependency,
    db: db_Dependency,
) -> Sequence[Reservation]:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )

    result = await db.exec(select(Reservation).where(Reservation.user_id == user.id))

    return result.all()


@router.get("/issues/my")
async def my_issued_books(user: user_dependency, db: db_Dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )

    issues = await db.exec(
        select(IssueRecord).where(
            IssueRecord.user_id == user.id,
            IssueRecord.status == "issued",
        )
    )

    return issues.all()
