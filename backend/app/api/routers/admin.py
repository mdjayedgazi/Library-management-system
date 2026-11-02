from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, status
from fastapi.responses import JSONResponse
from sqlmodel import select, update

from app.core.database import db_Dependency
from app.dependencies.auth import user_dependency
from app.models.books import Book
from app.models.issue_records import IssueRecord
from app.models.reservations import Reservation, Status
from app.models.user import Role, User
from app.schemas.book import Create_Books, IssueBook, Update_Books


def calculate_fine(du_date: datetime, return_date: datetime) -> float:
    overdue_days = (return_date.date() - du_date.date()).days
    if overdue_days > 0:
        total_fine = round(overdue_days * 20, 2)
    else:
        total_fine = 0.0
    return total_fine


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.post("/add_book", status_code=status.HTTP_201_CREATED)
async def create_book(
    new_book: Annotated[Create_Books, Form()],
    user: user_dependency,
    db: db_Dependency,
):
    if user is None or user.role != Role.LIBRARIAN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed Authentication",
        )

    book_model = Book(
        **new_book.model_dump(),
        available_copies=new_book.total_copies,
    )

    db.add(book_model)
    await db.commit()
    await db.refresh(book_model)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Book added successfully",
        },
    )


@router.patch("/update_book/{book_id}", status_code=status.HTTP_200_OK)
async def update_book(
    book_id: int,
    update: Update_Books,
    user: user_dependency,
    db: db_Dependency,
):
    if user is None or user.role != Role.LIBRARIAN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed Authentication",
        )

    # Find the book
    result = await db.exec(select(Book).where(Book.id == book_id))
    book = result.first()

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    # Include only supplied, non-null fields
    update_data = update.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    # Keep available copies consistent with total copies
    if "total_copies" in update_data:
        new_total = update_data["total_copies"]
        checked_out = book.total_copies - book.available_copies

        if new_total < checked_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total copies cannot be less than checked-out copies",
            )

        book.available_copies = new_total - checked_out

    # Update only the supplied fields
    for field, value in update_data.items():
        setattr(book, field, value)

    await db.commit()
    await db.refresh(book)

    return {
        "message": "Book updated successfully",
        "book_id": book.id,
    }


@router.delete("/delete_book/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(db: db_Dependency, user: user_dependency, book_id: int):

    if user is None or user.role != Role.LIBRARIAN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed Authentication",
        )
    result = await db.exec(select(Book).where(Book.id == book_id))
    book = result.first()
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    await db.delete(book)
    await db.commit()

    return {
        "message": "Book deleted successfully",
    }


@router.post("/issue_record", status_code=status.HTTP_201_CREATED)
async def issue_record(
    user: user_dependency, db: db_Dependency, issue_request: IssueBook
):

    if user is None or user.role != Role.LIBRARIAN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed Authentication",
        )

    result = await db.exec(select(Book).where(Book.id == issue_request.book_id))
    book = result.first()

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    result = await db.exec(select(User).where(User.id == issue_request.user_id))
    user = result.first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if book.available_copies <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Copies Available",
        )

    issue_date = datetime.now(UTC)

    issue_model = IssueRecord(
        book_id=issue_request.book_id,
        user_id=issue_request.user_id,
        issue_date=issue_date,
        due_date=issue_date + timedelta(days=14),
        status="issued",
    )

    book.available_copies -= 1
    result = await db.exec(
        select(Reservation).where(
            Reservation.book_id == issue_request.book_id,
            Reservation.user_id == issue_request.user_id,
            Reservation.status == Status.PENDING,
        )
    )
    reservation = result.first()

    if reservation is not None:
        reservation.status = Status.APPROVED

    db.add(issue_model)
    await db.commit()
    await db.refresh(issue_model)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Book Issued successfully"},
    )


@router.patch(
    "/return_book/{issue_id}",
    status_code=status.HTTP_200_OK,
)
async def return_book(
    user: user_dependency,
    db: db_Dependency,
    issue_id: int,
):
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Not authenticated",
        )

    if user.role != Role.LIBRARIAN:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Librarian access required",
        )

    result = await db.exec(
        select(IssueRecord).where(IssueRecord.id == issue_id).with_for_update()
    )
    issue = result.first()

    if issue is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Issue record not found",
        )

    if issue.return_date is not None or issue.status == "returned":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Book already returned",
        )

    return_date = datetime.now(UTC)
    fine = calculate_fine(issue.due_date, return_date)

    result = await db.exec(
        update(Book)
        .where(
            Book.id == issue.book_id,
            Book.available_copies < Book.total_copies,
        )
        .values(available_copies=Book.available_copies + 1)
    )

    if result.rowcount != 1:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Book inventory could not be updated",
        )

    issue.return_date = return_date
    issue.status = "returned"
    issue.fine_amount = fine

    await db.commit()
    await db.refresh(issue)

    return {
        "message": "Book returned successfully",
        "fine_amount": fine,
    }


@router.patch("/fine/pay/{issue_id}")
async def fine_paid(user: user_dependency, db: db_Dependency, issue_id: int):

    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Not authenticated",
        )
    if user.role != Role.LIBRARIAN:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Librarian access required",
        )

    result = await db.exec(select(IssueRecord).where(IssueRecord.id == issue_id))
    issue = result.first()

    if issue is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Issue record not found",
        )

    issue.fine_paid = True

    await db.commit()
    await db.refresh(issue)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Fine paid successfully"},
    )
