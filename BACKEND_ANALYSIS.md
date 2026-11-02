# Library Management Backend — Complete Analysis, Data Initialization & Frontend Integration Guide

**Project:** `Phitron/library_Management`
**Backend root:** `backend/`
**Analysis date:** 2026-11-01
**Report files:** `data.md` (canonical full review), `BACKEND_ANALYSIS.md` (identical deliverable copy)

> **Safety statement**
> The configured `DATABASE_URL` points at a remote Supabase Postgres instance. That
> database was **not written to, migrated, truncated, or reset** during this work.
> All write verification was performed against a disposable **local** PostgreSQL 16
> container (`127.0.0.1:55432`) created for this review and removed afterwards.
> No `.env` value, credential, connection setting, or environment variable was changed.
> Secrets are redacted throughout this document.

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Backend architecture overview](#2-backend-architecture-overview)
3. [Complete API endpoint inventory](#3-complete-api-endpoint-inventory)
4. [Database schema and relationships](#4-database-schema-and-relationships)
5. [Authentication and authorization](#5-authentication-and-authorization)
6. [Why the application currently has no data](#6-why-the-application-currently-has-no-data)
7. [Recommended data initialization strategy](#7-recommended-data-initialization-strategy)
8. [Frontend API integration reference](#8-frontend-api-integration-reference)
9. [Identified problems and severity](#9-identified-problems-and-severity)
10. [Changes applied during this review](#10-changes-applied-during-this-review)
11. [Verification results](#11-verification-results)
12. [Appendix — commands, accounts, files](#12-appendix--commands-accounts-files)
13. [Supabase connection investigation — 2026-11-02](#13-supabase-connection-investigation--2026-11-02)

---

## 1. Executive summary

The backend is a small FastAPI + SQLModel + async SQLAlchemy application with **16 real
endpoints**, **4 database tables**, **no migrations**, **no test suite**, and **no seed
mechanism before this review**. It uses JWT bearer authentication with two roles
(`librarian`, `member`).

Key findings:

| # | Finding | Impact |
|---|---------|--------|
| 1 | The configured remote database is **unreachable** (`tenant/user ... not found`, project host `NXDOMAIN`). | The app cannot create tables at startup or serve data in this environment. See §13 for the 2026-11-02 re-investigation. |
| 2 | At review start, there was **no seed infrastructure** and the database contained no application data. | Even with a reachable DB, the UI would show empty collections. **Addressed by `backend/app/seed.py`.** |
| 3 | The frontend **does not call any API** (`fetch()` has no URL), and routes for `/books`, `/categories`, `/about` do not exist. | This is a frontend integration gap, not a backend data bug. |
| 4 | `GET /books/all` requires authentication. | An anonymous homepage fetch gets `401`, which can look like "no data". |
| 5 | Five runtime bugs broke real endpoints. | `/books/issues/my` and password change returned `500`; two admin routes were unreachable; issued books were stored with an invisible status. **All fixed.** |
| 6 | No CORS middleware existed. | A browser frontend on another port would be blocked. **Fixed for localhost.** |
| 7 | No pagination, filtering, searching, sorting, dashboard, authors, publishers, or user-management endpoints exist. | These features must be done client-side or are unavailable. |

A production-quality, **idempotent seed script** was added at
`backend/app/seed.py`. It creates 14 users, 30 books (3 per category), 15 issue records,
and 10 reservations, and it refuses to run against a non-local database unless explicitly
opted in. All 30 books use verified Open Library cover URLs; see `BOOK_COVER_URLS.md`.

### 1.1 30-book dataset update (this task)

| Item | Result |
|------|--------|
| Book definitions | **30** (3 per category across 10 categories) |
| Categories represented | **10 / 10** |
| Verified cover URLs | **30 / 30** returned `HTTP 200 image/jpeg` |
| URLs requiring manual replacement | **0** |
| Existing users / issues / reservations | **14 / 15 / 10**, unchanged |
| Seed idempotency | Run 1 created 14/30/15/10; run 2 created 0 and skipped 69 |
| Inventory consistency | **0 mismatches** (`available = total − active issues`) |
| FK integrity | **0 orphan issues/reservations** |
| Non-destructive test | Unrelated user/book/issue/reservation survived a rerun unchanged |
| Local verification | Dry run, fresh seed, rerun, API smoke test, issue/return inventory test |
| Cover evidence | `BOOK_COVER_URLS.md` |
| Configured remote database | **Not contacted for writes** |

---

## 2. Backend architecture overview

### 2.1 Stack

| Layer | Technology | Version / detail |
|-------|------------|------------------|
| Language | Python | `>=3.13.1` |
| Web framework | FastAPI | `0.160.0` |
| ORM | SQLModel | `>=0.0.47` |
| DB toolkit | SQLAlchemy async | `2.1.6` |
| Driver | psycopg (binary) | `>=3.3.6`, async |
| Database | PostgreSQL | Supabase-hosted (remote) |
| Password hashing | pwdlib + Argon2 | `>=0.3.1` |
| JWT | PyJWT | `2.15.1`, HS256 |
| Settings | pydantic-settings | `2.16.1` |
| Forms | python-multipart | `>=0.0.32` |
| Lint | Ruff | dev dependency |

### 2.2 File tree (backend)

```text
backend/
├── .env                        # DATABASE_URL, SECRET_KEY (values not printed)
├── pyproject.toml
├── uv.lock
└── app/
    ├── main.py                 # FastAPI app, lifespan, CORS, router registration
    ├── seed.py                 # NEW: idempotent development seed script
    ├── api/routers/
    │   ├── auth.py             # register, login, edit profile, change password
    │   ├── books.py            # list/detail books, reservations, my issues
    │   └── admin.py            # librarian book CRUD, issue, return, fine payment
    ├── core/
    │   ├── config.py           # Settings (DATABASE_URL, SECRET_KEY, JWT settings)
    │   ├── database.py         # async engine, session factory, get_db, create_all
    │   └── security.py         # password hash/verify, JWT creation
    ├── dependencies/auth.py    # OAuth2 bearer scheme, get_current_user
    ├── models/
    │   ├── user.py             # User, Role
    │   ├── books.py            # Book, BookCategory
    │   ├── issue_records.py    # IssueRecord
    │   └── reservations.py     # Reservation, Status
    └── schemas/
        ├── auth.py             # UserCreate, Token
        ├── book.py             # Create_Books, Update_Books, IssueBook
        └── user.py             # UserResponse, UpdateUser, PasswordUpdate
```

There is **no** `services/`, `repositories/`, `crud/`, `middleware/` package, `alembic/`,
`tests/`, `scripts/`, or `docker-compose.yml`. Business logic lives directly in the routers.

### 2.3 Request flow

```text
HTTP request
  → FastAPI router (app/api/routers/*.py)
      → dependency: get_db() → AsyncSession (app/core/database.py)
      → dependency: get_current_user() → decode JWT, load User (app/dependencies/auth.py)
      → inline role check (user.role != Role.LIBRARIAN)
      → SQLModel select/insert/update/delete
      → response model serialization (SQLModel/Pydantic)
```

### 2.4 Application startup

`app/main.py` uses an async lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    await engine.dispose()
```

`create_db_and_tables()` runs `SQLModel.metadata.create_all(...)`. This is the **only**
schema mechanism: there are **no Alembic migrations**. `create_all` creates missing tables
and enum types, but it **never alters existing tables**. Schema changes require manual SQL
or a migration tool added later.

Because the DB is contacted during startup, an unreachable database prevents the server
from starting cleanly.

### 2.5 Configuration

`app/core/config.py`:

| Setting | Required | Default | Source |
|---------|----------|---------|--------|
| `DATABASE_URL` | yes | — | `.env` / environment |
| `SECRET_KEY` | yes | — | `.env` / environment |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `60` | code default |
| `ALGORITHM` | no | `HS256` | code default |

Only `DATABASE_URL` and `SECRET_KEY` are present in `.env`. Environment variables take
precedence over `.env` via pydantic-settings. `extra="ignore"` means unknown variables are
ignored.

### 2.6 Database session management

`app/core/database.py`:

- One module-level `AsyncEngine` created from `settings.DATABASE_URL`, with `echo=True`
  (all SQL is logged at INFO level).
- `async_sessionmaker(..., class_=AsyncSession, expire_on_commit=False)`.
- `get_db()` yields a session per request.
- `db_Dependency = Annotated[AsyncSession, Depends(get_db)]`.

There is no explicit transaction helper; each endpoint calls `await db.commit()` itself.

### 2.7 Routers registered

`app/main.py` registers three routers with no global API prefix:

| Router | Prefix | Tags |
|--------|--------|------|
| `auth.router` | `/auth` | Authentication |
| `books.router` | `/books` | Books |
| `admin.router` | `/admin` | admin |

There is no `/api` or `/v1` prefix. The OpenAPI docs are at `/docs`, `/redoc`, and
`/openapi.json`.

### 2.8 Middleware / exception handling

- Only the new CORS middleware (added during this review) and FastAPI defaults.
- No custom exception handlers, no request logging middleware, no rate limiting,
  no trusted-host middleware, no GZip.
- Errors are raised as `fastapi.HTTPException`; validation errors use FastAPI's default
  `422` shape.

---

## 3. Complete API endpoint inventory

Exactly **16** endpoints exist. Paths below are the paths **after** the route fixes
described in §10. Nothing outside this list exists.

### 3.1 Summary table

| # | Method | Path | Auth | Role | Purpose |
|---|--------|------|------|------|---------|
| 1 | POST | `/auth/register` | No | — | Create account |
| 2 | POST | `/auth/login` | No | — | Obtain JWT |
| 3 | PATCH | `/auth/edituser` | Yes | any | Update own profile |
| 4 | PATCH | `/auth/changepassword` | Yes | any | Change own password |
| 5 | GET | `/books/all` | Yes | any | List all books |
| 6 | GET | `/books/{book_id}` | Yes | any | Book detail |
| 7 | POST | `/books/reserve/{book_id}` | Yes | any | Reserve a book |
| 8 | PUT | `/books/reserve/cancel/{reservation_id}` | Yes | any | Cancel own reservation |
| 9 | GET | `/books/reservation/my` | Yes | any | Own reservations |
| 10 | GET | `/books/issues/my` | Yes | any | Own active checkouts |
| 11 | POST | `/admin/add_book` | Yes | librarian | Create book |
| 12 | PATCH | `/admin/update_book/{book_id}` | Yes | librarian | Update book |
| 13 | DELETE | `/admin/delete_book/{book_id}` | Yes | librarian | Delete book |
| 14 | POST | `/admin/issue_record` | Yes | librarian | Check out a book |
| 15 | PATCH | `/admin/return_book/{issue_id}` | Yes | librarian | Return a book |
| 16 | PATCH | `/admin/fine/pay/{issue_id}` | Yes | librarian | Mark fine paid |

Authentication is `Authorization: Bearer <jwt>` for every protected endpoint.
"Role: any" means any active authenticated user (member or librarian).

> **Important:** there is no `GET /auth/me`, no `GET /admin/users`, no dashboard endpoint,
> no search endpoint, no category/author/publisher endpoints, and no admin list of all
> issue records or reservations.

---

### 3.2 Authentication endpoints

#### 1. `POST /auth/register`

| Field | Value |
|-------|-------|
| Purpose | Register a user |
| Auth | None |
| Role | — |
| Request body | JSON `UserCreate` |
| Success | `201` → `UserResponse` |
| Errors | `409` duplicate username/email, `422` validation |
| Tables | `user` |

Request body:

| Field | Type | Required | Constraints / default |
|-------|------|----------|-----------------------|
| `first_name` | string | yes | — |
| `last_name` | string | yes | — |
| `username` | string | yes | unique (checked in code) |
| `email` | email string | yes | normalized to lowercase; unique |
| `password` | string | yes | hashed with Argon2 |
| `role` | `"librarian"` \| `"member"` | no | default `"member"` |

> **Security warning:** the client may submit `"role": "librarian"` and the account is
> created as a librarian. See §9, finding H1.

Response `201`:

```json
{
  "first_name": "Sample",
  "last_name": "Reader",
  "username": "sample_reader",
  "email": "sample_reader@example.com",
  "role": "member",
  "is_active": true,
  "phone_number": null
}
```

Note: the response does **not** include `id`. The frontend cannot get the new user's ID
from registration; it must log in and decode the JWT (which contains `id`).

Duplicate check is `username == new_user.username OR email == lowercased email`.
Race conditions can still produce a DB unique-index error (`500`).

---

#### 2. `POST /auth/login`

| Field | Value |
|-------|-------|
| Purpose | Authenticate and obtain JWT |
| Auth | None |
| Request body | `application/x-www-form-urlencoded` (`OAuth2PasswordRequestForm`) |
| Success | `200` → `Token` |
| Errors | `401` incorrect username/password, `422` missing form fields |
| Tables | `user` |

Form fields: `username` (required), `password` (required). OAuth2 fields `grant_type`,
`scope`, `client_id`, `client_secret` are accepted but ignored.

Response `200`:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

JWT payload (decoded):

```json
{
  "sub": "alice",
  "id": 3,
  "role": "member",
  "exp": 1793557607
}
```

- Algorithm: `HS256`
- Lifetime: `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60 minutes)
- No refresh token, no logout/revocation.
- **Inactive users can still log in** because `login_user` does not check `is_active`;
  protected endpoints later reject them with `400 Inactive user`.

Wrong credentials return:

```json
{ "detail": "Incorrect username or password" }
```

with header `WWW-Authenticate: Bearer`.

---

#### 3. `PATCH /auth/edituser`

| Field | Value |
|-------|-------|
| Purpose | Update the current user's profile |
| Auth | Bearer |
| Role | any |
| Request body | JSON `UpdateUser` |
| Success | `200` → `UserResponse` |
| Errors | `401` invalid/expired token, `400` inactive, `422` invalid email, `500` duplicate email |
| Tables | `user` |

Body (all optional, `exclude_unset=True`):

| Field | Type | Notes |
|-------|------|-------|
| `first_name` | string | |
| `last_name` | string | |
| `email` | email string | **not lowercased** and **no uniqueness check** → duplicate raises `500` |
| `phone_number` | string | |

`username`, `role`, and `is_active` cannot be changed here.

---

#### 4. `PATCH /auth/changepassword`

| Field | Value |
|-------|-------|
| Purpose | Change own password |
| Auth | Bearer |
| Role | any |
| Request body | JSON `PasswordUpdate` |
| Success | `200` → `{ "message": "Password updated successfully" }` |
| Errors | `401` wrong current password or invalid token, `400` inactive, `422` |
| Tables | `user` |

Body: `{ "current_password": "...", "new_password": "..." }`.

No password-strength validation exists beyond Pydantic string typing.

> This endpoint previously raised `500 AttributeError` due to a typo; it is fixed (§10).

---

### 3.3 Book endpoints

#### 5. `GET /books/all`

| Field | Value |
|-------|-------|
| Purpose | List every book |
| Auth | Bearer |
| Role | any |
| Query params | none (unknown params are ignored) |
| Success | `200` → `Book[]` |
| Errors | `401` missing/invalid token, `400` inactive |
| Tables | `book` |

- Returns **all** rows, no pagination, filtering, searching, or sorting.
- No `ORDER BY`; do not rely on a stable order.
- An anonymous request returns `401 {"detail":"Not authenticated"}`.
- Seeded dataset returns 30 items.

`Book` response shape (real):

```json
{
  "id": 1,
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "category": "fiction",
  "description": "A mysterious millionaire throws lavish parties on Long Island while chasing a lost love, in a portrait of ambition and the American Dream.",
  "price": 12.99,
  "total_copies": 6,
  "available_copies": 6,
  "cover_image": "https://covers.openlibrary.org/b/isbn/9780020198819-L.jpg",
  "created_at": "2026-11-01T17:26:46.621813Z"
}
```

---

#### 6. `GET /books/{book_id}`

| Field | Value |
|-------|-------|
| Purpose | Get one book |
| Auth | Bearer |
| Role | any |
| Path param | `book_id` integer |
| Success | `200` → `Book` |
| Errors | `404` book not found, `422` non-integer ID, `401` |
| Tables | `book` |

Example errors:

```json
{ "detail": "Book not found" }
```

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "book_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "not-an-int"
    }
  ]
}
```

> **Route shadowing:** because this route is declared before `/books/search` would be,
> `GET /books/search` matches `{book_id}` and returns `422`, not `404`. Any future search
> route must be declared before `/{book_id}` or use a distinct prefix.

---

#### 7. `POST /books/reserve/{book_id}`

| Field | Value |
|-------|-------|
| Purpose | Create a reservation for the current user |
| Auth | Bearer |
| Role | any |
| Path param | `book_id` integer |
| Request body | none |
| Success | `201` → `{ "message": "Book reserved successfully" }` |
| Errors | `404` book not found, `401`, `422` |
| Tables | `book`, `reservation`, `user` |

Behavior and gaps:

- Does **not** check `available_copies`.
- Does **not** prevent duplicate reservations (same user + book can be reserved repeatedly).
- Does **not** decrement inventory or hold a copy.
- Reservation is created with status `PENDING`.
- Response contains **no reservation ID**, so the client must call
  `GET /books/reservation/my` to obtain it before cancelling.

---

#### 8. `PUT /books/reserve/cancel/{reservation_id}`

| Field | Value |
|-------|-------|
| Purpose | Cancel own reservation |
| Auth | Bearer |
| Role | any |
| Path param | `reservation_id` integer |
| Success | `200` → `{ "message": "Reservation cancelled successfully" }` |
| Errors | `404` not found, `403` not the owner, `401`, `422` |
| Tables | `reservation` |

Cancellation is a soft status change: `status = "REJECTED"`. The row is not deleted.
A librarian **cannot** cancel another user's reservation through this endpoint
(it returns `403`), and there is no admin override endpoint.

---

#### 9. `GET /books/reservation/my`

| Field | Value |
|-------|-------|
| Purpose | List current user's reservations |
| Auth | Bearer |
| Role | any |
| Success | `200` → `Reservation[]` |
| Errors | `401`, `400` inactive |
| Tables | `reservation` |

Real response item:

```json
{
  "id": 6,
  "book_id": 25,
  "user_id": 3,
  "reservation_date": "2026-10-20T09:00:00Z",
  "status": "APPROVED"
}
```

Status values are uppercase: `PENDING`, `APPROVED`, `REJECTED`.
There is no filter by status and no pagination.

---

#### 10. `GET /books/issues/my`

| Field | Value |
|-------|-------|
| Purpose | List current user's active checkouts |
| Auth | Bearer |
| Role | any |
| Success | `200` → `IssueRecord[]` where `status == "issued"` |
| Errors | `401`, `400` inactive |
| Tables | `issuerecord` |

Real response item:

```json
{
  "id": 1,
  "book_id": 17,
  "user_id": 3,
  "issue_date": "2026-10-20T09:00:00Z",
  "due_date": "2026-11-03T09:00:00Z",
  "return_date": null,
  "status": "issued",
  "fine_amount": 0.0,
  "fine_paid": false
}
```

- Only active (`"issued"`) records are returned; returned history is **not exposed**.
- No book title/author join; the client must resolve `book_id` via `GET /books/{id}`
  or the `/books/all` list.
- This endpoint previously returned `500` because of a missing `await`; fixed (§10).

---

### 3.4 Admin endpoints

All admin endpoints require a librarian. Role failures are inconsistent:
`add_book`, `update_book`, `delete_book`, `issue_record` return **`401`**;
`return_book` and `fine/pay` return **`403`**.

#### 11. `POST /admin/add_book`

| Field | Value |
|-------|-------|
| Purpose | Create a book |
| Auth | Bearer |
| Role | librarian |
| Request body | `application/x-www-form-urlencoded` or `multipart/form-data` (`Form`) |
| Success | `201` → `{ "message": "Book added successfully" }` |
| Errors | `401` not librarian, `422` validation |
| Tables | `book` |

Form fields (`Create_Books`):

| Field | Type | Required | Constraints / default |
|-------|------|----------|-----------------------|
| `title` | string | yes | max 150 |
| `author` | string | yes | max 150 |
| `description` | string | yes | max 220 |
| `price` | float | no | default `0`, `>= 0` |
| `total_copies` | int | no | default `1`, `>= 0` |
| `category` | enum value | no | default `"biography"` |

- `available_copies` is set to `total_copies` on creation.
- `cover_image` is **not** accepted; new books have `cover_image = null`.
- The request is **not JSON**. A JSON body returns `422`.
- Enum values are lowercase: `fiction`, `mystery`, `thriller`, `romance`,
  `science_fiction`, `fantasy`, `biography`, `history`, `science_technology`, `self_help`.
- The response contains no book ID; re-fetch `/books/all` to find it.

---

#### 12. `PATCH /admin/update_book/{book_id}`

| Field | Value |
|-------|-------|
| Purpose | Update a book |
| Auth | Bearer |
| Role | librarian |
| Path param | `book_id` integer |
| Request body | JSON `Update_Books` (all optional) |
| Success | `200` → `{ "message": "Book updated successfully", "book_id": 17 }` |
| Errors | `401`, `404`, `400` no fields / total below checked-out, `422` |
| Tables | `book` |

Fields: `title`, `author`, `description`, `price`, `total_copies`, `category`.
`cover_image` and `available_copies` cannot be updated.

Behavior:

- `exclude_unset=True` and `exclude_none=True`; sending `null` does not clear a field.
- If `total_copies` changes, `available_copies` is recalculated as
  `new_total - (old_total - old_available)`.
- If `new_total < checked_out`, returns `400 Total copies cannot be less than checked-out copies`.
- Empty body returns `400 No fields provided for update`.

---

#### 13. `DELETE /admin/delete_book/{book_id}`

| Field | Value |
|-------|-------|
| Purpose | Delete a book |
| Auth | Bearer |
| Role | librarian |
| Path param | `book_id` integer |
| Success | `204` no content |
| Errors | `401`, `404`, `500` if referenced by issue/reservation rows |
| Tables | `book` |

- Hard delete.
- Foreign keys from `issuerecord` and `reservation` have **no `ON DELETE CASCADE`**, so
  deleting a book with history raises an integrity error → `500`.
- The route previously had a missing leading slash (`/admindelete_book/...`); fixed (§10).

---

#### 14. `POST /admin/issue_record`

| Field | Value |
|-------|-------|
| Purpose | Check out a book to a user |
| Auth | Bearer |
| Role | librarian |
| Request body | JSON `IssueBook` |
| Success | `201` → `{ "message": "Book Issued successfully" }` |
| Errors | `401`, `404` book/user, `400` no copies, `422` |
| Tables | `issuerecord`, `book`, `user`, `reservation` |

Body:

```json
{ "book_id": 5, "user_id": 7 }
```

Behavior:

- Verifies book and user exist.
- Requires `book.available_copies > 0`; otherwise `400 No Copies Available`.
- Decrements `available_copies` by 1.
- Creates an `IssueRecord` with:
  - `issue_date = now (UTC)`
  - `due_date = issue_date + 14 days`
  - `status = "issued"` (fixed; previously incorrectly `"PENDING"`)
  - `fine_amount = 0.0`, `fine_paid = false`
- If a `PENDING` reservation exists for the same book+user, it is set to `APPROVED`.
- No duplicate-active-checkout check: the same user can borrow the same book multiple times
  if copies remain.
- Response has no issue ID; the member can read `/books/issues/my`.

---

#### 15. `PATCH /admin/return_book/{issue_id}`

| Field | Value |
|-------|-------|
| Purpose | Return a checked-out book |
| Auth | Bearer |
| Role | librarian |
| Path param | `issue_id` integer |
| Request body | none |
| Success | `200` → `{ "message": "Book returned successfully", "fine_amount": 200.0 }` |
| Errors | `401`, `403`, `404`, `409` already returned |
| Tables | `issuerecord`, `book` |

Behavior:

- Uses `SELECT ... FOR UPDATE` on the issue record.
- Rejects if `return_date` is already set or `status == "returned"` → `409`.
- Computes fine as `max(0, (return_date.date() - due_date.date()).days) * 20.0`.
- Increments `available_copies` by 1, guarded by `available_copies < total_copies`;
  if the guarded update does not affect exactly one row, rolls back and returns `409`.
- Sets `return_date`, `status = "returned"`, `fine_amount`.
- Does **not** change `fine_paid`; a returned fine starts unpaid.

---

#### 16. `PATCH /admin/fine/pay/{issue_id}`

| Field | Value |
|-------|-------|
| Purpose | Mark a fine as paid |
| Auth | Bearer |
| Role | librarian |
| Path param | `issue_id` integer |
| Success | `200` → `{ "message": "Fine paid successfully" }` |
| Errors | `401`, `403`, `404` |
| Tables | `issuerecord` |

- Sets `fine_paid = true`.
- Does **not** check that the book was returned, that a fine exists, or that it is unpaid.
- Route was previously malformed (`/adminfine/pay/{issue_id}`) and typed `issue_id` as
  `str`, causing a PostgreSQL type error; fixed (§10).

---

## 4. Database schema and relationships

### 4.1 Entity-relationship overview

```text
┌────────────────────┐
│ user               │
│ PK id              │
│ UQ email           │
│ UQ username        │
│ role: LIBRARIAN|MEMBER
└─────────┬──────────┘
          │ 1
          │
          │ N
┌─────────▼──────────┐        ┌────────────────────┐
│ issuerecord        │  N   1 │ book               │
│ PK id              ├───────►│ PK id              │
│ FK user_id         │        │ category enum      │
│ FK book_id         │        │ total/available    │
│ status "issued"/"returned"  │ created_at         │
└────────────────────┘        └─────────▲──────────┘
          │                             │
          │ N                         1 │
┌─────────▼──────────┐                  │
│ reservation        │──────────────────┘
│ PK id              │  FK book_id
│ FK user_id         │
│ status PENDING|APPROVED|REJECTED
└────────────────────┘
```

Tables: `user`, `book`, `issuerecord`, `reservation`.
There are **no** category, author, publisher, fine, or audit tables. `author` is a plain
string on `book`; `category` is a PostgreSQL enum.

### 4.2 `user`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | serial integer | no | sequence | PK |
| `email` | varchar | no | — | unique index `ix_user_email` |
| `username` | varchar | no | — | unique index `ix_user_username` |
| `first_name` | varchar | no | — | |
| `last_name` | varchar | no | — | |
| `hash_password` | varchar | no | — | Argon2 hash |
| `is_active` | boolean | no | Python `True` | no server default |
| `role` | enum `role` | no | Python `MEMBER` | DB values: `LIBRARIAN`, `MEMBER` |
| `phone_number` | varchar | yes | null | |

No `created_at` / `updated_at`.

### 4.3 `book`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | serial integer | no | sequence | PK |
| `title` | varchar | no | — | not unique |
| `author` | varchar | no | — | free text, not a FK |
| `category` | enum `bookcategory` | no | Python `FICTION` | 10 DB values (names) |
| `description` | varchar | no | — | API max 220, DB unlimited |
| `price` | double precision | no | — | float, not Decimal |
| `total_copies` | integer | no | Python `5` | no server default |
| `available_copies` | integer | no | Python `3` | no check constraint |
| `cover_image` | varchar | yes | null | URL string |
| `created_at` | timestamptz | no | Python UTC now | no server default |

No unique constraint on `(title, author)` and no index on `category`.

### 4.4 `issuerecord`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | serial integer | no | sequence | PK |
| `book_id` | integer | no | — | FK → `book.id`, indexed |
| `user_id` | integer | no | — | FK → `user.id`, indexed |
| `issue_date` | timestamptz | no | Python UTC now | |
| `due_date` | timestamptz | no | — | required |
| `return_date` | timestamptz | yes | null | |
| `status` | varchar | no | `"issued"` | **free-form string**, not an enum |
| `fine_amount` | double precision | no | `0.0` | Python `ge=0` only |
| `fine_paid` | boolean | no | `false` | |

Allowed statuses are conventions, not constraints: `"issued"` and `"returned"`.
No `created_at`/`updated_at`.

### 4.5 `reservation`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | serial integer | no | sequence | PK (typed `int` but default `None`) |
| `book_id` | integer | no | — | FK → `book.id` |
| `user_id` | integer | no | — | FK → `user.id` |
| `reservation_date` | timestamptz | no | Python UTC now | |
| `status` | enum `status` | no | Python `PENDING` | DB values: `PENDING`, `APPROVED`, `REJECTED` |

No unique constraint on `(book_id, user_id)`; duplicates are allowed.

### 4.6 Enum storage — critical for raw SQL

SQLAlchemy `Enum` stores the **enum member names**, not the lowercase API values:

| API value | Database value |
|-----------|----------------|
| `fiction` | `FICTION` |
| `science_fiction` | `SCIENCE_FICTION` |
| `self_help` | `SELF_HELP` |
| `librarian` | `LIBRARIAN` |
| `member` | `MEMBER` |
| `PENDING` | `PENDING` |
| `APPROVED` | `APPROVED` |
| `REJECTED` | `REJECTED` |

PostgreSQL enum types created by `create_all`:

- `bookcategory`: `FICTION, MYSTERY, THRILLER, ROMANCE, SCIENCE_FICTION, FANTASY,
  BIOGRAPHY, HISTORY, SCIENCE_TECHNOLOGY, SELF_HELP`
- `role`: `LIBRARIAN, MEMBER`
- `status`: `PENDING, APPROVED, REJECTED`

If you seed with raw SQL, you **must** use uppercase names (and cast, e.g.
`'FICTION'::bookcategory`). The provided seed script uses the ORM and avoids this pitfall.

### 4.7 Record creation order and dependencies

```text
1. user        (independent)
2. book        (independent)
3. issuerecord (requires user.id AND book.id)
4. reservation (requires user.id AND book.id)
```

- A book does **not** require a category, author, or publisher row: category is an enum and
  author is a string.
- Issue and reservation rows require both a user and a book.
- Deleting a user or book with dependent rows fails at the FK level (no cascade).
- There is no explicit inventory ledger; `available_copies` is mutated in place.

### 4.8 Business constraints that are *not* enforced by the database

- `available_copies` between `0` and `total_copies` (no CHECK).
- `available_copies == total_copies - active issues` (maintained by code/seed only).
- `due_date > issue_date`.
- `return_date >= issue_date`.
- Unique `(book_id, user_id)` for active issues or pending reservations.
- `fine_amount >= 0` (Pydantic `ge=0`, no DB CHECK).
- Book title/author uniqueness.

---

## 5. Authentication and authorization

### 5.1 Authentication

- Scheme: OAuth2 password flow with bearer JWT.
- Token URL advertised to Swagger: `/auth/login`.
- `OAuth2PasswordBearer(tokenUrl="/auth/login")`.
- JWT claims: `sub` (username), `id` (user ID), `role`, `exp`.
- Signature: HS256 with `SECRET_KEY`; expiry from settings (default 60 min).
- `get_current_user` decodes the token, loads the user **by username**, rejects missing
  users (`401`) and inactive users (`400`).

There is no refresh token, token blacklist, logout, password reset, email verification,
or "me" endpoint.

### 5.2 Authorization matrix

| Endpoint | Anonymous | Member | Librarian |
|----------|-----------|--------|-----------|
| `POST /auth/register` | ✅ | ✅ | ✅ |
| `POST /auth/login` | ✅ | ✅ | ✅ |
| `PATCH /auth/edituser` | ❌ 401 | ✅ own | ✅ own |
| `PATCH /auth/changepassword` | ❌ 401 | ✅ own | ✅ own |
| `GET /books/all` | ❌ 401 | ✅ | ✅ |
| `GET /books/{id}` | ❌ 401 | ✅ | ✅ |
| `POST /books/reserve/{id}` | ❌ 401 | ✅ | ✅ |
| `PUT /books/reserve/cancel/{id}` | ❌ 401 | ✅ own | ✅ own |
| `GET /books/reservation/my` | ❌ 401 | ✅ own | ✅ own |
| `GET /books/issues/my` | ❌ 401 | ✅ own | ✅ own |
| `POST /admin/add_book` | ❌ 401 | ❌ 401 | ✅ |
| `PATCH /admin/update_book/{id}` | ❌ 401 | ❌ 401 | ✅ |
| `DELETE /admin/delete_book/{id}` | ❌ 401 | ❌ 401 | ✅ |
| `POST /admin/issue_record` | ❌ 401 | ❌ 401 | ✅ |
| `PATCH /admin/return_book/{id}` | ❌ 401 | ❌ 403 | ✅ |
| `PATCH /admin/fine/pay/{id}` | ❌ 401 | ❌ 403 | ✅ |

Authorization is implemented with inline `user.role != Role.LIBRARIAN` checks, not a
reusable role dependency. This produces inconsistent status codes and duplicated logic.

### 5.3 Security observations

- **Privilege escalation:** `POST /auth/register` accepts `role: "librarian"` from the
  client. Anyone who can reach the endpoint can self-register as a librarian.
- **No rate limiting** on login/register.
- **Inactive users can log in** and receive a token; they are rejected only on protected
  endpoints (`400`, not `401`).
- `SECRET_KEY` is a single static symmetric key; rotating it invalidates all tokens.
- `echo=True` logs every SQL statement and bound parameter to stdout.
- CORS now allows only localhost origins (regex), which is safe for development but must be
  extended deliberately for production.

---

## 6. Why the application currently has no data

This section distinguishes the six possible causes requested.

### 6.1 Observed evidence

| Check | Result |
|-------|--------|
| Is a backend server listening on `:8000`? | **No.** `curl http://127.0.0.1:8000/openapi.json` → connection failure (`000`). |
| Is the configured database reachable? | **No.** Connection fails with `FATAL: (ENOTFOUND) tenant/user postgres.<project-ref> not found`. |
| Does the direct Supabase project host resolve? | **No.** `db.<project-ref>.supabase.co` → `NXDOMAIN`. |
| Are migrations present? | **No** `alembic/`, no migration files. |
| Are seed scripts/fixtures present? | **None** before this review. |
| Are tests present? | **None.** `pytest` is not installed. |
| Does the frontend call the API? | **No.** `FeatureBooks.tsx` calls `fetch()` with no URL. |

The configured target is a Supabase pooler host. The tenant lookup fails before
authentication, which means the project referenced by `DATABASE_URL` does not currently
exist, is paused/deleted, or the project reference in the connection string is wrong.
This is **not** an empty-database problem; it is an unreachable-database problem.

> **Scope note:** these checks reflect this workspace and the `backend/.env` it contains.
> If your running backend uses a different environment or a corrected `DATABASE_URL`,
> the reachability result may differ. The connection failure above was reproduced twice
> with the configured target, and the project host does not resolve in DNS.

### 6.2 The six categories

| Category | Applies? | Explanation |
|----------|----------|-------------|
| **1. Empty database** | Likely, once reachable | `create_all` creates empty tables. Nothing populates them. |
| **2. Missing seed data** | **Yes** | No seed script/fixtures existed. This is the primary application-level cause. |
| **3. Incorrect API usage** | **Yes** | Frontend calls `fetch()` without a URL; login must be form-urlencoded; `/admin/add_book` must be form-encoded, not JSON. |
| **4. Missing/incomplete records** | **Yes** | No users, books, issues, or reservations exist to display. |
| **5. Frontend/API integration problems** | **Yes** | No API client, no `/books` page/route, no `/categories` route, `/about` missing; unauthenticated `/books/all` returns `401`; no CORS before this review. |
| **6. Actual backend implementation problems** | **Yes, secondary** | Five broken endpoints and several missing features (§9). The data absence itself is not caused by the schema. |

### 6.3 Conclusion

There are **three independent blockers**, in order:

1. **Environment blocker (critical):** the configured remote database cannot be reached,
   so the app cannot start or create tables.
2. **Data blocker (high):** no seed data and no seed mechanism existed.
3. **Integration blocker (high):** the frontend never calls the API, calls it without auth,
   and lacks the routes/pages it links to.

Fixing only #2 will not make the UI show data while #1 and #3 remain. The seed script
addresses #2; §8 addresses #3; #1 requires the project owner to restore/fix the database
target (not changed here).

> Do **not** change `DATABASE_URL` to a different database merely because this one has no
> application records. The connection failure is a separate infrastructure issue.

---

## 7. Recommended data initialization strategy

### 7.1 Why a script (not SQL, not a migration)

- The schema is created by `SQLModel.metadata.create_all`; there is no migration history.
- Enum columns store names, and the ORM handles the name/value conversion correctly.
- Passwords must be Argon2-hashed with the app's `get_password_hash`.
- Timestamps must be timezone-aware.
- Relationships (`book_id`, `user_id`) must be resolved from real inserted IDs.
- A Python script reuses the existing models, session factory, and security helpers, so it
  cannot drift from the schema.

### 7.2 The seed script

**File:** `backend/app/seed.py`
**Run as:** `python -m app.seed`

Design:

| Property | Implementation |
|----------|----------------|
| Idempotent | Users matched by `username`; books by `(title, author)`; issues by `(book_id, user_id, issue_date)`; reservations by `(book_id, user_id, reservation_date)`. Fixed timestamps make reruns stable. |
| Non-destructive | Never deletes, truncates, drops, or resets anything. |
| FK-safe | Inserts users and books first, flushes to obtain IDs, then issues/reservations. |
| Inventory-safe | `available_copies` starts at `total_copies` and is decremented once per newly created active issue. |
| Enum-safe | Uses `BookCategory`, `Role`, and `Status` enums; the ORM writes DB names. |
| Validation-safe | Titles/authors ≤150 chars, descriptions ≤220 chars, prices ≥0, copies ≥0. |
| Cover-safe | Each book stores a verified Open Library ISBN cover URL; the seed makes no network calls, so image-host outages cannot fail it. Edition-by-edition evidence is in `BOOK_COVER_URLS.md`. |
| Dry-run | `--dry-run` inserts inside a transaction and rolls back. Note: the script calls `create_db_and_tables()` first, so if the tables are missing, the dry run still creates the schema (DDL is not rolled back). The non-local guard runs before any of this. |
| Remote guard | Refuses non-local hosts unless `--allow-remote` is passed. |
| Secret-safe | Prints a masked database URL; never prints credentials. |

### 7.3 Dataset summary

| Entity | Count | Details |
|--------|-------|---------|
| Users | 14 | 2 librarians (`librarian`, `assistant`) + 12 members |
| Books | 30 | 3 per category across all 10 categories |
| Issue records | 15 | 10 active (`issued`), 5 returned; 2 returned with unpaid fines |
| Reservations | 10 | 5 `PENDING`, 3 `APPROVED`, 2 `REJECTED` |
| Categories | 10 | enum values, 3 books each |
| Authors/publishers | 0 tables | `author` is a string; no publisher concept |

All 30 cover images use verified Open Library ISBN URLs
(`https://covers.openlibrary.org/b/isbn/<isbn>-L.jpg`). Every URL returned
`HTTP 200 image/jpeg` during verification; 0 require manual replacement. The complete
ISBN/edition/cover table is in `BOOK_COVER_URLS.md`.

**Seeded books (30):**

| Category | Title | Author | ISBN | Total copies |
|---|---|---|---|---|
| Fiction | The Great Gatsby | F. Scott Fitzgerald | 9780020198819 | 6 |
| Fiction | To Kill a Mockingbird | Harper Lee | 9780061120084 | 8 |
| Fiction | The Alchemist | Paulo Coelho | 9780062315007 | 7 |
| Mystery | Gone Girl | Gillian Flynn | 9780307588371 | 6 |
| Mystery | The Hound of the Baskervilles | Arthur Conan Doyle | 9780140437867 | 5 |
| Mystery | The Girl with the Dragon Tattoo | Stieg Larsson | 9780307454546 | 4 |
| Thriller | The Da Vinci Code | Dan Brown | 9780307474278 | 7 |
| Thriller | The Silent Patient | Alex Michaelides | 9781250301697 | 5 |
| Thriller | Verity | Colleen Hoover | 9781538724736 | 6 |
| Romance | Pride and Prejudice | Jane Austen | 9780141439518 | 9 |
| Romance | It Ends with Us | Colleen Hoover | 9781501110368 | 7 |
| Romance | Me Before You | Jojo Moyes | 9780670026609 | 6 |
| Science Fiction | Dune | Frank Herbert | 9780441172719 | 6 |
| Science Fiction | The Martian | Andy Weir | 9780553418026 | 5 |
| Science Fiction | Project Hail Mary | Andy Weir | 9780593135204 | 6 |
| Fantasy | The Hobbit | J.R.R. Tolkien | 9780547928227 | 8 |
| Fantasy | Harry Potter and the Philosopher's Stone | J.K. Rowling | 9780747532699 | 9 |
| Fantasy | A Game of Thrones | George R.R. Martin | 9780553103540 | 6 |
| Biography | Educated | Tara Westover | 9780399590511 | 6 |
| Biography | Becoming | Michelle Obama | 9781524763138 | 5 |
| Biography | Steve Jobs | Walter Isaacson | 9781451648539 | 4 |
| History | Sapiens | Yuval Noah Harari | 9780062316097 | 7 |
| History | The Silk Roads | Peter Frankopan | 9781101912379 | 5 |
| History | Guns, Germs, and Steel | Jared Diamond | 9780393317558 | 4 |
| Science & Technology | A Brief History of Time | Stephen Hawking | 9780553380163 | 6 |
| Science & Technology | The Selfish Gene | Richard Dawkins | 9780198788607 | 5 |
| Science & Technology | Clean Code | Robert C. Martin | 9780132350884 | 4 |
| Self Help | Atomic Habits | James Clear | 9780735211292 | 9 |
| Self Help | Deep Work | Cal Newport | 9781455586691 | 6 |
| Self Help | The 7 Habits of Highly Effective People | Stephen R. Covey | 9781982137274 | 7 |

All seeded accounts share the password **`Library@123`** (development only).

Active checkouts intentionally leave several books with reduced availability, and the
dataset spans all categories so client-side filtering, sorting, and pagination can be
exercised.

### 7.4 Safe execution instructions

From the `backend/` directory:

```bash
cd backend

# 1. Preview the target and validate the guard (no writes if non-local)
uv run python -m app.seed --dry-run

# 2. Seed a confirmed LOCAL / disposable development database
uv run python -m app.seed
```

Equivalent without `uv`:

```bash
.venv/bin/python -m app.seed --dry-run
.venv/bin/python -m app.seed
```

For a **remote development** database (for example, a disposable Supabase dev project),
after confirming it is not production and taking a backup:

```bash
uv run python -m app.seed --allow-remote
```

**Do not** run with `--allow-remote` against production. The guard exists to prevent
accidental writes. The script itself never deletes existing rows, but it does create
tables if they are missing and inserts records.

### 7.5 What to do about the current unreachable database

1. Restore/unpause the Supabase project or correct the project reference in
   `DATABASE_URL` (owner action; not changed here).
2. Confirm the target is a development database.
3. Start the backend once so `create_all` creates the tables.
4. Run `python -m app.seed --dry-run`, then `python -m app.seed --allow-remote`.
5. Verify with `GET /books/all` using a librarian or member token.

If the current Supabase project is production or cannot be confirmed as disposable,
create a separate local/dev Postgres database and point a **development-only** environment
at it. Do not modify the working production configuration.

---

## 8. Frontend API integration reference

### 8.1 Base URL and headers

```ts
export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` }
}
```

- No `/api` or `/v1` prefix.
- JSON endpoints use `Content-Type: application/json`.
- `/auth/login` uses `application/x-www-form-urlencoded`.
- `/admin/add_book` uses form encoding (`FormData` or `URLSearchParams`).
- CORS now allows `http://localhost:<any-port>` and `http://127.0.0.1:<any-port>`.
- Token lifetime is 60 minutes by default; there is no refresh flow.

### 8.2 TypeScript interfaces (derived from the real schemas)

```ts
export type BookCategory =
  | 'fiction'
  | 'mystery'
  | 'thriller'
  | 'romance'
  | 'science_fiction'
  | 'fantasy'
  | 'biography'
  | 'history'
  | 'science_technology'
  | 'self_help'

export interface Book {
  id: number
  title: string
  author: string
  category: BookCategory
  description: string
  price: number
  total_copies: number
  available_copies: number
  cover_image: string | null
  created_at: string // ISO-8601, e.g. "2026-11-01T17:26:46.621813Z"
}

export type Role = 'librarian' | 'member'

export interface UserResponse {
  first_name: string
  last_name: string
  username: string
  email: string
  role: Role
  is_active: boolean
  phone_number: string | null
}

export interface Token {
  access_token: string
  token_type: string // "bearer"
}

export interface RegisterPayload {
  first_name: string
  last_name: string
  username: string
  email: string
  password: string
  role?: Role // omit in normal UI; see security warning
}

export interface UpdateUserPayload {
  first_name?: string
  last_name?: string
  email?: string
  phone_number?: string
}

export interface ChangePasswordPayload {
  current_password: string
  new_password: string
}

export type ReservationStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export interface Reservation {
  id: number
  book_id: number
  user_id: number
  reservation_date: string
  status: ReservationStatus
}

export type IssueStatus = 'issued' | 'returned' // backend convention, free-form string

export interface IssueRecord {
  id: number
  book_id: number
  user_id: number
  issue_date: string
  due_date: string
  return_date: string | null
  status: IssueStatus | string
  fine_amount: number
  fine_paid: boolean
}

export interface CreateBookForm {
  title: string
  author: string
  description: string
  price?: number
  total_copies?: number
  category?: BookCategory
}

export interface UpdateBookPayload {
  title?: string
  author?: string
  description?: string
  price?: number
  total_copies?: number
  category?: BookCategory
}

export interface IssueBookPayload {
  book_id: number
  user_id: number
}

export interface JwtPayload {
  sub: string // username
  id: number
  role: Role
  exp: number // unix seconds
}

export type ApiError =
  | { detail: string }
  | {
      detail: Array<{
        type: string
        loc: Array<string | number>
        msg: string
        input?: unknown
      }>
    }
```

### 8.3 Authentication examples

**Login** (form-urlencoded, not JSON):

```ts
const body = new URLSearchParams({ username, password })

const res = await fetch(`${API_BASE}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body,
})

if (!res.ok) throw new Error((await res.json()).detail)
const token: Token = await res.json()
```

**Register**:

```ts
const res = await fetch(`${API_BASE}/auth/register`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    first_name: 'Alice',
    last_name: 'Carter',
    username: 'alice2',
    email: 'alice2@example.com',
    password: 'StrongPass@123',
    // role intentionally omitted -> "member"
  } satisfies RegisterPayload),
})
```

**Authenticated request**:

```ts
const res = await fetch(`${API_BASE}/books/all`, {
  headers: { Authorization: `Bearer ${token}` },
})
```

**Current user:** there is no `/auth/me`. The only server-issued identity data is inside the
JWT. Decoding is acceptable for display, but never for authorization decisions:

```ts
function decodeJwt(token: string): JwtPayload {
  const payload = token.split('.')[1]
  return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
}
```

**Logout** is purely client-side: discard the token.

### 8.4 Book endpoints

**List all books**:

```ts
const books: Book[] = await fetch(`${API_BASE}/books/all`, {
  headers: { Authorization: `Bearer ${token}` },
}).then((r) => r.json())
```

No query parameters are honored. `?page=`, `?limit=`, `?search=`, `?category=`, `?sort=`
are silently ignored and still return all 30 records.

**Book detail**:

```ts
const book: Book = await fetch(`${API_BASE}/books/${id}`, {
  headers: { Authorization: `Bearer ${token}` },
}).then((r) => r.json())
```

**Reserve**:

```ts
await fetch(`${API_BASE}/books/reserve/${bookId}`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
})
// 201 { "message": "Book reserved successfully" }
```

**My reservations**:

```ts
const reservations: Reservation[] = await fetch(`${API_BASE}/books/reservation/my`, {
  headers: { Authorization: `Bearer ${token}` },
}).then((r) => r.json())
```

**Cancel reservation**:

```ts
await fetch(`${API_BASE}/books/reserve/cancel/${reservationId}`, {
  method: 'PUT',
  headers: { Authorization: `Bearer ${token}` },
})
```

**My active checkouts**:

```ts
const issues: IssueRecord[] = await fetch(`${API_BASE}/books/issues/my`, {
  headers: { Authorization: `Bearer ${token}` },
}).then((r) => r.json())
```

### 8.5 Admin examples

**Add a book** (form encoding; `cover_image` is not supported):

```ts
const form = new FormData()
form.set('title', 'New Book')
form.set('author', 'Author Name')
form.set('description', 'Short description (max 220 chars)')
form.set('price', '19.99')
form.set('total_copies', '5')
form.set('category', 'fiction')

await fetch(`${API_BASE}/admin/add_book`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${librarianToken}` }, // do NOT set Content-Type
  body: form,
})
```

**Update a book** (JSON):

```ts
await fetch(`${API_BASE}/admin/update_book/${bookId}`, {
  method: 'PATCH',
  headers: {
    Authorization: `Bearer ${librarianToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ price: 21.5, total_copies: 8 } satisfies UpdateBookPayload),
})
```

**Delete a book**:

```ts
await fetch(`${API_BASE}/admin/delete_book/${bookId}`, {
  method: 'DELETE',
  headers: { Authorization: `Bearer ${librarianToken}` },
})
// 204 no content
```

**Issue a book**:

```ts
await fetch(`${API_BASE}/admin/issue_record`, {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${librarianToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ book_id: 5, user_id: 7 } satisfies IssueBookPayload),
})
```

**Return a book**:

```ts
const result = await fetch(`${API_BASE}/admin/return_book/${issueId}`, {
  method: 'PATCH',
  headers: { Authorization: `Bearer ${librarianToken}` },
}).then((r) => r.json())
// { "message": "Book returned successfully", "fine_amount": 200.0 }
```

**Mark a fine paid**:

```ts
await fetch(`${API_BASE}/admin/fine/pay/${issueId}`, {
  method: 'PATCH',
  headers: { Authorization: `Bearer ${librarianToken}` },
})
```

### 8.6 Error handling

Error shapes:

- Domain errors: `{ "detail": "Book not found" }`
- Validation errors (`422`):

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required",
      "input": { "first_name": "x" }
    }
  ]
}
```

- `401` from `OAuth2PasswordBearer` when the header is missing:
  `{ "detail": "Not authenticated" }` with `WWW-Authenticate: Bearer`.
- `401` from invalid/expired token: `{ "detail": "Could not validate credentials" }`.
- `400` inactive user: `{ "detail": "Inactive user" }`.
- Role failures: `401 Failed Authentication` (admin write endpoints) or
  `403 Librarian access required` (return/fine).

Suggested client handling:

```ts
async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (res.status === 401) {
    // clear token, redirect to /login
  }
  if (!res.ok) {
    let detail: unknown = res.statusText
    try {
      detail = (await res.json()).detail
    } catch {}
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return res.status === 204 ? (undefined as T) : res.json()
}
```

### 8.7 Pagination behavior

**There is no server-side pagination.** `GET /books/all` returns every row. Query
parameters are ignored. Implement pagination, search, filtering, and sorting in the client:

```ts
function paginate<T>(items: T[], page: number, pageSize: number) {
  const start = (page - 1) * pageSize
  return items.slice(start, start + pageSize)
}

const filtered = books
  .filter((b) => category === 'all' || b.category === category)
  .filter((b) => `${b.title} ${b.author}`.toLowerCase().includes(query.toLowerCase()))
  .sort((a, b) => a.title.localeCompare(b.title))
```

For large datasets this will eventually need a backend endpoint; none exists today.

### 8.8 Which endpoints can power which UI

| UI feature | Available? | How |
|------------|------------|-----|
| Homepage hero | ✅ static | `HeroBanner.tsx` is already static; no API needed. |
| Featured books | ⚠️ partial | No "featured" flag. Use `GET /books/all`, then pick curated IDs or sort by `available_copies`/`created_at` client-side. Requires auth. |
| Book listing | ✅ | `GET /books/all`; paginate/filter/sort client-side. |
| Book details | ✅ | `GET /books/{id}`. |
| Category sections | ⚠️ derived only | No categories table/endpoint. Derive the 10 categories from `Book.category` and group client-side. |
| Search | ❌ server-side | No endpoint. `/books/search` returns `422` due to route shadowing. Filter client-side. |
| Author pages | ❌ | No author table/endpoint; `author` is a string on each book. |
| Publisher pages | ❌ | No publisher concept. |
| Dashboard statistics | ❌ server-side | No stats endpoint. You can compute book counts from `/books/all`, but issue/reservation totals for all users are not exposed. |
| Borrowing (member self-service) | ❌ | Members cannot issue books. Only librarians via `POST /admin/issue_record`. |
| Borrowing history | ❌ | `/books/issues/my` returns only `status == "issued"`; returned records are not exposed. |
| Reservations | ✅ | Reserve, cancel, list own. No availability/duplicate checks. |
| Fine payment | ✅ librarian | `PATCH /admin/fine/pay/{issue_id}`. |
| User profile | ⚠️ partial | Register/edit responses and JWT claims only; no `GET /auth/me`. |
| User management | ❌ | No list/create/update/deactivate endpoints for librarians. |
| Admin issue/reservation lists | ❌ | Only "my" endpoints exist. |
| Notifications | ❌ | Not implemented. |

### 8.9 Recommended frontend routes vs. actual React Router

The current `frontend/src/routes/Routes.tsx` defines only `/` and `/login`, while
`Navbar.tsx` links to `/books`, `/categories`, and `/about`. Those paths currently render
nothing. Add routes/pages before wiring the API.

`FeatureBooks.tsx` currently contains:

```ts
const [featureBooks, setFeatureBooks] = useState([])
useEffect(() => { fetch() }, [])
```

`fetch()` with no URL is invalid. Replace it with an authenticated
`GET ${API_BASE}/books/all` call and handle `401` by redirecting to login.

---

## 9. Identified problems and severity

### 9.1 Critical

| ID | Problem | Evidence / impact |
|----|---------|-------------------|
| C1 | Configured remote database unreachable | `FATAL: (ENOTFOUND) tenant/user postgres.<project-ref> not found`; direct project host `NXDOMAIN`. App startup (`create_all`) cannot complete. Not changed by this review. |
| C2 | No application data and no seed mechanism (before this review) | All collections empty once tables exist. Addressed by `app/seed.py`. |

### 9.2 High

| ID | Problem | Status |
|----|---------|--------|
| H1 | `POST /auth/register` accepts `role: "librarian"` from the client (privilege escalation) | **Open** — documented; not changed because it alters auth behavior. Recommend forcing `Role.MEMBER` server-side. |
| H2 | `GET /books/issues/my` returned `500` (`db.exec` not awaited) | **Fixed** |
| H3 | `PATCH /auth/changepassword` returned `500` (`update_password` vs `update_pass`) | **Fixed** |
| H4 | `DELETE /admindelete_book/{id}` (missing slash) unreachable | **Fixed** to `/admin/delete_book/{id}` |
| H5 | `PATCH /adminfine/pay/{id}` (missing slash) unreachable | **Fixed** to `/admin/fine/pay/{id}` |
| H6 | `fine/pay` typed `issue_id` as `str`, causing `integer = varchar` SQL error | **Fixed** to `int` |
| H7 | Issued books stored with status `"PENDING"`, invisible to `/books/issues/my` | **Fixed** to `"issued"` |
| H8 | No CORS middleware; browser frontend blocked | **Fixed** for localhost origins |
| H9 | Frontend never calls the API and lacks `/books`, `/categories`, `/about` routes | **Open** (frontend work; §8) |
| H10 | `GET /books/all` requires auth; anonymous homepage fetch gets `401` | **Open** (by design; frontend must log in or use a public endpoint) |

### 9.3 Medium

| ID | Problem | Impact |
|----|---------|--------|
| M1 | No pagination/filter/search/sort on `/books/all` | Client-side only; scales poorly. |
| M2 | No `GET /auth/me` | Frontend cannot fetch the current profile; must decode JWT. |
| M3 | No dashboard/statistics endpoint | Dashboard must be computed from `/books/all` only; issue/reservation totals unavailable. |
| M4 | No author/publisher tables or endpoints | Only a free-text `author` field. |
| M5 | Deleting a book with issue/reservation rows returns `500` (FK, no cascade) | Admin delete is unsafe for books with history. |
| M6 | `PATCH /auth/edituser` with a duplicate email returns `500` | No uniqueness check; DB error leaks as 500. |
| M7 | Role failures use `401` on some endpoints and `403` on others | Inconsistent client handling. |
| M8 | Reservations allow duplicates and unavailable books; no inventory hold | Data quality and UX issues. |
| M9 | `fine/pay` can mark unpaid/nonexistent fines; no return check | Business-logic gap. |
| M10 | Inactive users can obtain a token at login | Rejected later with `400`, but token is issued. |
| M11 | No migrations; `create_all` never alters existing tables | Future schema changes require manual SQL. |
| M12 | `echo=True` logs all SQL and parameters | Noise and potential data leakage in logs. |
| M13 | No automated tests; `pytest` not installed | Regressions are easy. |
| M14 | No rate limiting on login/register | Brute-force exposure. |
| M15 | `cover_image` cannot be set via add/update | New books always have `null` covers. |

### 9.4 Low

| ID | Problem | Impact |
|----|---------|--------|
| L1 | `Create_Books` default category is `biography`, model default is `fiction` | Inconsistent defaults depending on creation path. |
| L2 | Model `available_copies` default is `3`, `total_copies` default is `5` | Direct ORM inserts can start inconsistent; API/seed avoid it. |
| L3 | `Reservation.id` typed `int` with `default=None` | Type-checking oddity; runtime works. |
| L4 | `price`/`fine_amount` use `float`, not `Decimal` | Floating-point money. |
| L5 | `description` capped at 220 characters in the API | Tight for real book blurbs. |
| L6 | No `created_at`/`updated_at` on user/reservation/issue | Limited auditing. |
| L7 | No `expires_in` in the token response | Clients must decode `exp`. |
| L8 | `GET /books/{book_id}` shadows a future `/books/search` | Returns `422` for `/books/search`. |
| L9 | No stable `ORDER BY` on book lists | Order is not guaranteed. |
| L10 | `Token` response has no refresh token | Re-login every 60 minutes. |

---

## 10. Changes applied during this review

Only surgical fixes and the new seed script were added. **No models, schemas, database
configuration, environment variables, or auth dependencies were changed.**

### 10.1 `backend/app/main.py` — CORS

Added `CORSMiddleware` allowing localhost/127.0.0.1 on any port. This is required for the
Vite dev server to call the API from a browser. Production origins are intentionally not
allowed.

### 10.2 `backend/app/api/routers/auth.py` — password change

```diff
-    current_user.hash_password = get_password_hash(update_password.new_password)
+    current_user.hash_password = get_password_hash(update_pass.new_password)
```

### 10.3 `backend/app/api/routers/books.py` — missing await

```diff
-    issues = db.exec(
+    issues = await db.exec(
         select(IssueRecord).where(...)
     )
```

### 10.4 `backend/app/api/routers/admin.py` — four fixes

```diff
-@router.delete("delete_book/{book_id}", ...)
+@router.delete("/delete_book/{book_id}", ...)

-@router.patch("fine/pay/{issue_id}")
-async def fine_paid(..., issue_id: str):
+@router.patch("/fine/pay/{issue_id}")
+async def fine_paid(..., issue_id: int):

-        status=Status.PENDING,
+        status="issued",
```

### 10.5 `backend/app/seed.py` — new file

Idempotent development seed script. See §7.

### 10.6 Not changed (deliberately)

- `.env`, `app/core/config.py`, `app/core/database.py`
- `app/models/*`, `app/schemas/*`
- `app/dependencies/auth.py`, `app/core/security.py`
- Registration role behavior (security warning H1)
- Any production data or credentials

---

## 11. Verification results

### 11.1 Verification environment

| Item | Value |
|------|-------|
| Target | Disposable local PostgreSQL 16 container |
| Host/port | `127.0.0.1:55432` |
| Database | `library` |
| Isolation | Created for this review; removed afterwards |
| Configured remote DB | **Not contacted for writes** |
| Test client | `fastapi.testclient.TestClient` with `raise_server_exceptions=False` |
| App config | `DATABASE_URL` overridden **per process only**; `.env` untouched |

### 11.2 Seed verification

| Run | Users created | Books created | Issues created | Reservations created | Skipped |
|-----|---------------|---------------|----------------|----------------------|---------|
| 1 | 14 | 30 | 15 | 10 | 0 |
| 2 (rerun) | 0 | 0 | 0 | 0 | 69 |

- Row counts after rerun unchanged: 14 users, 30 books, 15 issues, 10 reservations.
- Inventory consistency query returned **0 mismatches**:
  `available_copies == total_copies - active_issue_count` for every book.
- Enum storage confirmed: `FICTION`, `MEMBER`, `PENDING`, etc. in the database.
- All 10 categories have exactly 3 books.
- All 30 seeded books have a unique, non-null Open Library cover URL; 30/30 returned
  `HTTP 200 image/jpeg` with `?default=false` (so missing covers could not masquerade as
  blank placeholders).
- A non-destructive rerun test inserted an unrelated user, book, issue, and reservation
  outside the seed. The rerun created 0 rows and left all custom records and foreign keys
  intact; inventory remained consistent.

### 11.3 Cover image verification

| Check | Result |
|-------|--------|
| Books with a non-null cover URL | 30 / 30 |
| Unique cover URLs | 30 / 30 |
| Cover URLs returning `HTTP 200 image/jpeg` | 30 / 30 |
| ISBNs matched to the intended title/author/edition | 30 / 30 |
| URLs requiring manual replacement | 0 |
| Corrected ISBNs during verification | *The Great Gatsby* (`9780020198819`), *Me Before You* (`9780670026609`), *Educated* (`9780399590511`) |
| Primary source | Open Library Covers API (`https://covers.openlibrary.org/b/isbn/<isbn>-L.jpg`) |
| Secondary confirmation | Publisher/retailer/bibliographic ISBN lookup for six records that hit transient Open Library/Google Books rate limits |
| Full evidence | `BOOK_COVER_URLS.md` |

The seed stores URLs only; it does not download images, so a temporary image-host outage
cannot fail the seed. Verification used `?default=false` and followed redirects to reject
Open Library's blank placeholder response.

### 11.4 Endpoint verification

**72 checks passed, 0 failed.** Coverage by area:

| Area | Checks | Result |
|------|--------|--------|
| Login / wrong password / register / duplicate / invalid email | 7 | ✅ |
| Profile edit / password change / re-login | 4 | ✅ |
| Book list/detail/404/422/query-param behavior | 8 | ✅ |
| Reservations create/list/cancel/403/404/duplicates | 8 | ✅ |
| My issues (previously 500) and field shape | 5 | ✅ |
| Issue record RBAC, missing book/user, inventory decrement, reservation auto-approval | 7 | ✅ |
| Update book success/400/404/RBAC | 5 | ✅ |
| Return book RBAC, fine calculation, double return, missing issue | 5 | ✅ |
| Fine payment RBAC/success/404 | 3 | ✅ |
| Add book RBAC/success/inventory/validation | 7 | ✅ |
| Delete book success/404 | 2 | ✅ |
| FK delete behavior (documented 500) | 1 | ✅ |
| CORS allowed/rejected origins | 2 | ✅ |
| Absent features (`/admin/dashboard`, `/admin/stats`, `/categories`, `/authors`, `/publishers`, `/auth/me`) | 6 | ✅ |
| `/books/search` route shadowing (422) | 1 | ✅ |

A separate seed/API smoke test on the 30-book dataset also passed: `GET /books/all`
returned 30 books (3 per category), all 30 covers were present and unique, issuing a book
decremented availability by 1, and returning it restored availability and set the issue
status to `returned`.

Key verified behaviors:

- `GET /books/all` returns 30 books with all 10 model fields.
- `Book.category` serializes as lowercase (`"fiction"`); DB stores uppercase (`FICTION`).
- `created_at` serializes as ISO-8601 UTC with `Z`.
- `GET /books/issues/my` returns `200` and only `"issued"` records.
- Issuing decrements `available_copies` by exactly 1.
- A matching `PENDING` reservation becomes `APPROVED` on issue.
- Returning an overdue book computes `overdue_days * 20` (verified 10 days → `200.0`).
- Double return returns `409`.
- `total_copies` below checked-out returns `400`.
- `add_book` sets `available_copies = total_copies`.
- Validation returns `422` for negative price/copies, invalid category, and >220-char
  description.
- Deleting a book with issue history returns `500` (documented FK gap).
- CORS preflight from `http://localhost:5173` is allowed; a foreign origin is rejected.
- All absent endpoints return `404`; `/books/search` returns `422` due to route shadowing.

Two initial test expectations were corrected during the run (test bugs, not code bugs):
the inventory test initially used a book with zero checkouts, and `/books/search` was
expected to be `404` rather than the actual `422`.

### 11.5 Lint / static checks

```text
ruff check app      -> All checks passed!
ruff format --check -> 23 files already formatted
python -m py_compile app/seed.py -> OK
```

### 11.6 Remote database verification

- Connection attempted read-only with a short timeout.
- Result: `FATAL: (ENOTFOUND) tenant/user postgres.<project-ref> not found`.
- Direct project host: `NXDOMAIN`.
- No tables were created, no rows were written, and no migrations were run against it.
- See §13 for the full 2026-11-02 re-investigation and the current blocked-data status.

### 11.7 Existing backend tests

No tests exist in the repository and `pytest` is not installed, so there was no pre-existing
suite to run. The verification suite above was executed ad hoc against the disposable local
database.

---

## 12. Appendix — commands, accounts, files

### 12.1 Seeded accounts (development only)

| Username | Role | Email |
|----------|------|-------|
| `librarian` | librarian | `librarian@library.dev` |
| `assistant` | librarian | `assistant@library.dev` |
| `alice` | member | `alice@example.com` |
| `bob` | member | `bob@example.com` |
| `carol` | member | `carol@example.com` |
| `david` | member | `david@example.com` |
| `emma` | member | `emma@example.com` |
| `farhan` | member | `farhan@example.com` |
| `grace` | member | `grace@example.com` |
| `hassan` | member | `hassan@example.com` |
| `isabel` | member | `isabel@example.com` |
| `jonas` | member | `jonas@example.com` |
| `keira` | member | `keira@example.com` |
| `liam` | member | `liam@example.com` |

Password for all: **`Library@123`**.

### 12.2 Seed data characteristics

- 30 books, 3 in each of the 10 categories.
- 10 active checkouts and 5 returned records.
- 2 returned records with unpaid fines (`160.0` and `100.0`).
- 10 reservations: 5 pending, 3 approved, 2 rejected.
- Several books have reduced availability; all inventory values are consistent.
- Fixed dates around September–October 2026 make the data deterministic and idempotent.
- All 30 books have unique, verified Open Library cover URLs; 0 require manual replacement.
- Existing rows are never modified. On an already-seeded database the script only adds
  missing definitions, so the three corrected ISBNs (*The Great Gatsby*, *Me Before You*,
  *Educated*) keep their previous cover URLs until those rows are refreshed manually or a
  fresh development database is seeded.

### 12.3 Commands used for verification

```bash
# local disposable database
docker run -d --name library-seed-verify \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=library \
  -p 127.0.0.1:55432:5432 postgres:16-alpine

cd backend
DATABASE_URL='postgresql+psycopg://postgres:postgres@127.0.0.1:55432/library' \
  .venv/bin/python -m app.seed

DATABASE_URL='postgresql+psycopg://postgres:postgres@127.0.0.1:55432/library' \
  PYTHONPATH=. .venv/bin/python /tmp/opencode/verify.py

.venv/bin/ruff check app
.venv/bin/ruff format --check app
```

The container and temporary verification files were removed after the run.

### 12.4 Files added/modified

| File | Change |
|------|--------|
| `backend/app/seed.py` | **Added/updated** — idempotent seed script with 30 books (3 per category), 15 issues, 10 reservations, and verified cover URLs |
| `BOOK_COVER_URLS.md` | **Added** — per-book ISBN, edition, cover URL, source, and verification record |
| `backend/app/main.py` | Added localhost CORS middleware |
| `backend/app/api/routers/auth.py` | Fixed password-change typo |
| `backend/app/api/routers/books.py` | Added missing `await` |
| `backend/app/api/routers/admin.py` | Fixed two route paths, one type, one status |
| `data.md` | Canonical full review (this report) |
| `BACKEND_ANALYSIS.md` | Identical deliverable copy of this report |

### 12.5 Final recommendation order

1. **Restore or correct the database target** (owner action). Do not point it at production.
2. Start the backend so `create_all` creates tables.
3. Run `python -m app.seed --dry-run`, then seed the confirmed dev database.
4. Build the frontend API client using §8 and add the missing `/books`, `/categories`,
   `/about` routes.
5. Address H1 (registration role escalation) before exposing registration publicly.
6. Add server-side pagination/search and a dashboard endpoint when the dataset grows.
7. Add Alembic and automated tests before further schema changes.

---

## 13. Supabase connection investigation — 2026-11-02

This section records the follow-up investigation into the live Supabase connection failure.
It supplements, but does not replace, the earlier local verification in §11.

### 13.1 Reported failure

Command:

```bash
cd /home/jayed/FastAPI/Phitron/library_Management/backend
uv run fastapi dev app/main.py
```

Observed failure:

```text
psycopg.OperationalError:
connection failed: connection to server at "65.0.195.55", port 5432 failed:
FATAL: (ENOTFOUND) tenant/user postgres.mhbbjwssxuikdbhwxutx not found

Host: aws-0-ap-south-1.pooler.supabase.com
Port: 5432
Username: postgres.mhbbjwssxuikdbhwxutx
```

Failure path:

```text
app/main.py:12                  await create_db_and_tables()
app/core/database.py:40         async with engine.begin() as connection:
```

The same failure was reproduced with a minimal Psycopg async connection using the runtime
settings, and by starting the application through `uv run fastapi dev`. Application startup
fails at lifespan initialization, so `/docs` is not reachable.

### 13.2 Configuration actually used at runtime

| Item | Runtime value / result |
|------|------------------------|
| Configuration source | `backend/.env` loaded by `pydantic-settings` |
| Working directory | `backend/` |
| Shell `DATABASE_URL` override | **None** |
| Shell `SECRET_KEY` override | **None** |
| `.env` keys | `DATABASE_URL`, `SECRET_KEY` |
| `.env` gitignored | **Yes** (`backend/.gitignore`, line 4) |
| `.env.example` before review | **Did not exist** |
| SQLAlchemy driver | `postgresql+psycopg` (correct async Psycopg 3 driver) |
| Host | `aws-0-ap-south-1.pooler.supabase.com` |
| Port | `5432` (session-pooler port) |
| Database | `postgres` |
| Username | `postgres.mhbbjwssxuikdbhwxutx` |
| Project reference in username | `mhbbjwssxuikdbhwxutx` |
| Password | Present; no unencoded `@`, `:`, `/`, `?`, `#`, or `%` detected. Value not printed. |
| Query parameters | None |
| Multiple/conflicting database URLs | None found |
| Engine creation | `create_async_engine(settings.DATABASE_URL, echo=True)` |
| Lifespan | Calls `create_db_and_tables()` before serving requests |
| Model tables | `user`, `book`, `issuerecord`, `reservation` |
| Migrations | None found |
| Tests | None found |
| Health/readiness endpoint | None found |
| Database dependencies | `psycopg[binary]>=3.3.6`, `sqlalchemy[asyncio]==2.1.6`, `sqlmodel>=0.0.47`, `pydantic-settings==2.16.1` |

No separate Supabase project URL is configured in the repository. The project reference
appears only in the database username inside `.env`, so it cannot be cross-checked against a
second local source.

### 13.3 Connectivity evidence

| Check | Result |
|-------|--------|
| Control DNS: `supabase.co` | Resolves (`76.76.21.21`) |
| Project API host: `mhbbjwssxuikdbhwxutx.supabase.co` | **NXDOMAIN** via public DNS (`1.1.1.1`) |
| Direct DB host: `db.mhbbjwssxuikdbhwxutx.supabase.co` | **NXDOMAIN** via public DNS |
| Pooler host: `aws-0-ap-south-1.pooler.supabase.com` | Resolves; TCP 5432 and 6543 reachable |
| `aws-0-ap-south-1` session pooler connection | `FATAL: (ENOTFOUND) tenant/user postgres.mhbbjwssxuikdbhwxutx not found` |
| `aws-1-ap-south-1` session pooler connection | Same tenant/user error |
| Password authentication | Never reached; the pooler cannot resolve the tenant |
| Username format | Correct shared-pooler format: `postgres.[PROJECT-REF]` |
| Port/mode | Correct for session pooler: `5432` |
| Driver | Correct: `postgresql+psycopg` |

Official references used:

- <https://supabase.com/docs/guides/database/connecting-to-postgres>
- <https://supabase.com/kb/troubleshooting/tenant-or-user-not-found>
- <https://supabase.com/docs/guides/troubleshooting/nxdomain-error-connecting-to-a-supabase-project>

### 13.4 Root cause

The configured project reference does not map to an active Supabase project/tenant.

The shared pooler is reachable and the username format is correct, but both `aws-0` and
`aws-1` pooler clusters in `ap-south-1` reject the same tenant. At the same time, both the
project API hostname and the direct database hostname return `NXDOMAIN`, while unrelated
Supabase control hostnames resolve normally.

Per Supabase’s official troubleshooting, those symptoms mean one of:

1. The project reference is wrong or stale.
2. The project is paused.
3. The project was deleted.

This is **not** a FastAPI, SQLAlchemy, SQLModel, Psycopg, URL-encoding, port, driver, or
password problem. No code change can create a missing Supabase tenant. The project must be
restored, or the correct project reference and Session pooler connection string must be
copied from the Supabase Dashboard.

### 13.5 Changes made

| File | Change |
|------|--------|
| `backend/.env.example` | **Added** — safe placeholders only, documenting the async URL format, the shared-pooler username format, and the requirement to copy the pooler host from Supabase. |

No changes were made to:

- `.env`
- `app/core/database.py`
- `app/core/config.py`
- `app/main.py`
- Models, schemas, routers, or dependencies
- Database data, schema, tables, or migrations

`.env` remains gitignored. No credentials were generated, invented, or printed.

### 13.6 Database connection status

**The database connection does not work.**

- Minimal Psycopg async test: **failed** with the tenant/user error.
- `uv run fastapi dev app/main.py`: **fails at lifespan startup** in
  `create_db_and_tables()`.
- `/docs`: **not reachable** because startup does not complete.
- Tables created by this startup attempt: **not reached**.
- Writes performed: **none**.
- Schema changes performed: **none**.
- Seed script run against Supabase: **none**.

### 13.7 Existing database data — verification blocked

Because the tenant cannot be reached, no read-only count query could run. The database must
not be described as empty or populated until connectivity is restored.

Expected tables from the SQLModel models:

| Table | Exists | Record Count | Status |
|---|---|---:|---|
| `user` | Unknown | Not queried | Blocked — no DB connection |
| `book` | Unknown | Not queried | Blocked — no DB connection |
| `issuerecord` | Unknown | Not queried | Blocked — no DB connection |
| `reservation` | Unknown | Not queried | Blocked — no DB connection |

Important distinctions:

- The actual model table names are singular: `user`, `book`, `issuerecord`, `reservation`.
- There are no plural `books` or `borrow_records` tables in the models.
- No migrations directory exists; schema creation is performed by
  `SQLModel.metadata.create_all` during lifespan startup.
- Because startup never connected, it is unknown whether the existing Supabase database
  already has these tables or data.
- If a future successful startup creates missing tables, that is schema creation by
  `create_all`, not proof that pre-existing data was present.
- No rows were inserted, updated, deleted, dropped, or truncated during this review.

After connectivity is restored, this read-only script reports the real table counts:

```bash
cd /home/jayed/FastAPI/Phitron/library_Management/backend

uv run python - <<'PY'
import asyncio
from sqlalchemy import text
from app.core.database import engine

TABLES = ("user", "book", "issuerecord", "reservation")

async def main():
    async with engine.connect() as conn:
        db = (await conn.execute(text("select current_database()"))).scalar_one()
        schema = (await conn.execute(text("select current_schema()"))).scalar_one()
        print(f"database={db} schema={schema}")

        for table in TABLES:
            exists = (await conn.execute(
                text("select to_regclass(:name) is not null"),
                {"name": f"public.{table}"},
            )).scalar_one()

            if not exists:
                print(f"{table}: exists=no")
                continue

            count = (await conn.execute(
                text(f'SELECT COUNT(*) FROM "{table}"')
            )).scalar_one()
            print(f"{table}: exists=yes count={count}")

    await engine.dispose()

asyncio.run(main())
PY
```

### 13.8 Backend verification

| Check | Result |
|-------|--------|
| Independent DB connection test | **Failed** — tenant/user not found |
| FastAPI lifespan startup | **Failed** at `create_db_and_tables()` |
| Tables created | Not reached |
| `/docs` | Not reachable because startup fails |
| Health endpoint | None implemented |
| Existing tests | None found |
| `uv run ruff check .` | Passed |
| `uv run ruff format --check .` | Passed, 24 files formatted |

Ruff passing validates syntax/style only; it does not validate database connectivity.

### 13.9 Details that must come from the Supabase Dashboard

| Detail | Where to obtain it |
|--------|--------------------|
| Project reference | Dashboard URL or **Project Settings → General** |
| Pooler hostname | **Connect → Session pooler** — copy it; do not derive it from the region |
| Port/mode | Session pooler = `5432`; transaction pooler = `6543` |
| Username | `postgres.<PROJECT-REF>` for the shared pooler |
| Database name | Usually `postgres` |
| Password | Existing database password; retrieve/reset under **Project Settings → Database** only if needed |

### 13.10 Manual action required

1. Open <https://supabase.com/dashboard/projects>.
2. Find the project.
   - If it is **Paused**, click **Restore** / **Resume** and wait until it is active.
   - If it is not listed, it may have been deleted. Check organization audit logs or contact
     Supabase support. Do not create a new project unless you intend to lose the old data.
3. Open the project and confirm the reference in the dashboard URL:
   `https://supabase.com/dashboard/project/<PROJECT-REF>`.
   Compare it with `mhbbjwssxuikdbhwxutx`. If it differs, the `.env` value is stale.
4. Click **Connect**, choose **Session pooler**, and copy the entire connection string.
   Do not construct the `aws-0` / `aws-1` host from the region.
5. Update `backend/.env` locally, preserving the async driver prefix:

   ```dotenv
   DATABASE_URL=postgresql+psycopg://postgres.<PROJECT-REF>:<URL-ENCODED-PASSWORD>@<POOLER-HOST>:5432/postgres
   SECRET_KEY=<keep the existing value>
   ```

   Percent-encode reserved password characters if present:
   `@` → `%40`, `:` → `%3A`, `/` → `%2F`, `?` → `%3F`, `#` → `%23`, `%` → `%25`.
6. If the password is unknown, retrieve or reset it at
   `https://supabase.com/dashboard/project/<PROJECT-REF>/database/settings`.
   Do not reset it unless the new connection string reports password authentication failure;
   the current error is tenant resolution.
7. Optional security hardening:

   ```bash
   chmod 600 backend/.env
   ```

8. Do not paste the password or full connection string into chat.

### 13.11 Verification commands after updating `.env`

Connectivity:

```bash
cd /home/jayed/FastAPI/Phitron/library_Management/backend

uv run python - <<'PY'
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def main():
    async with engine.connect() as conn:
        row = (await conn.execute(
            text("select current_database(), current_user")
        )).one()
        print("database:", row[0], "user:", row[1])
    await engine.dispose()

asyncio.run(main())
PY
```

Read-only table/count verification: run the script in §13.7.

Application startup:

```bash
uv run fastapi dev app/main.py
```

Then open <http://127.0.0.1:8000/docs>. A successful lifespan completes without the
`tenant/user ... not found` error and creates only missing tables; it does not drop existing
tables or data.

