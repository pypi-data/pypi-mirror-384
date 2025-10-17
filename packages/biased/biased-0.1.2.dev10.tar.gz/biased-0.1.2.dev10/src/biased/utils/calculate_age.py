from datetime import UTC, date, tzinfo

from dateutil.relativedelta import relativedelta

from biased.utils.time import build_today


def calculate_age(date_of_birth: date, today: date | None = None, tz: tzinfo = UTC) -> relativedelta:
    if today is None:
        today = build_today(tz=tz)
    return relativedelta(today, date_of_birth)
