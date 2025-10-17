"""
Procuret Python
Procuret Date Module
author: hugh@blinkybeach.com
"""
from datetime import datetime
from typing import TypeVar, Type, Any
from procuret.data.codable import Codable, CodingDefinition as CD

T = TypeVar('T', bound='ProcuretDate')


class ProcuretDate(datetime, Codable):
    _DB_FORMAT_STRING = "%Y-%m-%d"
    _REQUEST_FORMAT_STRING = "%Y-%m-%d"
    _REQUEST_FORMAT_STRING_B = "%Y/%m/%d"
    _REQUEST_FORMAT_STRING_C = "%d/%m/%Y"
    _REQUEST_FORMAT_STRING_D = "%d-%m-%Y"

    @classmethod
    def decode(cls: Type[T], data: Any) -> T:

        assert isinstance(data, str)
        data = data.split('T')[0]
        date = cls.strptime(data, cls._DB_FORMAT_STRING)
        return cls(
            year=date.year,
            month=date.month,
            day=date.day
        )

    def encode(self) -> str:
        return self.strftime(self._REQUEST_FORMAT_STRING)

    @classmethod
    def today(cls: Type[T]) -> T:
        return cls.create_now()

    @classmethod
    def create_now(cls: Type[T]) -> T:
        """Return the current date, at UTC"""
        date = datetime.utcnow()
        return cls(
            year=date.year,
            month=date.month,
            day=date.day
        )

