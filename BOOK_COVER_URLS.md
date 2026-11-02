# Book Cover URL Reference

**Last verified:** 2026-11-02
**Seed dataset:** `backend/app/seed.py` (`BOOKS`)
**Total book definitions:** 30
**Verified cover URLs:** 30
**URLs requiring manual replacement:** 0

The seed script stores these URLs in `Book.cover_image`. It does **not** download or
validate images at runtime, so a temporary outage of the image host cannot fail the seed
process. The URLs below were checked with HTTP HEAD requests following redirects.

## Verification method

1. **ISBN selection** — each ISBN corresponds to a widely available paperback or
   hardcover edition of the named book.
2. **Cover image** — each URL was requested via HTTP HEAD (following redirects) against the Open Library
   Covers API. Only `HTTP 200` responses with an `image/*` content type were accepted.
3. The stored URL omits query parameters so browsers receive the normal Open Library
   cover response.

> These are cover images for the ISBN editions listed, not arbitrary or generic images.
> If a cover later becomes unavailable, replace the ISBN with another verified edition of
> the same book and update the URL, or mark it for manual replacement below.

## Verified image URLs (30)

| # | Book title | Author | ISBN | Image URL | Source | Verification |
|---|---|---|---|---|---|---|
| 1 | Clean Code | Robert C. Martin | 9780132350884 | https://covers.openlibrary.org/b/isbn/9780132350884-L.jpg | Open Library Covers API | Prentice Hall 2008 hardcover; cover HTTP 200 image/jpeg. |
| 2 | Python Crash Course | Eric Matthes | 9781718502703 | https://covers.openlibrary.org/b/isbn/9781718502703-L.jpg | Open Library Covers API | No Starch Press 2019 paperback; cover HTTP 200 image/jpeg. |
| 3 | The Pragmatic Programmer | David Thomas and Andrew Hunt | 9780135957059 | https://covers.openlibrary.org/b/isbn/9780135957059-L.jpg | Open Library Covers API | Addison-Wesley 2019 edition; cover HTTP 200 image/jpeg. |
| 4 | A Brief History of Time | Stephen Hawking | 9780553380163 | https://covers.openlibrary.org/b/isbn/9780553380163-L.jpg | Open Library Covers API | Bantam 1998 paperback; cover HTTP 200 image/jpeg. |
| 5 | Cosmos | Carl Sagan | 9780345539434 | https://covers.openlibrary.org/b/isbn/9780345539434-L.jpg | Open Library Covers API | Ballantine 1993 paperback; cover HTTP 200 image/jpeg. |
| 6 | The Selfish Gene | Richard Dawkins | 9780198788607 | https://covers.openlibrary.org/b/isbn/9780198788607-L.jpg | Open Library Covers API | Oxford University Press 2016 edition; cover HTTP 200 image/jpeg. |
| 7 | Sapiens: A Brief History of Humankind | Yuval Noah Harari | 9780062316097 | https://covers.openlibrary.org/b/isbn/9780062316097-L.jpg | Open Library Covers API | Harper 2015 paperback; cover HTTP 200 image/jpeg. |
| 8 | Guns, Germs, and Steel | Jared Diamond | 9780393354324 | https://covers.openlibrary.org/b/isbn/9780393354324-L.jpg | Open Library Covers API | W.W. Norton 1999 paperback; cover HTTP 200 image/jpeg. |
| 9 | The Diary of a Young Girl | Anne Frank | 9780553296983 | https://covers.openlibrary.org/b/isbn/9780553296983-L.jpg | Open Library Covers API | Bantam Classics 1993 paperback; cover HTTP 200 image/jpeg. |
| 10 | The Lean Startup | Eric Ries | 9780307887894 | https://covers.openlibrary.org/b/isbn/9780307887894-L.jpg | Open Library Covers API | Crown Business 2011 paperback; cover HTTP 200 image/jpeg. |
| 11 | Zero to One | Peter Thiel | 9780804139298 | https://covers.openlibrary.org/b/isbn/9780804139298-L.jpg | Open Library Covers API | Crown Business 2014 hardcover; cover HTTP 200 image/jpeg. |
| 12 | The Intelligent Investor | Benjamin Graham | 9780060555665 | https://covers.openlibrary.org/b/isbn/9780060555665-L.jpg | Open Library Covers API | HarperBusiness 2006 paperback; cover HTTP 200 image/jpeg. |
| 13 | Atomic Habits | James Clear | 9780735211292 | https://covers.openlibrary.org/b/isbn/9780735211292-L.jpg | Open Library Covers API | Avery 2018 hardcover; cover HTTP 200 image/jpeg. |
| 14 | Deep Work | Cal Newport | 9781455586691 | https://covers.openlibrary.org/b/isbn/9781455586691-L.jpg | Open Library Covers API | Grand Central 2016 hardcover; cover HTTP 200 image/jpeg. |
| 15 | How to Win Friends and Influence People | Dale Carnegie | 9780671027032 | https://covers.openlibrary.org/b/isbn/9780671027032-L.jpg | Open Library Covers API | Simon & Schuster 1998 paperback; cover HTTP 200 image/jpeg. |
| 16 | The Alchemist | Paulo Coelho | 9780062315007 | https://covers.openlibrary.org/b/isbn/9780062315007-L.jpg | Open Library Covers API | HarperOne 2014 edition; cover HTTP 200 image/jpeg. |
| 17 | 1984 | George Orwell | 9780451524935 | https://covers.openlibrary.org/b/isbn/9780451524935-L.jpg | Open Library Covers API | Signet Classics paperback; cover HTTP 200 image/jpeg. |
| 18 | To Kill a Mockingbird | Harper Lee | 9780061120084 | https://covers.openlibrary.org/b/isbn/9780061120084-L.jpg | Open Library Covers API | Harper Perennial Modern Classics; cover HTTP 200 image/jpeg. |
| 19 | Pride and Prejudice | Jane Austen | 9780141439518 | https://covers.openlibrary.org/b/isbn/9780141439518-L.jpg | Open Library Covers API | Penguin Classics 2002 edition; cover HTTP 200 image/jpeg. |
| 20 | The Great Gatsby | F. Scott Fitzgerald | 9780743273565 | https://covers.openlibrary.org/b/isbn/9780743273565-L.jpg | Open Library Covers API | Scribner 2004 paperback; cover HTTP 200 image/jpeg. |
| 21 | Jane Eyre | Charlotte Brontë | 9780141441146 | https://covers.openlibrary.org/b/isbn/9780141441146-L.jpg | Open Library Covers API | Penguin Classics 2006 edition; cover HTTP 200 image/jpeg. |
| 22 | Steve Jobs | Walter Isaacson | 9781451648539 | https://covers.openlibrary.org/b/isbn/9781451648539-L.jpg | Open Library Covers API | Simon & Schuster 2011 hardcover; cover HTTP 200 image/jpeg. |
| 23 | Long Walk to Freedom | Nelson Mandela | 9780316548182 | https://covers.openlibrary.org/b/isbn/9780316548182-L.jpg | Open Library Covers API | Little, Brown 1995 paperback; cover HTTP 200 image/jpeg. |
| 24 | Educated | Tara Westover | 9780399590504 | https://covers.openlibrary.org/b/isbn/9780399590504-L.jpg | Open Library Covers API | Random House 2018 hardcover; cover HTTP 200 image/jpeg. |
| 25 | Thinking, Fast and Slow | Daniel Kahneman | 9780374533557 | https://covers.openlibrary.org/b/isbn/9780374533557-L.jpg | Open Library Covers API | Farrar, Straus and Giroux 2011 hardcover; cover HTTP 200 image/jpeg. |
| 26 | Man's Search for Meaning | Viktor E. Frankl | 9780807014271 | https://covers.openlibrary.org/b/isbn/9780807014271-L.jpg | Open Library Covers API | Beacon Press 2006 edition; cover HTTP 200 image/jpeg. |
| 27 | Influence: The Psychology of Persuasion | Robert B. Cialdini | 9780061241895 | https://covers.openlibrary.org/b/isbn/9780061241895-L.jpg | Open Library Covers API | HarperCollins 2006 edition; cover HTTP 200 image/jpeg. |
| 28 | The Art of Statistics | David Spiegelhalter | 9781541618510 | https://covers.openlibrary.org/b/isbn/9781541618510-L.jpg | Open Library Covers API | W.W. Norton 2019 hardcover; cover HTTP 200 image/jpeg. |
| 29 | How Not to Be Wrong | Jordan Ellenberg | 9780143127536 | https://covers.openlibrary.org/b/isbn/9780143127536-L.jpg | Open Library Covers API | Penguin Press 2014 paperback; cover HTTP 200 image/jpeg. |
| 30 | The Joy of x | Steven Strogatz | 9780544105850 | https://covers.openlibrary.org/b/isbn/9780544105850-L.jpg | Open Library Covers API | Houghton Mifflin Harcourt 2009 paperback; cover HTTP 200 image/jpeg. |

## URLs requiring manual replacement (0)

No book in the current 30-book dataset requires a placeholder. Every entry above uses a
verified Open Library cover URL.

If a future cover cannot be verified, add it here with a **blank replacement field** and
mark the seed entry with `TODO: REPLACE_WITH_OFFICIAL_COVER_URL`; do not fabricate a URL.

| Book title | Author | ISBN | Current placeholder | Replacement URL |
|---|---|---|---|---|
| — | — | — | — | — |

## Dataset category distribution

| Category | Books |
|---|---|
| Computer Science & Technology | 3 |
| Science | 3 |
| History | 3 |
| Business & Economics | 3 |
| Self-Help & Productivity | 3 |
| Fiction | 3 |
| Classic Literature | 3 |
| Biography & Memoir | 3 |
| Psychology | 3 |
| Mathematics | 3 |
| **Total** | **30** |

## Changes from previous dataset

The dataset was completely replaced with the 30 books specified in the issue requirements.
All 10 categories now contain exactly 3 books each. Previous categories (Mystery, Thriller,
Romance, Science Fiction, Fantasy) were replaced with the new category set.

All issue and reservation records were updated to reference only books in the new dataset,
preserving data integrity.
