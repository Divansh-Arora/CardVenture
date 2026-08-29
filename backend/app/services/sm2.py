"""
SM-2 spaced repetition algorithm.

Plain, dependency-free implementation of the SuperMemo-2 algorithm.
Given a card's current state and a quality rating (0-5) for how well the
user recalled it, returns the updated state.

Quality scale:
  0-2 -> failed recall (reset repetitions, review again soon)
  3   -> hard (correct, but effortful)
  4   -> good (correct, normal effort)
  5   -> easy (correct, trivial)
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class SM2State:
    ease_factor: float
    interval_days: int
    repetitions: int


@dataclass
class SM2Result:
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review_date: datetime


def review(state: SM2State, quality: int) -> SM2Result:
    if quality < 0 or quality > 5:
        raise ValueError("quality must be between 0 and 5")

    ease_factor = state.ease_factor
    interval_days = state.interval_days
    repetitions = state.repetitions

    if quality < 3:
        # Failed recall: reset progress, review again very soon
        repetitions = 0
        interval_days = 1
    else:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = round(interval_days * ease_factor)
        repetitions += 1

    # Update ease factor regardless of pass/fail (standard SM-2 formula)
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(1.3, ease_factor)  # SM-2 floor

    next_review_date = datetime.now(timezone.utc) + timedelta(days=interval_days)

    return SM2Result(
        ease_factor=ease_factor,
        interval_days=interval_days,
        repetitions=repetitions,
        next_review_date=next_review_date,
    )
