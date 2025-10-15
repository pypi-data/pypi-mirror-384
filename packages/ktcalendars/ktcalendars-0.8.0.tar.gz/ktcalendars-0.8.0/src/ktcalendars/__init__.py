from __future__ import annotations

import datetime
import os
import typing
from calendar import Calendar


__author__ = "Giovanni Bronzini"
__version__ = "0.8.0"
__name__ = "ktcalendars"


try:
    from typing import override
except ImportError:
    override = lambda _func: _func


import holidays
from dateutil.relativedelta import MO, SU, relativedelta


if typing.TYPE_CHECKING:
    from collections.abc import Iterator


def dt(dat: str) -> datetime.date | None:
    """Parse a date string into a datetime.date or None."""
    if not isinstance(dat, str):
        raise ValueError(f"Need a string to parse. Got {type(dat)}")
    if len(dat) not in (8, 10):
        return None
    if "-" in dat:
        return datetime.datetime.strptime(dat, "%Y-%m-%d").date()
    if "/" in dat:
        return datetime.datetime.strptime(dat, "%Y/%m/%d").date()
    return datetime.datetime.strptime(dat, "%Y%m%d").date()


class ExtraHolidayProvider:
    """Default extra holiday provider.

    Extend this class to provide your own way of detecting extra holidays.
    """

    @classmethod
    def is_extra_holiday(cls, ktd: KTDay, country_calendar_code: str) -> bool:
        """Return True if the given KTDay is recorded as extra holiday for the provided country calendar code."""
        return False


class KTDay:
    """Utility class for a day."""

    extra_holiday_provider = ExtraHolidayProvider
    non_working_days = ["Sat", "Sun"]

    def __init__(self, day: KTDay | datetime.date | str | None = None, **kwargs: dict) -> None:
        self.date: datetime.date
        if day is None:
            day = datetime.date.today()
        if isinstance(day, KTDay):
            self.date = day.date
        elif isinstance(day, datetime.date):
            self.date = day
        else:
            parsed_date = dt(day)
            if parsed_date is None:
                raise ValueError(f"Invalid date: {day!r}")
            self.date = parsed_date
        self.__dict__.update(kwargs)

    @property
    def day(self) -> int:
        """Return the day number of the day."""
        return self.date.day

    @property
    def month(self) -> int:
        """Return the month number of the day."""
        return self.date.month

    @property
    def year(self) -> int:
        """Return the year of the day."""
        return self.date.year

    @property
    def day_of_year(self) -> int:
        """Return the day of the year."""
        return self.date.timetuple().tm_yday

    @property
    def week_of_year(self) -> int:
        """Return the calendar week of the year for the day."""
        return self.date.isocalendar()[1]

    def is_extra_holiday(self, country_calendar_code: str) -> bool:
        """Return True if this day is an extra holiday."""
        return self.extra_holiday_provider.is_extra_holiday(self, country_calendar_code)

    def is_holiday(self, country_calendar_code: str | None = None, include_sundays_as_holiday: bool = True) -> bool:
        """Return True if this day is a holiday."""
        if country_calendar_code and self.is_extra_holiday(country_calendar_code):
            return True
        if include_sundays_as_holiday:
            return not get_country_holidays(country_calendar_code=country_calendar_code).is_working_day(self.date)
        return self.date in get_country_holidays(country_calendar_code=country_calendar_code)

    def is_non_working_day(self, country_calendar_code: str | None = None) -> bool:
        """Return true if it is a non working day."""
        return self.day_of_week_short in self.non_working_days or self.is_holiday(
            country_calendar_code=country_calendar_code
        )

    @property
    def day_of_week(self) -> str:
        """Return the day of the week."""
        return self.date.strftime("%A")

    @property
    def day_of_week_short(self) -> str:
        """Return the day of the week in short format."""
        return self.date.strftime("%a")

    @property
    def month_name(self) -> str:
        """Return the name of the month."""
        return self.date.strftime("%B")

    @property
    def month_name_short(self) -> str:
        """Return the name of the month in short format."""
        return self.date.strftime("%b")

    def range_to(self, target: datetime.date | KTDay) -> Iterator[KTDay]:
        """Iterate over all days between this day and the target day."""
        if not isinstance(target, KTDay):
            target = KTDay(target)
        if self.date > target.date:
            raise ValueError("Start date cannot be later than end date.")
        delta_days = (target.date - self.date).days
        for i in range(delta_days + 1):
            yield self + i

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, (KTDay, datetime.date, str)):
            raise NotImplementedError(f"Cannot compare a KTDay with {type(__value)}")
        if not isinstance(__value, KTDay):
            __value = KTDay(__value)
        return self.date == __value.date

    def __hash__(self) -> int:
        return self.date.year * 10000 + self.date.month * 100 + self.date.day

    def __lt__(self, __value: KTDay | datetime.date | str) -> bool:
        if not isinstance(__value, KTDay):
            __value = KTDay(__value)
        return hash(self) < hash(__value)

    def __gt__(self, __value: KTDay | datetime.date | str) -> bool:
        if not isinstance(__value, KTDay):
            __value = KTDay(__value)
        return hash(self) > hash(__value)

    def __le__(self, __value: KTDay | datetime.date | str) -> bool:
        if not isinstance(__value, KTDay):
            __value = KTDay(__value)
        return hash(self) <= hash(__value)

    def __ge__(self, __value: KTDay | datetime.date | str) -> bool:
        if not isinstance(__value, KTDay):
            __value = KTDay(__value)
        return hash(self) >= hash(__value)

    def __sub__(self, other: KTDay | int | datetime.timedelta | relativedelta) -> int | KTDay:
        """Subtract a number of days or a time period from this day."""
        if isinstance(other, KTDay):
            return (self.date - other.date).days
        if isinstance(other, int):
            delta = relativedelta(days=other)
        elif isinstance(other, datetime.timedelta):
            delta = relativedelta(days=other.days)
        elif isinstance(other, relativedelta):
            delta = relativedelta(years=other.years, months=other.months, days=other.days)
        return KTDay(self.date - delta)

    def __add__(self, other: int | datetime.timedelta | relativedelta) -> KTDay:
        """Add a number of days or a time period to this day.

        If `other` is an `int`, it represents a number of days to add.

        If `other` is a `timedelta`, only days are taken into account,
        without any rounding.

        If `other` is a `relativedelta`, only years, months, days and
        weeks are taken into account. Any relative information with
        finer granularity than days and any absolute information is
        ignored.

        :param other: the number of days or period of time to add.
        :return: a new `KrmDay` instance.
        """
        if isinstance(other, int):
            delta = relativedelta(days=other)
        elif isinstance(other, datetime.timedelta):
            delta = relativedelta(days=other.days)
        elif isinstance(other, relativedelta):
            delta = relativedelta(years=other.years, months=other.months, days=other.days)
        return KTDay(self.date + delta)

    def __repr__(self) -> str:
        return self.date.strftime("K%Y-%m-%d")

    def __str__(self) -> str:
        return self.date.strftime("%Y-%m-%d")


class KTCalendar(Calendar):
    """A custom calendar class for KRM that generates KrmDays."""

    @override
    def __init__(self, firstweekday: int = 0, country_code: str | None = None) -> None:
        super().__init__(firstweekday)
        self.country_calendar_code = country_code or KTCalendar.get_default_country_code()

    @staticmethod
    def get_default_country_code() -> str:
        """Return the default country code.

        Override this method to customise.
        """
        return os.environ.get("DEFAULT_HOLIDAYS_CALENDAR", "GB-ENG")

    def itermonthktdays(self, year: int, month: int) -> Iterator[KTDay | None]:
        """Iterate over the days of the month."""
        for x in super().itermonthdays(year, month):
            yield KTDay(datetime.date(year, month, x)) if x else None

    def iter_dates(
        self, from_date: KTDay | datetime.date | str, to_date: KTDay | datetime.date | str
    ) -> Iterator[KTDay]:
        """Iterate over all dates between from_date and to_date."""
        start = KTDay(from_date)
        end = KTDay(to_date)
        if start > end:
            raise ValueError("Start date cannot be after end date.")
        delta_days = (end.date - start.date).days

        for i in range(delta_days + 1):
            yield KTDay(start.date + datetime.timedelta(days=i))

    def get_work_days(
        self, from_date: KTDay | datetime.date | str, to_date: KTDay | datetime.date | str
    ) -> list[KTDay]:
        """Return the iterator for the work days between from_date and to_date."""
        days_between = self.iter_dates(from_date, to_date)

        return [
            day for day in days_between if not day.is_non_working_day(country_calendar_code=self.country_calendar_code)
        ]

    def week_for(self, date: KTDay | datetime.date | str | None = None) -> tuple[KTDay, KTDay]:
        """Return the start and end date of the week for the given date.

        If no date is given, the current date is used.
        """
        date = KTDay(date).date
        return KTDay(date + relativedelta(weekday=MO(-1))), KTDay(date + relativedelta(weekday=SU))

    def iter_week(self, date: datetime.date | str | None = None) -> Iterator[KTDay]:
        """Iterate over all dates in the week for the given date.

        If no date is given, the current date is used.
        """
        return self.iter_dates(*self.week_for(date))


def get_country_holidays(country_calendar_code: str | None = None) -> holidays.HolidayBase:
    """Generate the appropriate country holidays."""
    hol_calendar = country_calendar_code or os.environ.get("DEFAULT_HOLIDAYS_CALENDAR") or "GB-ENG"
    subdiv = None
    if "-" in hol_calendar:
        country, subdiv = hol_calendar.split("-")
    else:
        country = hol_calendar
    cal = holidays.country_holidays(country, subdiv)
    cal.weekend = {6}  # SUN
    return cal
