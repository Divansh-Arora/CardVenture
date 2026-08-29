from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.services import sm2

router = APIRouter(tags=["cards"])


@router.get("/decks/{deck_id}/due", response_model=list[schemas.CardOut])
def get_due_cards(
    deck_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if not deck or deck.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Deck not found.")

    now = datetime.now(timezone.utc)
    due_cards = (
        db.query(models.Card)
        .filter(models.Card.deck_id == deck_id, models.Card.next_review_date <= now)
        .order_by(models.Card.next_review_date.asc())
        .all()
    )
    return due_cards


@router.post("/cards/{card_id}/review", response_model=schemas.CardOut)
def submit_review(
    card_id: str,
    payload: schemas.ReviewSubmit,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    card = (
        db.query(models.Card)
        .join(models.Deck)
        .filter(models.Card.id == card_id, models.Deck.owner_id == current_user.id)
        .first()
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found.")

    previous_interval = card.interval_days
    now = datetime.now(timezone.utc)

    state = sm2.SM2State(
        ease_factor=card.ease_factor,
        interval_days=card.interval_days,
        repetitions=card.repetitions,
    )
    result = sm2.review(state, payload.quality)

    card.ease_factor = result.ease_factor
    card.interval_days = result.interval_days
    card.repetitions = result.repetitions
    card.next_review_date = result.next_review_date
    card.last_reviewed_at = now

    # Append to history *in the same transaction* as the state update, so
    # the two can never drift out of sync with each other.
    db.add(
        models.Review(
            card_id=card.id,
            quality=payload.quality,
            previous_interval=previous_interval,
            new_interval=result.interval_days,
        )
    )

    # Same transaction, same timestamp: the deck's "last studied" marker
    # (used to power a "resume studying" entry point) can't drift out of
    # sync with the review that produced it either.
    card.deck.last_studied_at = now

    db.commit()
    db.refresh(card)
    return card


@router.get("/cards/{card_id}/history", response_model=list[schemas.ReviewOut])
def card_history(
    card_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    card = (
        db.query(models.Card)
        .join(models.Deck)
        .filter(models.Card.id == card_id, models.Deck.owner_id == current_user.id)
        .first()
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found.")

    return (
        db.query(models.Review)
        .filter(models.Review.card_id == card_id)
        .order_by(models.Review.reviewed_at.desc())
        .all()
    )
