"""Tests for date comparison functionality in the expression language."""

from datetime import datetime, timedelta, timezone

from hypothesis import given, strategies as st, settings
import pytest

from dilemma.errors.exc import DateTimeError
from dilemma.lang import evaluate
from dilemma.dates import DateMethods
from dilemma.utils import ensure_datetime, create_timedelta


def test_date_is_comparisons():
    """Test 'is $past/future/today' date comparisons."""
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)
    today_different_time = datetime(
        now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc
    )

    variables = {
        "past_date": yesterday,
        "future_date": tomorrow,
        "today_date": today_different_time,
    }

    # Test 'is $past'
    assert evaluate("past_date is $past", variables) is True
    assert evaluate("future_date is $past", variables) is False

    # Test 'is $future'
    assert evaluate("future_date is $future", variables) is True
    assert evaluate("past_date is $future", variables) is False

    # Test 'is $today'
    assert evaluate("today_date is $today", variables) is True
    assert evaluate("past_date is $today", variables) is False
    assert evaluate("future_date is $today", variables) is False


def test_date_within_comparisons():
    """Test 'within' time period date comparisons."""
    now = datetime.now(timezone.utc)  # Ensure consistency with the method's 'now'

    variables = {
        "just_now": now + timedelta(minutes=5),  # Future date
        "hour_later": now + timedelta(hours=1),  # Future date
        "day_later": now + timedelta(days=1),  # Future date
        "week_later": now + timedelta(days=6),  # Future date
        "month_later": now + timedelta(days=25),  # Future date
        "year_later": now + timedelta(days=364),  # Future date
        "$now": now,  # Pass the fixed 'now' value explicitly
    }

    # Test various time periods
    assert evaluate("just_now upcoming within 1 hour", variables) is True
    assert evaluate("hour_later upcoming within 2 hours", variables) is True
    assert evaluate("hour_later upcoming within 30 minutes", variables) is False

    assert evaluate("day_later upcoming within 2 days", variables) is True
    assert evaluate("day_later upcoming within 12 hours", variables) is False

    assert evaluate("week_later upcoming within 1 week", variables) is True
    assert evaluate("week_later upcoming within 5 days", variables) is False

    assert evaluate("month_later upcoming within 1 month", variables) is True
    assert evaluate("month_later upcoming within 20 days", variables) is False

    assert evaluate("year_later upcoming within 1 year", variables) is True
    assert evaluate("year_later upcoming within 2 years", variables) is True


def test_date_older_than_comparisons():
    """Test 'older than' time period date comparisons."""
    now = datetime.now(timezone.utc)

    variables = {
        "hour_ago": now - timedelta(hours=3),
        "day_ago": now - timedelta(days=2),
        "week_ago": now - timedelta(days=10),
        "month_ago": now - timedelta(days=40),
        "year_ago": now - timedelta(days=400),
    }

    # Test various time periods
    assert evaluate("hour_ago older than 1 hour", variables) is True
    assert evaluate("hour_ago older than 4 hours", variables) is False

    assert evaluate("day_ago older than 1 day", variables) is True
    assert evaluate("day_ago older than 3 days", variables) is False

    assert evaluate("week_ago older than 1 week", variables) is True
    assert evaluate("week_ago older than 2 weeks", variables) is False

    assert evaluate("month_ago older than 1 month", variables) is True
    assert evaluate("month_ago older than 2 months", variables) is False

    assert evaluate("year_ago older than 1 year", variables) is True


def test_date_before_after_comparisons():
    """Test date-to-date comparison with 'before' and 'after'."""
    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    mid_date = datetime(2024, 6, 15, tzinfo=timezone.utc)
    end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

    variables = {"start": start_date, "middle": mid_date, "end": end_date}

    # Test 'before'
    assert evaluate("start before middle", variables) is True
    assert evaluate("middle before start", variables) is False
    assert evaluate("start before end", variables) is True

    # Test 'after'
    assert evaluate("middle after start", variables) is True
    assert evaluate("start after middle", variables) is False
    assert evaluate("end after start", variables) is True


def test_date_same_day_comparison():
    """Test 'same_day_as' date comparison."""
    day1_morning = datetime(2024, 5, 10, 8, 30, tzinfo=timezone.utc)
    day1_evening = datetime(2024, 5, 10, 20, 15, tzinfo=timezone.utc)
    day2 = datetime(2024, 5, 11, 12, 0, tzinfo=timezone.utc)

    variables = {"morning": day1_morning, "evening": day1_evening, "next_day": day2}

    # Test same day
    assert evaluate("morning same_day_as evening", variables) is True
    assert evaluate("morning same_day_as next_day", variables) is False
    assert evaluate("evening same_day_as next_day", variables) is False


def test_string_to_date_conversion():
    """Test conversion of string dates in expressions."""
    now = datetime.now(timezone.utc)
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    variables = {"date_string": yesterday, "future_string": tomorrow}

    # Test with string dates
    assert evaluate("date_string is $past", variables) is True
    assert evaluate("future_string is $future", variables) is True
    assert evaluate("date_string before future_string", variables) is True


def test_timestamp_to_date_conversion():
    """Test conversion of timestamp values in expressions."""
    now_ts = datetime.now(timezone.utc).timestamp()
    yesterday_ts = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
    tomorrow_ts = (datetime.now(timezone.utc) + timedelta(days=1)).timestamp()

    variables = {"now": now_ts, "yesterday": yesterday_ts, "tomorrow": tomorrow_ts}

    # Test with timestamps
    assert evaluate("yesterday is $past", variables) is True
    assert evaluate("tomorrow is $future", variables) is True
    assert evaluate("yesterday before tomorrow", variables) is True
    assert evaluate("yesterday older than 12 hours", variables) is True


def test_complex_date_expressions():
    """Test combining date comparisons with logical operations."""
    now = datetime.now(timezone.utc)

    variables = {
        "start_date": now - timedelta(days=30),
        "end_date": now + timedelta(days=10),
        "signup_date": now - timedelta(days=15),
        "last_login": now - timedelta(hours=25),
    }

    # Test combined expressions
    assert evaluate("start_date is $past and end_date is $future", variables) is True
    assert (
        evaluate("signup_date older than 7 days and last_login older than 24 hours", variables)
        is True
    )
    assert (
        evaluate(
            "signup_date after start_date and signup_date before end_date", variables
        )
        is True
    )
    assert (
        evaluate(
            "signup_date older than 2 days or last_login older than 3 hours", variables
        )
        is True
    )


def test_date_conversion_edge_cases():
    """Test edge cases in date conversion."""
    # Test timestamp conversion
    timestamp = datetime.now(timezone.utc).timestamp()
    variables = {"timestamp": timestamp}
    assert evaluate("timestamp is $past or timestamp is $future", variables) is True

    # Test parsing different string formats
    variables = {"iso_date": "2023-05-10T14:30:00Z", "simple_date": "2023-05-10"}
    assert evaluate("iso_date before '2024-01-01'", variables) is True
    assert evaluate("simple_date before '2024-01-01'", variables) is True


def test_date_error_handling():
    """Test error handling for invalid date formats."""
    # Test invalid string format
    variables = {"bad_date": "not-a-date"}
    with pytest.raises(DateTimeError, match="Could not parse date string"):
        evaluate("bad_date is $past", variables)

    # Test invalid type conversion - update the expected error message
    variables = {"obj": {}}
    with pytest.raises(
        DateTimeError, match="Cannot convert"
    ):  # Changed from "Unsupported type"
        evaluate("obj is $past", variables)

    # Test invalid time unit
    with pytest.raises(DateTimeError, match="Unsupported time unit"):
        # We need to trick the parser to test this branch
        class FakeUnit:
            def __str__(self):
                return "fake_unit"

        # Directly test the method to cover line 126
        date_methods = DateMethods()
        create_timedelta(1, FakeUnit())


def test_ensure_datetime_type_error():
    """Test TypeError in _ensure_datetime method."""
    from dilemma.dates import DateMethods

    # Create an instance of DateMethods
    date_methods = DateMethods()

    # Test with an object that's not a datetime, string, int, or float
    with pytest.raises(DateTimeError, match="Cannot convert"):
        ensure_datetime({})  # Using a dict should trigger the error


@settings(max_examples=10)
@given(
    days_offset=st.integers(min_value=-1000, max_value=1000),
    hours_offset=st.integers(min_value=-23, max_value=23),
)
def test_date_before_after_property(days_offset, hours_offset):
    """Property test for date before/after comparisons."""
    # Create two dates with the given offset
    base = datetime.now(timezone.utc)
    other = base + timedelta(days=days_offset, hours=hours_offset)

    variables = {"base": base, "other": other}

    # The expressions should match the Python comparison
    assert evaluate("base before other", variables) == (base < other)
    assert evaluate("base after other", variables) == (base > other)


@settings(max_examples=10)
@given(days_ago=st.integers(min_value=1, max_value=500))
def test_date_older_than_within_property(days_ago):
    """Property test for date 'older than' and time periods."""
    now = datetime.now(timezone.utc)
    test_date = now - timedelta(days=days_ago)

    variables = {"test_date": test_date}

    # Test older than
    assert evaluate(f"test_date older than {days_ago - 1} days", variables) is True
    assert evaluate(f"test_date older than {days_ago + 1} days", variables) is False

