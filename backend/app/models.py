"""
Normalized schema: User -> Deck -> Card -> Review.

Review is a genuine append-only history table (not just state on Card), so
"today's reviews", accuracy, and streaks can be computed later without
having thrown the data away -- separating the *event log* (Review) from
the *current state* (Card's SM-2 fields) is what makes analytics possible
at all, rather than bolting them on after the fact.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base, GUID as UUID


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class CardType(str, enum.Enum):
    definition = "definition"
    formula = "formula"
    relationship = "relationship"
    method = "method"
    worked_example = "worked_example"
    misconception = "misconception"
    edge_case = "edge_case"


class Difficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(), primary_key=True, default=_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)

    decks = relationship("Deck", back_populates="owner", cascade="all, delete-orphan")


class Deck(Base):
    __tablename__ = "decks"

    id = Column(UUID(), primary_key=True, default=_uuid)
    owner_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    source_filename = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    # Last time any card in this deck was reviewed -- lets the frontend
    # offer a "resume studying" entry point (most-recently-studied deck
    # first) instead of only ever sorting by upload date. Set in
    # routers/cards.py whenever a review is submitted for one of this
    # deck's cards, in the same transaction as the review itself.
    last_studied_at = Column(DateTime(timezone=True), nullable=True, index=True)

    owner = relationship("User", back_populates="decks")
    cards = relationship("Card", back_populates="deck", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"

    id = Column(UUID(), primary_key=True, default=_uuid)
    deck_id = Column(UUID(), ForeignKey("decks.id"), nullable=False, index=True)

    # --- content ---
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)  # extra context beyond the answer itself
    card_type = Column(SAEnum(CardType, name="card_type"), nullable=False, default=CardType.definition)
    difficulty = Column(SAEnum(Difficulty, name="difficulty"), nullable=False, default=Difficulty.medium)
    topic = Column(String, nullable=True)          # e.g. "Quadratic Equations"
    source_page = Column(Integer, nullable=True)   # page in the source PDF this came from

    # --- SM-2 spaced repetition state (current state, not history) ---
    ease_factor = Column(Float, nullable=False, default=2.5)
    interval_days = Column(Integer, nullable=False, default=0)
    repetitions = Column(Integer, nullable=False, default=0)
    next_review_date = Column(DateTime(timezone=True), default=_now, index=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_now)

    deck = relationship("Deck", back_populates="cards")
    reviews = relationship("Review", back_populates="card", cascade="all, delete-orphan")


class Review(Base):
    """
    Append-only log of every review event. Card holds the *current* SM-2
    state; Review holds the *history* that produced it, which is what lets
    us answer "how many reviews today" or "what's my accuracy" without
    reconstructing it from side effects.
    """
    __tablename__ = "reviews"

    id = Column(UUID(), primary_key=True, default=_uuid)
    card_id = Column(UUID(), ForeignKey("cards.id"), nullable=False, index=True)

    quality = Column(Integer, nullable=False)            # 0-5, as submitted
    previous_interval = Column(Integer, nullable=False)   # interval_days before this review
    new_interval = Column(Integer, nullable=False)        # interval_days after this review
    reviewed_at = Column(DateTime(timezone=True), default=_now, index=True)

    card = relationship("Card", back_populates="reviews")
