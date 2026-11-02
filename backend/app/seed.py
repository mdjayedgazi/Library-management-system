"""Idempotent development seed data for the Library Management API.

This script uses the project's existing SQLModel models and async session
configuration. It never deletes or truncates data and can be run repeatedly:
records are matched on natural keys before insertion.

Usage (from the ``backend`` directory):

    uv run python -m app.seed                 # local databases only
    uv run python -m app.seed --dry-run       # roll back at the end
    uv run python -m app.seed --allow-remote  # explicit opt-in for a remote dev DB

Safety: by default the script refuses to run unless the configured database
host is local. Use ``--allow-remote`` only when you have confirmed that
``DATABASE_URL`` points at a disposable development database.

Seed Credentials
----------------
The script requires two environment variables for account passwords. There are
no defaults: if they are missing the script exits with a clear error message.

    SEED_LIBRARIAN_PASSWORD=<strong password for librarian accounts>
    SEED_MEMBER_PASSWORD=<strong password for member accounts>

Passwords are never printed to stdout.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.engine import make_url
from sqlmodel import select

from app.core.config import settings
from app.core.database import async_session, create_db_and_tables, engine
from app.core.security import get_password_hash
from app.models.books import Book, BookCategory
from app.models.issue_records import IssueRecord
from app.models.reservations import Reservation, Status
from app.models.user import Role, User

LOCAL_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "db",
    "postgres",
    "host.docker.internal",
}


def _dt(year: int, month: int, day: int, hour: int = 9) -> datetime:
    """Fixed timestamps keep the seed idempotent across runs."""
    return datetime(year, month, day, hour, 0, tzinfo=UTC)


USERS: list[dict[str, Any]] = [
    {
        "username": "librarian",
        "email": "librarian@library.dev",
        "first_name": "Maya",
        "last_name": "Rahman",
        "role": Role.LIBRARIAN,
        "phone_number": "+8801700000001",
    },
    {
        "username": "assistant",
        "email": "assistant@library.dev",
        "first_name": "Omar",
        "last_name": "Hasan",
        "role": Role.LIBRARIAN,
        "phone_number": "+8801700000002",
    },
    {
        "username": "alice",
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Carter",
        "role": Role.MEMBER,
        "phone_number": "+8801700000011",
    },
    {
        "username": "bob",
        "email": "bob@example.com",
        "first_name": "Bob",
        "last_name": "Nguyen",
        "role": Role.MEMBER,
        "phone_number": "+8801700000012",
    },
    {
        "username": "carol",
        "email": "carol@example.com",
        "first_name": "Carol",
        "last_name": "Mendes",
        "role": Role.MEMBER,
        "phone_number": "+8801700000013",
    },
    {
        "username": "david",
        "email": "david@example.com",
        "first_name": "David",
        "last_name": "Okafor",
        "role": Role.MEMBER,
        "phone_number": "+8801700000014",
    },
    {
        "username": "emma",
        "email": "emma@example.com",
        "first_name": "Emma",
        "last_name": "Lindqvist",
        "role": Role.MEMBER,
        "phone_number": "+8801700000015",
    },
    {
        "username": "farhan",
        "email": "farhan@example.com",
        "first_name": "Farhan",
        "last_name": "Ahmed",
        "role": Role.MEMBER,
        "phone_number": "+8801700000016",
    },
    {
        "username": "grace",
        "email": "grace@example.com",
        "first_name": "Grace",
        "last_name": "Kim",
        "role": Role.MEMBER,
        "phone_number": "+8801700000017",
    },
    {
        "username": "hassan",
        "email": "hassan@example.com",
        "first_name": "Hassan",
        "last_name": "Ali",
        "role": Role.MEMBER,
        "phone_number": "+8801700000018",
    },
    {
        "username": "isabel",
        "email": "isabel@example.com",
        "first_name": "Isabel",
        "last_name": "Moreau",
        "role": Role.MEMBER,
        "phone_number": "+8801700000019",
    },
    {
        "username": "jonas",
        "email": "jonas@example.com",
        "first_name": "Jonas",
        "last_name": "Weber",
        "role": Role.MEMBER,
        "phone_number": "+8801700000020",
    },
    {
        "username": "keira",
        "email": "keira@example.com",
        "first_name": "Keira",
        "last_name": "Walsh",
        "role": Role.MEMBER,
        "phone_number": "+8801700000021",
    },
    {
        "username": "liam",
        "email": "liam@example.com",
        "first_name": "Liam",
        "last_name": "Foster",
        "role": Role.MEMBER,
        "phone_number": "+8801700000022",
    },
]


# (title, author, category, price, total_copies, isbn, description)
# Cover images are derived from these ISBNs via the Open Library Covers API.
# Edition-by-edition verification is recorded in BOOK_COVER_URLS.md at the
# repository root.
BOOKS: list[tuple[str, str, BookCategory, float, int, str, str]] = [
    # Category 1: Computer Science & Technology (3)
    (
        "Clean Code",
        "Robert C. Martin",
        BookCategory.COMPUTER_SCIENCE,
        32.00,
        4,
        "9780132350884",
        "A practical guide to writing readable, maintainable software through disciplined naming, structure, and refactoring techniques that improve code quality.",
    ),
    (
        "Python Crash Course",
        "Eric Matthes",
        BookCategory.COMPUTER_SCIENCE,
        22.99,
        5,
        "9781718502703",
        "A hands-on, project-based introduction to Python that takes beginners from fundamentals to building games, data visualizations, and web applications.",
    ),
    (
        "The Pragmatic Programmer",
        "David Thomas and Andrew Hunt",
        BookCategory.COMPUTER_SCIENCE,
        45.00,
        4,
        "9780135957059",
        "Timeless advice on software craftsmanship, covering tools, techniques, and mindsets that help programmers write better code and build better systems.",
    ),
    # Category 2: Science (3)
    (
        "A Brief History of Time",
        "Stephen Hawking",
        BookCategory.SCIENCE,
        15.99,
        6,
        "9780553380163",
        "An accessible journey through cosmology, black holes, time, and the search for a unified theory of the universe by one of the greatest physicists of our time.",
    ),
    (
        "Cosmos",
        "Carl Sagan",
        BookCategory.SCIENCE,
        18.00,
        5,
        "9780345539434",
        "A sweeping exploration of the universe, from the origins of life to the fate of galaxies, blending science, philosophy, and wonder into a single narrative.",
    ),
    (
        "The Selfish Gene",
        "Richard Dawkins",
        BookCategory.SCIENCE,
        14.75,
        5,
        "9780198788607",
        "A landmark account of evolution from the gene's perspective, explaining altruism, cooperation, and the mechanics of natural selection.",
    ),
    # Category 3: History (3)
    (
        "Sapiens: A Brief History of Humankind",
        "Yuval Noah Harari",
        BookCategory.HISTORY,
        21.00,
        7,
        "9780062316097",
        "A sweeping history of humankind traces how language, cooperation, and belief shaped civilizations and our modern world from the Stone Age to the Silicon Age.",
    ),
    (
        "Guns, Germs, and Steel",
        "Jared Diamond",
        BookCategory.HISTORY,
        18.75,
        4,
        "9780393354324",
        "An inquiry into why some societies came to dominate others, arguing that geography and environment — not racial or cultural superiority — shaped history.",
    ),
    (
        "The Diary of a Young Girl",
        "Anne Frank",
        BookCategory.HISTORY,
        12.99,
        7,
        "9780553296983",
        "The intimate journal of a Jewish girl hiding from the Nazis in Amsterdam, offering a timeless account of courage, hope, and humanity during the Holocaust.",
    ),
    # Category 4: Business & Economics (3)
    (
        "The Lean Startup",
        "Eric Ries",
        BookCategory.BUSINESS_ECONOMICS,
        16.99,
        5,
        "9780307887894",
        "A methodology for building successful startups through rapid experimentation, validated learning, and iterative product releases based on customer feedback.",
    ),
    (
        "Zero to One",
        "Peter Thiel",
        BookCategory.BUSINESS_ECONOMICS,
        17.00,
        5,
        "9780804139298",
        "A venture capitalist's argument that true progress comes from creating something entirely new rather than competing in existing markets.",
    ),
    (
        "The Intelligent Investor",
        "Benjamin Graham",
        BookCategory.BUSINESS_ECONOMICS,
        24.00,
        4,
        "9780060555665",
        "The definitive guide to value investing, teaching principles of risk management, margin of safety, and long-term wealth building through disciplined analysis.",
    ),
    # Category 5: Self-Help & Productivity (3)
    (
        "Atomic Habits",
        "James Clear",
        BookCategory.SELF_HELP,
        16.99,
        9,
        "9780735211292",
        "A practical framework for building good habits and breaking bad ones through small, compounding changes that transform your life over time.",
    ),
    (
        "Deep Work",
        "Cal Newport",
        BookCategory.SELF_HELP,
        15.25,
        6,
        "9781455586691",
        "An argument for focused, distraction-free work and a set of strategies for cultivating concentration in a noisy, hyperconnected world.",
    ),
    (
        "How to Win Friends and Influence People",
        "Dale Carnegie",
        BookCategory.SELF_HELP,
        14.99,
        6,
        "9780671027032",
        "A timeless guide to interpersonal skills, communication, and leadership that has helped millions improve their relationships and influence others positively.",
    ),
    # Category 6: Fiction (3)
    (
        "The Alchemist",
        "Paulo Coelho",
        BookCategory.FICTION,
        11.75,
        7,
        "9780062315007",
        "An Andalusian shepherd travels in search of treasure and discovers a deeper lesson about following one's personal legend and listening to the heart.",
    ),
    (
        "1984",
        "George Orwell",
        BookCategory.FICTION,
        13.99,
        8,
        "9780451524935",
        "In a dystopian future, a totalitarian regime controls every aspect of life, and one man's quiet rebellion reveals the devastating cost of freedom.",
    ),
    (
        "To Kill a Mockingbird",
        "Harper Lee",
        BookCategory.FICTION,
        12.99,
        6,
        "9780061120084",
        "A young girl in the American South witnesses her father's courageous defense of an innocent man, confronting racism, injustice, and moral growth.",
    ),
    # Category 7: Classic Literature (3)
    (
        "Pride and Prejudice",
        "Jane Austen",
        BookCategory.CLASSIC_LITERATURE,
        9.99,
        9,
        "9780141439518",
        "Elizabeth Bennet and Mr. Darcy navigate pride, prejudice, and social expectation in Austen's enduring comedy of manners and romance.",
    ),
    (
        "The Great Gatsby",
        "F. Scott Fitzgerald",
        BookCategory.CLASSIC_LITERATURE,
        12.99,
        6,
        "9780743273565",
        "A mysterious millionaire throws lavish parties on Long Island while chasing a lost love, in a portrait of ambition and the American Dream.",
    ),
    (
        "Jane Eyre",
        "Charlotte Brontë",
        BookCategory.CLASSIC_LITERATURE,
        11.50,
        5,
        "9780141441146",
        "An orphaned governess falls in love with her brooding employer at Thornfield Hall, where dark secrets and moral trials test her independence and faith.",
    ),
    # Category 8: Biography & Memoir (3)
    (
        "Steve Jobs",
        "Walter Isaacson",
        BookCategory.BIOGRAPHY,
        18.99,
        5,
        "9781451648539",
        "The definitive biography of Apple's co-founder, based on extensive interviews, revealing his genius, temper, and relentless drive to change the world.",
    ),
    (
        "Long Walk to Freedom",
        "Nelson Mandela",
        BookCategory.BIOGRAPHY,
        17.50,
        5,
        "9780316548182",
        "Nelson Mandela chronicles his life from childhood through decades of anti-apartheid struggle, twenty-seven years of imprisonment, and presidency.",
    ),
    (
        "Educated",
        "Tara Westover",
        BookCategory.BIOGRAPHY,
        15.60,
        6,
        "9780399590504",
        "A woman raised in an isolated survivalist family pursues an education that transforms her understanding of home, family, and self.",
    ),
    # Category 9: Psychology (3)
    (
        "Thinking, Fast and Slow",
        "Daniel Kahneman",
        BookCategory.PSYCHOLOGY,
        16.00,
        5,
        "9780374533557",
        "A Nobel laureate reveals two systems that drive how we think — fast, intuitive thinking and slow, deliberate reasoning — and how they shape our decisions.",
    ),
    (
        "Man's Search for Meaning",
        "Viktor E. Frankl",
        BookCategory.PSYCHOLOGY,
        14.00,
        6,
        "9780807014271",
        "A psychiatrist's memoir of surviving Nazi concentration camps and his theory that finding meaning in suffering is the primary human motivation.",
    ),
    (
        "Influence: The Psychology of Persuasion",
        "Robert B. Cialdini",
        BookCategory.PSYCHOLOGY,
        15.99,
        5,
        "9780061241895",
        "A groundbreaking exploration of the six universal principles of persuasion and how understanding them can protect us from manipulation and improve our influence.",
    ),
    # Category 10: Mathematics (3)
    (
        "The Art of Statistics",
        "David Spiegelhalter",
        BookCategory.MATHEMATICS,
        17.00,
        4,
        "9781541618510",
        "A clear guide to understanding data, interpreting statistics, and making sense of the numbers that shape our world — from medical trials to weather forecasts.",
    ),
    (
        "How Not to Be Wrong",
        "Jordan Ellenberg",
        BookCategory.MATHEMATICS,
        16.00,
        5,
        "9780143127536",
        "A mathematician shows how mathematical thinking permeates everyday life, from politics and medicine to love and war, revealing the hidden math in the world.",
    ),
    (
        "The Joy of x",
        "Steven Strogatz",
        BookCategory.MATHEMATICS,
        14.99,
        5,
        "9780544105850",
        "A celebrated mathematician guides readers through the beauty and relevance of mathematics, from calculus to infinity, in short, accessible chapters.",
    ),
]


# (book title, email, issue_date, due_date, return_date, fine_amount, fine_paid)
ISSUE_RECORDS: list[
    tuple[str, str, datetime, datetime, datetime | None, float, bool]
] = [
    ("Clean Code", "alice@example.com", _dt(2026, 10, 20), _dt(2026, 11, 3), None, 0.0, False),
    (
        "Thinking, Fast and Slow",
        "bob@example.com",
        _dt(2026, 10, 18),
        _dt(2026, 11, 1),
        None,
        0.0,
        False,
    ),
    ("Atomic Habits", "carol@example.com", _dt(2026, 10, 12), _dt(2026, 10, 26), None, 0.0, False),
    ("Cosmos", "david@example.com", _dt(2026, 10, 22), _dt(2026, 11, 5), None, 0.0, False),
    ("The Lean Startup", "farhan@example.com", _dt(2026, 10, 15), _dt(2026, 10, 29), None, 0.0, False),
    ("Educated", "grace@example.com", _dt(2026, 10, 25), _dt(2026, 11, 8), None, 0.0, False),
    (
        "The Joy of x",
        "hassan@example.com",
        _dt(2026, 10, 24),
        _dt(2026, 11, 7),
        None,
        0.0,
        False,
    ),
    (
        "Pride and Prejudice",
        "isabel@example.com",
        _dt(2026, 10, 19),
        _dt(2026, 11, 2),
        None,
        0.0,
        False,
    ),
    ("Sapiens: A Brief History of Humankind", "jonas@example.com", _dt(2026, 10, 8), _dt(2026, 10, 22), None, 0.0, False),
    ("1984", "keira@example.com", _dt(2026, 10, 26), _dt(2026, 11, 9), None, 0.0, False),
    (
        "The Great Gatsby",
        "alice@example.com",
        _dt(2026, 9, 1),
        _dt(2026, 9, 15),
        _dt(2026, 9, 14),
        0.0,
        True,
    ),
    (
        "To Kill a Mockingbird",
        "bob@example.com",
        _dt(2026, 9, 5),
        _dt(2026, 9, 19),
        _dt(2026, 9, 25),
        120.0,
        True,
    ),
    (
        "Deep Work",
        "carol@example.com",
        _dt(2026, 9, 10),
        _dt(2026, 9, 24),
        _dt(2026, 10, 2),
        160.0,
        False,
    ),
    (
        "The Alchemist",
        "david@example.com",
        _dt(2026, 9, 12),
        _dt(2026, 9, 26),
        _dt(2026, 9, 26),
        0.0,
        True,
    ),
    (
        "Steve Jobs",
        "emma@example.com",
        _dt(2026, 9, 20),
        _dt(2026, 10, 4),
        _dt(2026, 10, 9),
        100.0,
        False,
    ),
]


# (book title, email, reservation_date, status)
RESERVATIONS: list[tuple[str, str, datetime, Status]] = [
    ("Man's Search for Meaning", "emma@example.com", _dt(2026, 10, 28), Status.PENDING),
    ("Atomic Habits", "bob@example.com", _dt(2026, 10, 29), Status.PENDING),
    ("Python Crash Course", "carol@example.com", _dt(2026, 10, 30), Status.PENDING),
    ("Clean Code", "david@example.com", _dt(2026, 10, 27), Status.PENDING),
    ("How Not to Be Wrong", "isabel@example.com", _dt(2026, 10, 31), Status.PENDING),
    ("Educated", "alice@example.com", _dt(2026, 10, 20), Status.APPROVED),
    ("Sapiens: A Brief History of Humankind", "emma@example.com", _dt(2026, 10, 22), Status.APPROVED),
    ("The Pragmatic Programmer", "farhan@example.com", _dt(2026, 10, 21), Status.APPROVED),
    ("Influence: The Psychology of Persuasion", "grace@example.com", _dt(2026, 10, 18), Status.REJECTED),
    ("Zero to One", "hassan@example.com", _dt(2026, 10, 19), Status.REJECTED),
]


def _masked_url() -> str:
    url = make_url(settings.DATABASE_URL)
    if url.password:
        return str(url.set(password="***"))
    return str(url)


def _is_local(url_text: str) -> bool:
    url = make_url(url_text)
    return (url.host or "").lower() in LOCAL_HOSTS


async def _get_or_create_user(session: Any, spec: dict[str, Any]) -> tuple[User, bool]:
    existing = (
        await session.exec(select(User).where(User.email == spec["email"]))
    ).first()
    if existing is not None:
        return existing, False

    # Use role-specific password from environment variables
    if spec["role"] == Role.LIBRARIAN:
        password = os.environ.get("SEED_LIBRARIAN_PASSWORD")
    else:
        password = os.environ.get("SEED_MEMBER_PASSWORD")

    if not password:
        env_var = (
            "SEED_LIBRARIAN_PASSWORD"
            if spec["role"] == Role.LIBRARIAN
            else "SEED_MEMBER_PASSWORD"
        )
        print(
            f"Error: {env_var} environment variable is not set. "
            f"Cannot create user '{spec['email']}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    user = User(
        username=spec["username"],
        email=spec["email"],
        first_name=spec["first_name"],
        last_name=spec["last_name"],
        hash_password=get_password_hash(password),
        role=spec["role"],
        phone_number=spec["phone_number"],
    )
    session.add(user)
    await session.flush()
    return user, True


async def _get_or_create_book(
    session: Any, spec: tuple[str, str, BookCategory, float, int, str, str]
) -> tuple[Book, bool]:
    title, author, category, price, total_copies, isbn, description = spec

    existing = (
        await session.exec(
            select(Book).where(Book.title == title, Book.author == author)
        )
    ).first()
    if existing is not None:
        return existing, False

    book = Book(
        title=title,
        author=author,
        category=category,
        description=description,
        price=price,
        total_copies=total_copies,
        available_copies=total_copies,
        cover_image=f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg",
    )
    session.add(book)
    await session.flush()
    return book, True


async def seed(dry_run: bool = False) -> dict[str, int]:
    stats = {
        "users_created": 0,
        "books_created": 0,
        "issues_created": 0,
        "reservations_created": 0,
        "skipped": 0,
    }

    # In dry-run mode, skip table creation to avoid any persistent changes.
    # The user should initialize the schema separately before running the seed.
    if not dry_run:
        await create_db_and_tables()

    async with async_session() as session:
        users: dict[str, User] = {}
        for spec in USERS:
            user, created = await _get_or_create_user(session, spec)
            users[spec["email"]] = user
            stats["users_created" if created else "skipped"] += 1

        books: dict[str, Book] = {}
        for spec in BOOKS:
            book, created = await _get_or_create_book(session, spec)
            books[spec[0]] = book
            stats["books_created" if created else "skipped"] += 1

        for (
            title,
            email,
            issue_date,
            due_date,
            return_date,
            fine,
            fine_paid,
        ) in ISSUE_RECORDS:
            book = books[title]
            user = users[email]

            existing = (
                await session.exec(
                    select(IssueRecord).where(
                        IssueRecord.book_id == book.id,
                        IssueRecord.user_id == user.id,
                        IssueRecord.issue_date == issue_date,
                    )
                )
            ).first()
            if existing is not None:
                stats["skipped"] += 1
                continue

            status = "returned" if return_date is not None else "issued"
            session.add(
                IssueRecord(
                    book_id=book.id,
                    user_id=user.id,
                    issue_date=issue_date,
                    due_date=due_date,
                    return_date=return_date,
                    status=status,
                    fine_amount=fine,
                    fine_paid=fine_paid,
                )
            )
            if status == "issued":
                book.available_copies = max(0, book.available_copies - 1)
            stats["issues_created"] += 1

        for title, email, reservation_date, reservation_status in RESERVATIONS:
            book = books[title]
            user = users[email]

            existing = (
                await session.exec(
                    select(Reservation).where(
                        Reservation.book_id == book.id,
                        Reservation.user_id == user.id,
                        Reservation.reservation_date == reservation_date,
                    )
                )
            ).first()
            if existing is not None:
                stats["skipped"] += 1
                continue

            session.add(
                Reservation(
                    book_id=book.id,
                    user_id=user.id,
                    reservation_date=reservation_date,
                    status=reservation_status,
                )
            )
            stats["reservations_created"] += 1

        if dry_run:
            await session.rollback()
        else:
            await session.commit()

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed the Library Management database."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Insert inside a transaction, then roll back.",
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow running against a non-local database (explicit opt-in).",
    )
    args = parser.parse_args()

    # The app engine uses echo=True; silence SQL logging for readable seed output.
    engine.sync_engine.echo = False

    target = _masked_url()
    print(f"Database target: {target}")

    if not _is_local(settings.DATABASE_URL) and not args.allow_remote:
        print(
            "Refusing to write: the configured database host is not local.\n"
            "If this is a disposable development database, re-run with --allow-remote.",
            file=sys.stderr,
        )
        return 2

    stats = asyncio.run(seed(dry_run=args.dry_run))

    print("\nSeed summary:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    if args.dry_run:
        print("\nDry run: all changes were rolled back.")
        print("Note: schema initialization was skipped in dry-run mode.")

    print("\nSeed accounts use passwords from environment variables:")
    print("  Librarian accounts: SEED_LIBRARIAN_PASSWORD")
    print("  Member accounts:    SEED_MEMBER_PASSWORD")
    print("Librarian login: librarian@library.dev")
    print("Member login:    alice@example.com")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
