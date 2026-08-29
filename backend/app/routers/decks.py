from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.services.pdf_service import extract_pages
from app.services.llm_service import generate_deck_cards

router = APIRouter(prefix="/decks", tags=["decks"])


@router.post("/upload", response_model=schemas.DeckDetailOut, status_code=201)
def upload_deck(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = file.file.read()

    try:
        pages = extract_pages(pdf_bytes)
        generated = generate_deck_cards(pages)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:  # LLM/network failure - don't leak internals
        raise HTTPException(
            status_code=502,
            detail="Card generation failed. Please try again in a moment.",
        ) from exc

    deck = models.Deck(owner_id=current_user.id, title=title, source_filename=file.filename)
    db.add(deck)
    db.flush()  # get deck.id before creating cards

    for item in generated:
        db.add(
            models.Card(
                deck_id=deck.id,
                question=item["question"],
                answer=item["answer"],
                explanation=item.get("explanation"),
                card_type=item["card_type"],
                difficulty=item["difficulty"],
                topic=item.get("topic"),
                source_page=item.get("source_page"),
            )
        )

    db.commit()
    db.refresh(deck)
    return _deck_to_detail(deck)


@router.get("", response_model=list[schemas.DeckOut])
def list_decks(
    q: str | None = Query(
        default=None, description="Filter decks by title or source filename."
    ),
    sort: str = Query(
        default="recent",
        pattern="^(recent|last_studied)$",
        description=(
            "'recent' orders by upload date (default). 'last_studied' "
            "surfaces decks with review activity first -- ordered by "
            "last_studied_at descending, decks never studied last -- for "
            "a 'resume studying' dashboard entry point."
        ),
    ),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = (
        db.query(models.Deck, func.count(models.Card.id).label("card_count"))
        .outerjoin(models.Card)
        .filter(models.Deck.owner_id == current_user.id)
    )

    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(models.Deck.title.ilike(like), models.Deck.source_filename.ilike(like))
        )

    query = query.group_by(models.Deck.id)

    if sort == "last_studied":
        # NULLS LAST isn't portable across every backend SQLAlchemy might
        # sit on top of (SQLite included, which this test suite runs
        # against), so it's expressed with a boolean sort key instead of
        # relying on database-specific NULLS LAST syntax.
        query = query.order_by(
            models.Deck.last_studied_at.is_(None), models.Deck.last_studied_at.desc()
        )
    else:
        query = query.order_by(models.Deck.created_at.desc())

    result = []
    for deck, card_count in query.all():
        out = schemas.DeckOut.model_validate(deck)
        out.card_count = card_count
        result.append(out)
    return result


@router.get("/{deck_id}", response_model=schemas.DeckDetailOut)
def get_deck(
    deck_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    deck = _get_owned_deck(db, deck_id, current_user.id)
    return _deck_to_detail(deck)


@router.get("/{deck_id}/progress", response_model=schemas.DeckProgress)
def deck_progress(
    deck_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    deck = _get_owned_deck(db, deck_id, current_user.id)

    mastered = shaky = upcoming = 0
    for card in deck.cards:
        if card.repetitions >= 3 and card.ease_factor >= 2.3:
            mastered += 1
        elif card.repetitions == 0 or card.ease_factor < 2.0:
            shaky += 1
        else:
            upcoming += 1

    return schemas.DeckProgress(
        mastered=mastered, shaky=shaky, upcoming=upcoming, total=len(deck.cards)
    )


@router.get("/{deck_id}/breakdown", response_model=list[schemas.DeckTypeBreakdown])
def deck_type_breakdown(
    deck_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Card counts per category -- shows whether generation actually
    achieved comprehensive coverage (definitions, formulas, relationships,
    methods, worked examples, misconceptions, edge cases) rather than
    producing a lopsided deck."""
    deck = _get_owned_deck(db, deck_id, current_user.id)

    counts: dict[str, int] = {}
    for card in deck.cards:
        key = card.card_type.value if hasattr(card.card_type, "value") else card.card_type
        counts[key] = counts.get(key, 0) + 1

    return [
        schemas.DeckTypeBreakdown(card_type=card_type, count=count)
        for card_type, count in sorted(counts.items(), key=lambda kv: -kv[1])
    ]


@router.get("/{deck_id}/cards/search", response_model=list[schemas.CardOut])
def search_deck_cards(
    deck_id: str,
    q: str = Query(min_length=1, description="Text to search for in this deck's cards."),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Search question/answer/explanation/topic text within one deck --
    e.g. jumping straight to "the card about entropy" in a 200-card deck
    instead of scrolling to find it."""
    deck = _get_owned_deck(db, deck_id, current_user.id)

    like = f"%{q.strip()}%"
    return (
        db.query(models.Card)
        .filter(
            models.Card.deck_id == deck.id,
            or_(
                models.Card.question.ilike(like),
                models.Card.answer.ilike(like),
                models.Card.explanation.ilike(like),
                models.Card.topic.ilike(like),
            ),
        )
        .order_by(models.Card.created_at.asc())
        .all()
    )


@router.delete("/{deck_id}", status_code=204)
def delete_deck(
    deck_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    deck = _get_owned_deck(db, deck_id, current_user.id)
    db.delete(deck)
    db.commit()


# ---------- helpers ----------

def _get_owned_deck(db: Session, deck_id: str, owner_id: str) -> models.Deck:
    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if not deck or deck.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Deck not found.")
    return deck


def _deck_to_detail(deck: models.Deck) -> schemas.DeckDetailOut:
    out = schemas.DeckDetailOut.model_validate(deck)
    out.card_count = len(deck.cards)
    out.cards = [schemas.CardOut.model_validate(c) for c in deck.cards]
    return out
