import json
from datetime import datetime, timezone

from .utils import (
    temporal_unit_comparison,
    ensure_datetime,
    create_timedelta,
    unpack_datetimes,
)
from .logconf import get_logger

log = get_logger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        return {"__datetime__": obj.isoformat()}


class DateMethods:
    """
    Mixin class for add datetime handling methods to ExpressionTransformer
    """

    def date_is_past(self, items: list) -> bool:
        """Handle 'is past' date comparison"""
        date_obj = ensure_datetime(items[0])
        now = datetime.now(date_obj.tzinfo if date_obj.tzinfo else timezone.utc)
        return date_obj < now

    def date_is_future(self, items: list) -> bool:
        """Handle 'is future' date comparison"""
        date_obj = ensure_datetime(items[0])
        now = datetime.now(date_obj.tzinfo if date_obj.tzinfo else timezone.utc)
        return date_obj > now

    def date_is_today(self, items: list) -> bool:
        """Handle 'is today' date comparison"""
        date_obj = ensure_datetime(items[0])
        now = datetime.now(date_obj.tzinfo if date_obj.tzinfo else timezone.utc)
        return date_obj.date() == now.date()

    def now_value(self, _) -> datetime:
        """Return the current datetime for use in comparisons"""
        return datetime.now(tz=timezone.utc)

    @temporal_unit_comparison
    def date_older_than(self, date_obj: datetime, quantity: float, unit: str) -> bool:
        """
        Check if date is older than a specified time period from now.
        """
        now = datetime.now(date_obj.tzinfo if date_obj.tzinfo else timezone.utc)
        delta = create_timedelta(quantity, unit)

        return (now - date_obj) > delta

    @temporal_unit_comparison
    def date_upcoming_within(
        self, date_obj: datetime, quantity: float, unit: str
    ) -> bool:
        """
        Check if a date is within a specified time period in the future from now.
        """
        now = datetime.now(date_obj.tzinfo if date_obj.tzinfo else timezone.utc)
        delta = create_timedelta(quantity, unit)

        return now <= date_obj <= (now + delta)

    def date_before(self, items: list) -> bool:
        """Check if one date is before another"""
        date1, date2 = unpack_datetimes(items)
        return date1 < date2

    def date_after(self, items: list) -> bool:
        """Check if one date is after another"""
        date1, date2 = unpack_datetimes(items)
        return date1 > date2

    def date_same_day(self, items: list) -> bool:
        """Check if two dates are on the same calendar day"""
        date1, date2 = unpack_datetimes(items)
        return date1.date() == date2.date()

    # Unit methods
    def minute_unit(self, _) -> str:
        return "minute"

    def hour_unit(self, _) -> str:
        return "hour"

    def day_unit(self, _) -> str:
        return "day"

    def week_unit(self, _) -> str:
        return "week"

    def month_unit(self, _) -> str:
        return "month"

    def year_unit(self, _) -> str:
        return "year"
