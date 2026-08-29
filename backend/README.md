# Flashcard Engine — Backend

FastAPI backend for the Flashcard Engine. Handles auth (JWT), a multi-stage
PDF-to-flashcard generation pipeline, review history, and SM-2 spaced
repetition.

## Stack

- **FastAPI** — API layer
- **PostgreSQL + SQLAlchemy** — data layer
- **JWT auth** (python-jose + passlib/bcrypt) — users, login, protected routes
- **NVIDIA Nemotron 3 Ultra** (via build.nvidia.com, OpenAI-compatible SDK) — card generation
- **pypdf** — PDF text extraction
- **SM-2 algorithm** — plain-Python spaced repetition logic (`app/services/sm2.py`)

## Generation pipeline

The original approach (extract everything → take the first 60,000
characters → one LLM call) silently truncated anything past that cutoff
and produced whatever categories of card the model felt like. It's now:

```
PDF
  → extract_pages          per-page text (app/services/pdf_service.py)
  → chunk_pages             group pages into ~3,500-char chunks, preferring
                             to break at detected section headings
                             (app/services/chunking.py)
  → generate per chunk       one LLM call per chunk, prompted to
                             systematically cover 7 categories: definitions,
                             formulas, relationships, methods, worked
                             examples, misconceptions, edge cases
                             (app/services/llm_service.py)
  → merge                   concatenate every chunk's cards
  → deduplicate_cards        collapse near-duplicate questions across
                             chunks, keeping the more complete version
                             (app/services/dedup.py)
  → quality_check            filter thin/malformed cards, default invalid
                             categories rather than reject the whole card
                             (app/services/quality.py)
  → final deck
```

Section detection is a lightweight heuristic (short, title-cased lines
with no trailing punctuation) rather than true layout analysis, since
`pypdf` text extraction doesn't preserve font size/weight — noted as the
natural place to upgrade (e.g. a PDF library that exposes layout info) if
this needs to get more precise. Quality-checking is rule-based rather than
a second LLM pass, trading a small amount of precision for real latency
and cost savings on every upload — the natural next step if it needs to
catch more subtle issues.

Each chunk call is spaced ~1.5s apart to stay comfortably under NVIDIA's
free-tier rate limit even on long documents with many chunks.

## Data model

```
User
 └── Deck
      └── Card
           ├── question, answer, explanation
           ├── card_type   (definition / formula / relationship / method /
           │                worked_example / misconception / edge_case)
           ├── difficulty  (easy / medium / hard)
           ├── topic, source_page
           ├── ease_factor, interval_days, repetitions   ← current SM-2 state
           ├── next_review_date, last_reviewed_at
           └── Review[]     ← append-only history, one row per review event
                ├── quality, previous_interval, new_interval, reviewed_at
```

Card holds *current* SM-2 state (what you need to decide what's due next).
Review is a separate, append-only *history* of every review event — that
split is what makes analytics possible: "today's reviews" or "accuracy"
can't be computed if the state that produced them was overwritten in
place with nowhere else to look.

## Project layout

```
app/
  main.py              FastAPI app, CORS, router wiring, /health
  config.py            Settings loaded from environment / .env
  database.py           SQLAlchemy engine/session
  models.py            User, Deck, Card, Review tables + CardType/Difficulty enums
  schemas.py            Pydantic request/response contracts
  auth.py               Password hashing, JWT issue/verify, get_current_user
  routers/
    auth.py             /auth/register, /auth/login, /auth/me
    decks.py             upload, list/get/delete, progress, category breakdown
    cards.py             due cards, submit review (+ history), card history
    analytics.py          today's reviews / accuracy / mastered / struggling
  services/
    pdf_service.py        PDF -> per-page text
    chunking.py            pages -> section-aware chunks
    llm_service.py          chunk -> cards, plus the full pipeline orchestrator
    dedup.py                cross-chunk near-duplicate removal
    quality.py               rule-based quality filter
    sm2.py                    SM-2 algorithm (pure logic, no DB/HTTP)
```

## Local setup

1. Create a Postgres database (e.g. at neon.com — free, no expiring tier) and
   copy its connection string.
2. Get an NVIDIA API key at build.nvidia.com (Prototype tab on the Nemotron
   model page).
3. Copy `.env.example` to `.env` and fill in `DATABASE_URL`, `NVIDIA_API_KEY`,
   and a random `JWT_SECRET` (generate one with
   `python -c "import secrets; print(secrets.token_hex(32))"`).
4. Install dependencies and run:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

5. Visit `http://localhost:8000/docs` for interactive API docs.

Tables are created automatically on startup — no separate migration step
needed for a project this size.

## API overview

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/auth/register` | POST | – | Create an account |
| `/auth/login` | POST | – | Get a JWT access token |
| `/auth/me` | GET | ✔ | Current user info |
| `/decks/upload` | POST | ✔ | Upload a PDF, run the full generation pipeline |
| `/decks` | GET | ✔ | List your decks |
| `/decks/{id}` | GET | ✔ | Deck detail + all cards |
| `/decks/{id}/progress` | GET | ✔ | Mastered / shaky / upcoming counts |
| `/decks/{id}/breakdown` | GET | ✔ | Card counts per category (definition/formula/…) |
| `/decks/{id}` | DELETE | ✔ | Delete a deck |
| `/decks/{id}/due` | GET | ✔ | Cards due for review right now |
| `/decks/{id}/analytics` | GET | ✔ | Today's reviews/accuracy/mastered/struggling for this deck |
| `/cards/{id}/review` | POST | ✔ | Submit a review rating (0-5), applies SM-2, logs history |
| `/cards/{id}/history` | GET | ✔ | Full review history for one card |
| `/analytics/today` | GET | ✔ | Same as deck analytics, aggregated across all your decks |
| `/health` | GET | – | Liveness check |

Protected routes expect `Authorization: Bearer <token>` from `/auth/login`.

## Deploying (Render / Railway)

1. Push this `backend/` folder to your GitHub repo.
2. Create a new Web Service pointed at it (both platforms auto-detect the
   `Dockerfile`, or you can set the start command manually to
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
3. Set environment variables in the host's dashboard: `DATABASE_URL`,
   `NVIDIA_API_KEY`, `JWT_SECRET`, `JWT_ALGORITHM`, `CORS_ORIGINS`
   (include your deployed frontend's URL once you have it).
4. **Never** commit `.env` — it's already in `.gitignore`.

## Security notes

- `NVIDIA_API_KEY` is only ever read server-side (`app/config.py` →
  `app/services/llm_service.py`) — it never reaches the frontend or a
  response body.
- Passwords are hashed with bcrypt, never stored or logged in plain text.
- JWTs are signed with `JWT_SECRET` — treat it like a password; rotate it
  if it's ever exposed.

