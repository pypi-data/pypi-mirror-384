import datetime as _dt
import calendar as _cal
from functools import total_ordering as _total_ordering

@_total_ordering
class MonthEndDate:
    __slots__ = ("_date",)

    def __init__(self, year: int, month: int, day: int = 1):
        last_day = _cal.monthrange(year, month)[1]
        self._date = _dt.date(year, month, last_day)

    @classmethod
    def from_date(cls, d: _dt.date):
        return cls(d.year, d.month, d.day)

    def to_date(self) -> _dt.date:
        return self._date

    def __repr__(self):
        return f"MonthEndDate({self._date.isoformat()})"

    # 比較 & ハッシュ（中の date に委譲）
    def _coerce_other(self, other):
        if isinstance(other, MonthEndDate):
            return other._date
        if isinstance(other, _dt.date):
            return other
        return NotImplemented

    def __eq__(self, other):
        other_date = self._coerce_other(other)
        if other_date is NotImplemented:
            return NotImplemented
        return self._date == other_date

    def __lt__(self, other):
        other_date = self._coerce_other(other)
        if other_date is NotImplemented:
            return NotImplemented
        return self._date < other_date

    def __hash__(self):
        return hash(self._date)

@_total_ordering
class WeekendDate:
    __slots__ = ("_date",)

    def __init__(self, year: int, month: int, day: int):
        d = _dt.date(year, month, day)
        # 日曜始まりの週で、その週の土曜を求める
        # weekday(): 月=0 ... 日=6
        # 日曜始まりにしたいので +1 して mod 7
        weekday_sun_start = (d.weekday() + 1) % 7  # 日曜=0, 土曜=6
        offset = 6 - weekday_sun_start
        self._date = d + _dt.timedelta(days=offset)

    @classmethod
    def from_date(cls, d: _dt.date):
        return cls(d.year, d.month, d.day)

    def to_date(self) -> _dt.date:
        return self._date

    def __repr__(self):
        return f"WeekendDate({self._date.isoformat()})"

    def _coerce_other(self, other):
        if isinstance(other, WeekendDate):
            return other._date
        if isinstance(other, _dt.date):
            return other
        return NotImplemented

    def __eq__(self, other):
        other_date = self._coerce_other(other)
        if other_date is NotImplemented:
            return NotImplemented
        return self._date == other_date

    def __lt__(self, other):
        other_date = self._coerce_other(other)
        if other_date is NotImplemented:
            return NotImplemented
        return self._date < other_date

    def __hash__(self):
        return hash(self._date)
