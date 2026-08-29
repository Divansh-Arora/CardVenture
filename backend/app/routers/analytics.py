from datetime import datetime, timezone, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(tags=["analytics"])


def _today_bounds() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def _summarize(db: Session, card_ids_query) -> schemas.AnalyticsSummary:
    start, end = _today_bounds()

    todays_reviews = (
        db.query(models.Review)
        .filter(
            models.Review.card_id.in_(card_ids_query),
            models.Review.reviewed_at >= start,
            models.Review.reviewed_at <= end,
        )
        .all()
    )

    reviews_today = len(todays_reviews)
    correct_today = sum(1 for r in todays_reviews if r.quality >= 3)
    accuracy_pct = round((correct_today / reviews_today) * 100, 1) if reviews_today else 0.0

    cards = db.query(models.Card).filter(models.Card.id.in_(card_ids_query)).all()
    mastered = sum(1 for c in cards if c.repetitions >= 3 and c.ease_factor >= 2.3)
    struggling = sum(1 for c in cards if c.repetitions == 0 or c.ease_factor < 2.0)

    return schemas.AnalyticsSummary(
        date=date.today(),
        reviews_today=reviews_today,
        correct_today=correct_today,
        accuracy_pct=accuracy_pct,
        cards_mastered=mastered,
        cards_struggling=struggling,
        total_cards=len(cards),
    )


@router.get("/decks/{deck_id}/analytics", response_model=schemas.AnalyticsSummary)
def deck_analytics(
    deck_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if not deck or deck.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Deck not found.")

    card_ids = db.query(models.Card.id).filter(models.Card.deck_id == deck_id)
    return _summarize(db, card_ids)


@router.get("/analytics/today", response_model=schemas.AnalyticsSummary)
def today_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Aggregated across every deck the current user owns -- a dashboard-
    level view of today's study session, not tied to any single deck."""
    card_ids = (
        db.query(models.Card.id)
        .join(models.Deck)
        .filter(models.Deck.owner_id == current_user.id)
    )
    return _summarize(db, card_ids)
