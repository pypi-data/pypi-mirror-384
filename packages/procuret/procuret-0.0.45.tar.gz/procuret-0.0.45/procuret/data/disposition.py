"""
Procuret Python
Disposition Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable
from typing import TypeVar, Type, Any, Dict

T = TypeVar('T', bound='Disposition')


class Disposition(Codable):

    def __init__(
        self,
        sequence: int,
        count: int,
        limit: int,
        offset: int
    ) -> None:

        self._sequence = sequence
        self._count = count
        self._limit = limit
        self._offset = offset

        return

    sequence = property(lambda s: s._sequence)
    count = property(lambda s: s._count)
    limit = property(lambda s: s._limit)
    offset = property(lambda s: s._offset)

    def encode(self) -> Dict[str, int]:
        return {
            'sequence': self._sequence,
            'count': self._count,
            'limit': self._limit,
            'offset': self._offset
        }

    @classmethod
    def decode(cls: Type[T], data: Any) -> T:
        return cls(
            sequence=data['sequence'],
            count=data['count'],
            limit=data['limit'],
            offset=data['offset']
        )
