"""
Procuret API
Procuret Time Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable
from datetime import timedelta
from datetime import datetime
from typing import TypeVar, Type, Any
from procuret.time.tz_utc import UTC

T = TypeVar('T', bound='ProcuretTime')


class ProcuretTime(datetime, Codable):
    _DB_FORMAT_STRING = '%Y-%m-%d %H:%M:%S.%f'

    @classmethod
    def decode(cls: Type[T], data: Any) -> T:

        assert isinstance(data, str)
        if '+' in data:
            parsable = data.split('+')[0]
        else:
            if '-' in data.split(':')[2]:
                parsable = data[:-6]
            else:
                parsable = data
        parsable = parsable.replace('T', ' ')
        parsable = parsable.replace('_', ' ')
        time = cls.strptime(parsable, cls._DB_FORMAT_STRING)
        decoded = cls(
            year=time.year,
            month=time.month,
            day=time.day,
            hour=time.hour,
            minute=time.minute,
            second=time.second,
            microsecond=time.microsecond,
            tzinfo=UTC
        )

        return decoded

    def encode(self) -> str:
        return self.strftime(self._DB_FORMAT_STRING)

    @classmethod
    def utcnow(cls: Type[T]) -> T:
        time = datetime.utcnow()
        return cls._from_datetime(time)

    @classmethod
    def from_unix_timestamp(cls: Type[T], timestamp: int) -> T:
        time = datetime.fromtimestamp(timestamp)
        return cls._from_datetime(time)

    @classmethod
    def in_seconds_from_now(cls: Type[T], seconds: int) -> T:
        time = datetime.utcnow() + timedelta(seconds=seconds)
        return cls._from_datetime(time)

    @classmethod
    def in_minutes_from_now(cls: Type[T], minutes: int) -> T:
        time = datetime.utcnow() + timedelta(minutes=minutes)
        return cls._from_datetime(time)

    @classmethod
    def in_days_from_now(cls: Type[T], days: int) -> T:
        time = datetime.utcnow() + timedelta(days=days)
        return cls._from_datetime(time)

    @classmethod
    def _from_datetime(cls: Type[T], time: datetime) -> T:
        return cls(
            year=time.year,
            month=time.month,
            day=time.day,
            hour=time.hour,
            minute=time.minute,
            second=time.second,
            microsecond=time.microsecond,
            tzinfo=UTC
        )
