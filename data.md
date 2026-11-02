# Library Management Backend — Seed Dataset Update Report

**Project:** `Phitron/library_Management`
**Backend root:** `backend/`
**Report date:** 2026-11-02
**Task:** Populate seed dataset with 30 realistic books and verified cover images.

---

## 1. Executive Summary

The seed dataset in `backend/app/seed.py` has been updated to contain **30 high-quality, realistic book records** with **genuine book-cover images** from the Open Library Covers API. All 30 cover URLs were verified via HTTP HEAD requests and return valid image content.

### Key Results

| Metric | Value |
|--------|-------|
| Total book definitions | 30 |
| Verified cover URLs | 30 |
| URLs requiring manual replacement | 0 |
| Categories represented | 10 |
| Issue record references preserved | 15/15 |
| Reservation references preserved | 10/10 |
| Ruff lint | Passed |
| Ruff format | Passed |

---

## 2. Book Dataset Changes

### Books Added (6)

Six books from the task's suggested list were added:

| Book | Author | Category | ISBN |
|------|--------|----------|------|
| 1984 | George Orwell | Fiction | 9780451524935 |
| The Girl on the Train | Paula Hawkins | Thriller | 9781594634024 |
| The Notebook | Nicholas Sparks | Romance | 9780446605236 |
| Foundation | Isaac Asimov | Science Fiction | 9780553293357 |
| The Diary of a Young Girl | Anne Frank | Biography | 9780553296983 |
| Long Walk to Freedom | Nelson Mandela | Biography | 9780743227354 |

### Books Removed (6)

Six non-referenced books were removed to maintain exactly 30 seed definitions:

| Book | Author | Reason |
|------|--------|--------|
| To Kill a Mockingbird | Harper Lee | Not referenced by issue/reservation records |
| The Da Vinci Code | Dan Brown | Not referenced by issue/reservation records |
| Me Before You | Jojo Moyes | Not referenced by issue/reservation records |
| Steve Jobs | Walter Isaacson | Not referenced by issue/reservation records |
| The Hound of the Baskervilles | Arthur Conan Doyle | Not referenced by issue/reservation records |
| A Game of Thrones | George R.R. Martin | Not referenced by issue/reservation records |

### Books Preserved (24)

All 24 books that appear in both the previous and current datasets were kept. This includes 6 books that the suggested list wanted to remove but are referenced by existing issue or reservation records:

| Book | Referenced By |
|------|---------------|
| The Alchemist | Issue record (david, returned) |
| Verity | Reservation (grace, rejected) |
| It Ends with Us | Reservation (hassan, rejected) |
| Project Hail Mary | Issue record (hassan, active) |
| Educated | Issue record (grace, active) + Reservation (alice, approved) |
| Becoming | Issue record (emma, returned) |

---

## 3. Category Distribution

| Category | Books | Titles |
|----------|-------|--------|
| Fiction | 3 | The Great Gatsby, The Alchemist, 1984 |
| Mystery | 2 | Gone Girl, The Girl with the Dragon Tattoo |
| Thriller | 3 | The Silent Patient, Verity, The Girl on the Train |
| Romance | 3 | Pride and Prejudice, It Ends with Us, The Notebook |
| Science Fiction | 4 | Dune, The Martian, Project Hail Mary, Foundation |
| Fantasy | 2 | The Hobbit, Harry Potter and the Philosopher's Stone |
| Biography | 4 | Educated, Becoming, The Diary of a Young Girl, Long Walk to Freedom |
| History | 3 | Sapiens, The Silk Roads, Guns, Germs, and Steel |
| Science & Technology | 3 | A Brief History of Time, The Selfish Gene, Clean Code |
| Self Help | 3 | Atomic Habits, Deep Work, The 7 Habits of Highly Effective People |
| **Total** | **30** | |

Distribution ranges from 2–4 books per category, averaging 3.0.

---

## 4. Cover Image Verification

All 30 book cover URLs were verified against the Open Library Covers API:

- **Method:** HTTP HEAD request to `https://covers.openlibrary.org/b/isbn/{ISBN}-L.jpg`
- **Criteria:** HTTP 200 status with `image/*` content type
- **Result:** All 30 URLs passed verification
- **Source:** Open Library Covers API (Priority 1 per task requirements)
- **Fabricated URLs:** 0

One book (Long Walk to Freedom) returns `image/gif` instead of `image/jpeg`; this is a valid image format and was accepted.

---

## 5. Data Integrity Verification

### Issue Records (15 total)

All 15 issue records reference books present in the new dataset:

| Book | User | Status |
|------|------|--------|
| Dune | alice | Active |
| The Silent Patient | bob | Active |
| Atomic Habits | carol | Active |
| The Hobbit | david | Active |
| Clean Code | farhan | Active |
| Educated | grace | Active |
| Project Hail Mary | hassan | Active |
| Pride and Prejudice | isabel | Active |
| Sapiens | jonas | Active |
| The Martian | keira | Active |
| The Great Gatsby | alice | Returned |
| Gone Girl | bob | Returned (late, fine paid) |
| Deep Work | carol | Returned (late, fine unpaid) |
| The Alchemist | david | Returned |
| Becoming | emma | Returned (late, fine unpaid) |

### Reservations (10 total)

All 10 reservation records reference books present in the new dataset:

| Book | User | Status |
|------|------|--------|
| The Silent Patient | emma | Pending |
| Atomic Habits | bob | Pending |
| Dune | carol | Pending |
| Clean Code | david | Pending |
| The Martian | isabel | Pending |
| Educated | alice | Approved |
| Sapiens | emma | Approved |
| The Hobbit | farhan | Approved |
| Verity | grace | Rejected |
| It Ends with Us | hassan | Rejected |

### Foreign-Key Safety

No cascading deletes are configured. The seed script uses `_get_or_create_book()` which matches on `(title, author)` — existing database rows for removed books will not be deleted. The seed only creates new rows for books not yet present.

---

## 6. Files Modified

| File | Changes |
|------|---------|
| `backend/app/seed.py` | Updated `BOOKS` list: 6 books added, 6 removed; category comments updated |
| `BOOK_COVER_URLS.md` | Complete rewrite with all 30 verified URLs, change log, and category distribution |
| `data.md` | New report file (this file) |

---

## 7. Static Analysis

| Check | Command | Result |
|-------|---------|--------|
| Ruff lint | `.venv/bin/python -m ruff check app/seed.py` | **All checks passed** |
| Ruff format | `.venv/bin/python -m ruff format --check app/seed.py` | **1 file already formatted** |

---

## 8. Seed Script Behavior

The seed script remains:

- **Idempotent:** Running twice creates no duplicates (matches on `title + author`).
- **Non-destructive:** Never deletes or truncates existing data.
- **Foreign-key safe:** All issue and reservation references resolve to existing book definitions.
- **Enum safe:** All categories use valid `BookCategory` enum values.
- **Inventory consistent:** `available_copies` starts at `total_copies` and is decremented for active issues.
- **Remote-protected:** Refuses to run against non-local databases without `--allow-remote`.

---

## 9. ISBN and Edition Notes

| Book | ISBN | Edition |
|------|------|---------|
| The Great Gatsby | 9780020198819 | Collier Books 1992 paperback |
| The Alchemist | 9780062315007 | HarperOne 2014 paperback |
| 1984 | 9780451524935 | Signet Classics paperback |
| Gone Girl | 9780307588371 | Crown 2012 paperback |
| The Girl with the Dragon Tattoo | 9780307454546 | Vintage 2009 paperback |
| The Silent Patient | 9781250301697 | Celadon 2019 hardcover |
| Verity | 9781538724736 | Grand Central 2018 paperback |
| The Girl on the Train | 9781594634024 | Riverhead 2015 hardcover |
| Pride and Prejudice | 9780141439518 | Penguin Classics 2002 |
| It Ends with Us | 9781501110368 | Atria 2016 hardcover |
| The Notebook | 9780446605236 | Grand Central 2000 paperback |
| Dune | 9780441172719 | Ace 1990 paperback |
| The Martian | 9780553418026 | Crown 2014 paperback |
| Project Hail Mary | 9780593135204 | Ballantine 2021 hardcover |
| Foundation | 9780553293357 | Bantam Spectra 1988 paperback |
| The Hobbit | 9780547928227 | Houghton Mifflin Harcourt 2012 |
| Harry Potter and the Philosopher's Stone | 9780747532699 | Bloomsbury 1997 paperback |
| Educated | 9780399590511 | Random House 2018 hardcover |
| Becoming | 9781524763138 | Crown 2018 hardcover |
| The Diary of a Young Girl | 9780553296983 | Bantam Classics 1993 paperback |
| Long Walk to Freedom | 9780743227354 | Three Rivers Press 1995 paperback |
| Sapiens | 9780062316097 | Harper 2015 paperback |
| The Silk Roads | 9781101912379 | Vintage 2017 paperback |
| Guns, Germs, and Steel | 9780393317558 | W.W. Norton 1997 paperback |
| A Brief History of Time | 9780553380163 | Bantam 1998 paperback |
| The Selfish Gene | 9780198788607 | Oxford University Press 2016 |
| Clean Code | 9780132350884 | Prentice Hall 2008 hardcover |
| Atomic Habits | 9780735211292 | Avery 2018 hardcover |
| Deep Work | 9781455586691 | Grand Central 2016 hardcover |
| The 7 Habits of Highly Effective People | 9781982137274 | Simon & Schuster 30th Anniversary 2020 |

---

## 10. Commands to Verify

To verify the seed script works correctly against a local database:

```bash
cd backend
export SEED_LIBRARIAN_PASSWORD="<strong password>"
export SEED_MEMBER_PASSWORD="<strong password>"

# Dry-run (requires existing schema)
.venv/bin/python -m app.seed --dry-run

# Full seed (local database only)
.venv/bin/python -m app.seed

# For remote Supabase (explicit opt-in)
.venv/bin/python -m app.seed --allow-remote
```

---

## 11. Remaining Notes

- **Mystery and Fantasy categories** have 2 books each (below the average of 3). This is because all books that would bring them to 3 are either referenced by issue/reservation records (must be kept) or were not in the suggested list. Adding more books to these categories would exceed the 30-book target.
- **No `.env` changes** were made. No database was modified. No migrations were run.
- The seed script was **not executed** during this task — only static analysis and import verification were performed.
