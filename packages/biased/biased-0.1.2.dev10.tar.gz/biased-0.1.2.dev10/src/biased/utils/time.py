from datetime import UTC, date, datetime, timedelta, tzinfo

from biased.types import CalendarMonth


def build_now(tz: tzinfo = UTC) -> datetime:
    return datetime.now(tz=tz)


def build_today(tz: tzinfo = UTC) -> date:
    return build_now(tz=tz).date()


def build_yesterday(tz: tzinfo = UTC) -> date:
    return build_today(tz=tz) - timedelta(days=1)


def build_current_month(tz: tzinfo = UTC) -> CalendarMonth:
    today = build_today(tz=tz)
    return CalendarMonth(year=today.year, month=today.month, day=1)


def build_now_utc_naive() -> datetime:
    return build_now().replace(tzinfo=None)


def build_now_utc_timestamp() -> float:
    return build_now().timestamp()


def date_to_period_begin(date: date, tz: tzinfo = UTC) -> datetime:
    return datetime.combine(date, datetime.min.time(), tzinfo=tz)


def date_to_period_end(date: date, tz: tzinfo = UTC) -> datetime:
    return datetime.combine(date, datetime.max.time(), tzinfo=tz)


def date_to_id(date: date) -> str:
    return date.strftime("%Y%m%d")


def prev_month_last_day(date: date) -> date:
    date = date.replace(day=1)
    return date - timedelta(days=1)


def today_prev_month_last_day(tz: tzinfo = UTC) -> date:
    today = build_today(tz=tz)
    return prev_month_last_day(date=today)


def date_to_inclusive_period(begin: date, end: date | None = None, tz: tzinfo = UTC) -> tuple[datetime, datetime]:
    if end is None:
        end = begin
    period_begin = date_to_period_begin(begin, tz=tz)
    period_end = date_to_period_end(end, tz=tz)
    return period_begin, period_end


def date_to_exclusive_period(begin: date, end: date | None = None, tz: tzinfo = UTC) -> tuple[datetime, datetime]:
    if end is None:
        end = begin
    period_begin = date_to_period_begin(begin, tz=tz)
    period_end = date_to_period_begin(end + timedelta(days=1), tz=tz)
    return period_begin, period_end
