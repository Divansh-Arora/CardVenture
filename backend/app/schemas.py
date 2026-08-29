"""
Pydantic schemas: the typed contract between frontend and backend.
"""
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field

from app.models import CardType, Difficulty


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Cards ----------

class CardOut(BaseModel):
    id: str
    question: str
    answer: str
    explanation: str | None
    card_type: CardType
    difficulty: Difficulty
    topic: str | None
    source_page: int | None

    ease_factor: float
    interval_days: int
    repetitions: int
    next_review_date: datetime
    last_reviewed_at: datetime | None

    class Config:
        from_attributes = True


class ReviewSubmit(BaseModel):
    # SM-2 quality rating: 0-2 = fail/again, 3 = hard, 4 = good, 5 = easy
    quality: int = Field(ge=0, le=5)


class ReviewOut(BaseModel):
    id: str
    card_id: str
    quality: int
    previous_interval: int
    new_interval: int
    reviewed_at: datetime

    class Config:
        from_attributes = True


# ---------- Decks ----------

class DeckOut(BaseModel):
    id: str
    title: str
    source_filename: str | None
    created_at: datetime
    last_studied_at: datetime | None = None
    card_count: int = 0

    class Config:
        from_attributes = True


class DeckDetailOut(DeckOut):
    cards: list[CardOut] = []


class DeckProgress(BaseModel):
    mastered: int
    shaky: int
    upcoming: int
    total: int


class DeckTypeBreakdown(BaseModel):
    """Card counts per category — surfaces the systematic coverage the
    generation pipeline aims for (definitions, formulas, relationships,
    methods, worked examples, misconceptions, edge cases)."""
    card_type: CardType
    count: int


# ---------- Analytics ----------

class AnalyticsSummary(BaseModel):
    date: date
    reviews_today: int
    correct_today: int
    accuracy_pct: float
    cards_mastered: int
    cards_struggling: int
    total_cards: int
