"""
Defines timezone-aware periods
"""

from datetime import date, datetime, time, timedelta, tzinfo
from typing import List, Tuple

import pytz
from pytz.tzinfo import DstTzInfo, StaticTzInfo

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"


class PeriodSchedule:
    """
    Defines a schedule to manage a period of time that is inclusive of start time and exclusive of
    end time as well as being timezone aware.
    """

    period_start_time_of_day: str
    period_end_time_of_day: str
    valid_days_of_week: List[int] = [0, 1, 2, 3, 4, 5, 6]
    tz: tzinfo | DstTzInfo | StaticTzInfo

    start_time: time
    end_time: time

    def __repr__(self) -> str:
        return (
            f"<PeriodSchedule start_time={self.start_time} "
            f"end_time={self.end_time} "
            f"tz={self.tz} "
            f"valid_days_of_week={self.valid_days_of_week} />"
        )

    def __init__(
        self,
        period_start_time_of_day: str,
        period_end_time_of_day: str,
        valid_days_of_week: List[int] | None = None,
        tz: tzinfo | DstTzInfo | StaticTzInfo | str | None = None,
    ) -> None:
        """
        Create a period schedule with a start time of day, end time of day, and days of the week
        that this period schedule is applicable to, inclusive of start time and until, excluding
        end time

        :param period_start_time_of_day String in the form of "HH:MM:SS" in 24-hour time
        :param period_end_time_of_day   String in the form of "HH:MM:SS" in 24-hour time
        :param valid_days_of_week       List of days where Sunday=0 ... Saturday=6. If the list is
                                        empty or None, every day is considered a valid day
        """

        # Ensure that supplied strings are valid
        self.start_time = datetime.strptime(
            period_start_time_of_day, TIME_FORMAT
        ).time()
        self.period_start_time_of_day = period_start_time_of_day

        self.end_time = datetime.strptime(period_end_time_of_day, TIME_FORMAT).time()
        self.period_end_time_of_day = period_end_time_of_day

        if valid_days_of_week is not None and len(valid_days_of_week) > 0:
            if len(valid_days_of_week) > 7:
                raise ValueError(
                    "Cannot have more than 7 valid days of the week and "
                    f"{len(valid_days_of_week)} valid days provided. They are: "
                    f"{valid_days_of_week}"
                )

            for vd in valid_days_of_week:
                if vd < 0 or vd > 6:
                    raise ValueError(
                        f"Invalid cardinality of Day of Week provided: {vd}. Must "
                        "be between 0 (Sunday) through to 6 (Saturday)."
                    )

            self.valid_days_of_week = valid_days_of_week

        if tz is None:
            self.tz = pytz.timezone("UTC")
        elif isinstance(tz, str):
            self.tz = pytz.timezone(tz)
        elif (
            isinstance(tz, tzinfo)
            or isinstance(tz, StaticTzInfo)
            or isinstance(tz, DstTzInfo)
        ):
            self.tz = tz
        else:
            raise ValueError(f"Invalid timezone of type '{type(tz)}' supplied: {tz}")

    def is_in_period(self, check_datetime: datetime) -> bool:
        """
        Checks if the supplied datetime is in the configured period
        """

        localized_dt = self.localize_check_datetime(check_datetime)
        check_date, _ = self.extract_date_time_from_check_datetime(localized_dt)
        if int(check_date.strftime("%w")) not in self.valid_days_of_week:
            return False

        (
            start_datetime,
            end_datetime,
        ) = self.get_start_end_datetimes_for_datetime(check_datetime)

        if start_datetime <= localized_dt and end_datetime > localized_dt:
            return True

        return False

    def localize_check_datetime(self, check_datetime: datetime) -> datetime:
        """
        Checks if the supplied datetime is non-naive (i.e. has a timezone defined) and
        returns a timezone-aware datetime.

        :Note: If the supplied datetime is naive (no timezone), it is localized into the timezone
        configured in this period schedule.
        """

        if check_datetime is None:
            raise ValueError("Cannot localize datetime timezone on None value")

        if check_datetime.tzinfo is None:
            if not hasattr(self.tz, "localize"):
                raise RuntimeError(
                    f"Supplied timezone type ({type(self.tz)}) does not have a localize() method. "
                    f"Unable to localize datetime {check_datetime}. Pick a different timezone for "
                    "this period schedule."
                )

            return self.tz.localize(check_datetime)  # type: ignore
        else:
            return check_datetime.astimezone(self.tz)

    def extract_date_time_from_check_datetime(
        self, check_datetime: datetime
    ) -> Tuple[date, time]:
        """
        Extracts the date and time from a datetime object, localizing for a timezone if necessary
        """

        if check_datetime.tzinfo is None:
            raise ValueError(
                "Extracting date and time must only be done from a timezone configured datetime "
                "variable. Use localize_check_datetime() to ensure that a valid timezone is "
                f"applied to {check_datetime}"
            )

        return (check_datetime.date(), check_datetime.time())

    def get_start_end_datetimes_for_datetime(
        self, check_datetime: datetime
    ) -> Tuple[datetime, datetime]:
        """
        Gets the start and end datetimes for a point in time and returns a tuple of
        (start_datetime, end_datetime)
        """

        check_date, check_time = self.extract_date_time_from_check_datetime(
            self.localize_check_datetime(check_datetime)
        )

        if self.end_time < self.start_time and check_time < self.end_time:
            check_start_datetime = self.tz.localize(  # type: ignore
                datetime.combine(check_date - timedelta(days=1), self.end_time)
            )
            check_end_datetime = self.tz.localize(  # type: ignore
                datetime.combine(check_date, self.end_time)
            )

        elif self.end_time < self.start_time and check_time > self.end_time:
            check_start_datetime = self.tz.localize(  # type: ignore
                datetime.combine(check_date, self.start_time)
            )
            check_end_datetime = self.tz.localize(  # type: ignore
                datetime.combine(check_date + timedelta(days=1), self.end_time)
            )
        else:
            check_start_datetime = self.tz.localize(  # type: ignore
                datetime.combine(check_date, self.start_time)
            )
            check_end_datetime = self.tz.localize(  # type: ignore
                datetime.combine(check_date, self.end_time)
            )

        return (check_start_datetime, check_end_datetime)

    def get_last_start_datetime(self, check_datetime: datetime) -> datetime | None:
        """
        Gets the datetime of the previous start period if there are valid days
        """

        check_date, check_time = self.extract_date_time_from_check_datetime(
            self.localize_check_datetime(check_datetime)
        )

        # Valid days of the week relate to the start period, not the end period
        has_found_valid_day_of_week = False

        last_valid_date = None
        timedelta_offset = 0
        while not has_found_valid_day_of_week:
            check_last_valid_date = check_date - timedelta(days=timedelta_offset)
            check_date_day_of_week = int(check_last_valid_date.strftime("%w"))

            if check_date_day_of_week in self.valid_days_of_week and not (
                timedelta_offset == 0 and check_time < self.start_time
            ):
                (start_date, _) = self.get_start_end_datetimes_for_datetime(
                    datetime.combine(
                        check_last_valid_date, self.start_time, tzinfo=self.tz
                    )
                )
                last_valid_date = start_date
                has_found_valid_day_of_week = True
            else:
                # Check another day
                timedelta_offset += 1

        return last_valid_date

    def duration_since_last_start_datetime(self, check_datetime: datetime) -> timedelta:
        """
        Gets the timedelta duration between the supplied check_datetime and the last start time
        """

        last_start_dt = self.get_last_start_datetime(
            self.localize_check_datetime(check_datetime)
        )

        if last_start_dt is None:
            raise ValueError(
                "Cannot get duration since last start datetime as it is null"
            )

        return self.localize_check_datetime(check_datetime) - last_start_dt

    def get_last_end_datetime(self, check_datetime: datetime) -> datetime:
        """
        Gets the number of seconds since the last end time
        """

        check_date, check_time = self.extract_date_time_from_check_datetime(
            self.localize_check_datetime(check_datetime)
        )

        # Valid days of the week relate to the start period, not the end period
        has_found_valid_day_of_week = False

        last_valid_date = None
        timedelta_offset = 0
        while not has_found_valid_day_of_week:
            check_last_valid_date = check_date - timedelta(days=timedelta_offset)
            check_date_day_of_week = int(check_last_valid_date.strftime("%w"))

            if check_date_day_of_week in self.valid_days_of_week and not (
                timedelta_offset == 0 and check_time < self.start_time
            ):
                (_, end_date) = self.get_start_end_datetimes_for_datetime(
                    datetime.combine(
                        check_last_valid_date, self.start_time, tzinfo=self.tz
                    )
                )
                last_valid_date = end_date
                has_found_valid_day_of_week = True
            else:
                # Check another day
                timedelta_offset += 1

        if last_valid_date is None:
            raise ValueError("No valid last end datetimes found")

        return last_valid_date

    def duration_since_last_end_datetime(self, check_datetime: datetime) -> timedelta:
        """
        Gets the timedelta duration between the supplied check_datetime and the last end time
        """

        return self.localize_check_datetime(
            check_datetime
        ) - self.get_last_end_datetime(self.localize_check_datetime(check_datetime))

    def get_next_start_datetime(self, check_datetime: datetime) -> datetime | None:
        """
        Gets the datetime of the next start period if there are valid days
        """

        check_date, check_time = self.extract_date_time_from_check_datetime(
            self.localize_check_datetime(check_datetime)
        )

        # Valid days of the week relate to the start period, not the end period
        has_found_valid_day_of_week = False

        next_valid_date = None
        timedelta_offset = 0
        while not has_found_valid_day_of_week:
            check_last_valid_date = check_date + timedelta(days=timedelta_offset)
            check_date_day_of_week = int(check_last_valid_date.strftime("%w"))

            if check_date_day_of_week in self.valid_days_of_week and not (
                timedelta_offset == 0 and check_time > self.start_time
            ):
                (start_date, _) = self.get_start_end_datetimes_for_datetime(
                    datetime.combine(
                        check_last_valid_date, self.start_time, tzinfo=self.tz
                    )
                )
                next_valid_date = start_date
                has_found_valid_day_of_week = True
            else:
                # Check another day
                timedelta_offset += 1

        return next_valid_date

    def duration_until_next_start_datetime(self, check_datetime: datetime) -> timedelta:
        """
        Gets the timedelta duration between the supplied check_datetime and the next start time
        """

        next_start_datetime = self.get_next_start_datetime(
            self.localize_check_datetime(check_datetime)
        )

        if next_start_datetime is None:
            raise ValueError(
                "Cannot get duration until next start datetime as it is null"
            )

        return next_start_datetime - self.localize_check_datetime(check_datetime)

    def get_next_end_datetime(self, check_datetime: datetime) -> datetime | None:
        """
        Gets the datetime of the next end period if there are valid days
        """

        check_date, check_time = self.extract_date_time_from_check_datetime(
            self.localize_check_datetime(check_datetime)
        )

        # Valid days of the week relate to the start period, not the end period
        has_found_valid_day_of_week = False

        next_valid_date = None
        timedelta_offset = 0
        while not has_found_valid_day_of_week:
            check_last_valid_date = check_date + timedelta(days=timedelta_offset)
            check_date_day_of_week = int(check_last_valid_date.strftime("%w"))

            if check_date_day_of_week in self.valid_days_of_week and not (
                timedelta_offset == 0 and check_time > self.start_time
            ):
                (_, end_date) = self.get_start_end_datetimes_for_datetime(
                    datetime.combine(
                        check_last_valid_date, self.start_time, tzinfo=self.tz
                    )
                )
                next_valid_date = end_date
                has_found_valid_day_of_week = True
            else:
                # Check another day
                timedelta_offset += 1

        return next_valid_date

    def duration_until_next_end_datetime(self, check_datetime: datetime) -> timedelta:
        """
        Gets the timedelta duration between the supplied check_datetime and the next end time
        """

        next_end_datetime = self.get_next_end_datetime(
            self.localize_check_datetime(check_datetime)
        )

        if next_end_datetime is None:
            raise ValueError(
                "Cannot get duration until next end datetime as it is null"
            )

        return next_end_datetime - self.localize_check_datetime(check_datetime)

    def get_current_start_datetime(self, check_datetime: datetime) -> datetime | None:
        """
        Gets the datetime of the current end period if there it is a valid day
        """

        check_date, _ = self.extract_date_time_from_check_datetime(
            self.localize_check_datetime(check_datetime)
        )

        # Valid days of the week relate to the start period, not the end period
        has_found_valid_day_of_week = False

        next_valid_date = None
        timedelta_offset = 0

        while not has_found_valid_day_of_week:
            check_last_valid_date = check_date + timedelta(days=timedelta_offset)
            check_date_day_of_week = int(check_last_valid_date.strftime("%w"))

            if check_date_day_of_week in self.valid_days_of_week:
                (start_date, _) = self.get_start_end_datetimes_for_datetime(
                    datetime.combine(
                        check_last_valid_date, self.start_time, tzinfo=self.tz
                    )
                )
                next_valid_date = start_date
                has_found_valid_day_of_week = True
            else:
                # Check another day
                timedelta_offset += 1

        return next_valid_date

    def duration_until_current_start_datetime(
        self, check_datetime: datetime
    ) -> timedelta:
        """
        Gets the timedelta duration between the supplied check_datetime and the next end time
        """

        current_start_datetime = self.get_current_start_datetime(
            self.localize_check_datetime(check_datetime)
        )

        if current_start_datetime is None:
            raise ValueError(
                "Cannot get duration until current start datetime as it is null"
            )

        return current_start_datetime - self.localize_check_datetime(check_datetime)

    def get_current_end_datetime(self, check_datetime: datetime) -> datetime | None:
        """
        Gets the datetime of the current end period if there it is a valid day
        """

        check_date, _ = self.extract_date_time_from_check_datetime(
            self.localize_check_datetime(check_datetime)
        )

        # Valid days of the week relate to the start period, not the end period
        has_found_valid_day_of_week = False

        next_valid_date = None
        timedelta_offset = 0

        while not has_found_valid_day_of_week:
            check_last_valid_date = check_date + timedelta(days=timedelta_offset)
            check_date_day_of_week = int(check_last_valid_date.strftime("%w"))

            if check_date_day_of_week in self.valid_days_of_week:
                (_, end_date) = self.get_start_end_datetimes_for_datetime(
                    datetime.combine(
                        check_last_valid_date, self.start_time, tzinfo=self.tz
                    )
                )
                next_valid_date = end_date
                has_found_valid_day_of_week = True
            else:
                # Check another day
                timedelta_offset += 1

        return next_valid_date

    def duration_until_current_end_datetime(
        self, check_datetime: datetime
    ) -> timedelta:
        """
        Gets the timedelta duration between the supplied check_datetime and the next end time
        """

        current_end_datetime = self.get_current_end_datetime(
            self.localize_check_datetime(check_datetime)
        )

        if current_end_datetime is None:
            raise ValueError(
                "Cannot get duration until current end datetime as it is null"
            )

        return current_end_datetime - self.localize_check_datetime(check_datetime)
