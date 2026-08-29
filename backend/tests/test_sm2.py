"""SM-2 algorithm: pure logic, no DB, so tested in isolation from the API."""
import pytest

from app.services import sm2


def test_first_success_sets_interval_to_one_day():
    state = sm2.SM2State(ease_factor=2.5, interval_days=0, repetitions=0)
    result = sm2.review(state, quality=4)
    assert result.interval_days == 1
    assert result.repetitions == 1


def test_second_consecutive_success_sets_interval_to_six_days():
    state = sm2.SM2State(ease_factor=2.5, interval_days=1, repetitions=1)
    result = sm2.review(state, quality=4)
    assert result.interval_days == 6
    assert result.repetitions == 2


def test_third_success_multiplies_by_ease_factor():
    state = sm2.SM2State(ease_factor=2.5, interval_days=6, repetitions=2)
    result = sm2.review(state, quality=4)
    assert result.interval_days == round(6 * 2.5)
    assert result.repetitions == 3


def test_failed_recall_resets_repetitions_and_interval():
    state = sm2.SM2State(ease_factor=2.3, interval_days=40, repetitions=5)
    result = sm2.review(state, quality=1)
    assert result.repetitions == 0
    assert result.interval_days == 1


@pytest.mark.parametrize("quality", [0, 1, 2, 3, 4, 5])
def test_ease_factor_never_drops_below_floor(quality):
    state = sm2.SM2State(ease_factor=1.3, interval_days=1, repetitions=0)
    result = sm2.review(state, quality=quality)
    assert result.ease_factor >= 1.3


def test_easy_rating_increases_ease_factor():
    state = sm2.SM2State(ease_factor=2.5, interval_days=6, repetitions=2)
    result = sm2.review(state, quality=5)
    assert result.ease_factor > 2.5


def test_hard_but_passing_rating_decreases_ease_factor():
    state = sm2.SM2State(ease_factor=2.5, interval_days=6, repetitions=2)
    result = sm2.review(state, quality=3)
    assert result.ease_factor < 2.5


def test_next_review_date_is_in_the_future_by_interval_days():
    from datetime import datetime, timezone

    state = sm2.SM2State(ease_factor=2.5, interval_days=1, repetitions=1)
    before = datetime.now(timezone.utc)
    result = sm2.review(state, quality=4)
    delta = result.next_review_date - before
    assert 5.9 <= delta.total_seconds() / 86400 <= 6.1


@pytest.mark.parametrize("bad_quality", [-1, 6, 10])
def test_out_of_range_quality_raises(bad_quality):
    state = sm2.SM2State(ease_factor=2.5, interval_days=1, repetitions=1)
    with pytest.raises(ValueError):
        sm2.review(state, quality=bad_quality)
