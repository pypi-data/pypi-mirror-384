"""
Procuret Python
Currency Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.money.unit_of_account import UnitOfAccount
from typing import TypeVar, Type, Optional, Any
from decimal import Decimal

Self = TypeVar('Self', bound='Currency')


class Currency(Codable, UnitOfAccount):

    coding_map = {
        'indexid': CD(int),
        'name': CD(str),
        'iso_4217': CD(str),
        'exponent': CD(int),
        'symbol': CD(str)
    }

    def __init__(
        self,
        indexid: int,
        name: str,
        iso_4217: str,
        exponent: int,
        symbol: str
    ) -> None:

        self._indexid = indexid
        self._name = name
        self._iso_4217 = iso_4217
        self._exponent = exponent
        self._symbol = symbol

        return

    indexid = property(lambda s: s._indexid)
    exponent = property(lambda s: s._exponent)
    iso_4217 = property(lambda s: s._iso_4217)

    def to_pretty_string(self, amount: Decimal) -> str:
        amount = self.round_to_maximum_precision(amount)
        return '{0:,}'.format(amount)

    def to_symbolised_pretty_string(self, amount: Decimal) -> str:
        return self._symbol + self.to_pretty_string(amount)

    def encode(self) -> int:
        return self._indexid

    @classmethod
    def decode(cls: Type[Self], data: Any) -> Self:
        if isinstance(data, int):
            currency = cls.with_id(data)
            if currency is None:
                raise RuntimeError('Unknown currency ' + str(data))
            return currency
        return super().decode(data)

    @classmethod
    def with_iso4217(cls: Type[Self], iso_4217: str) -> Optional[Self]:
        iso_4217 = iso_4217.upper()
        if iso_4217 in Constants.ENUMERATIONS:
            return Constants.ENUMERATIONS[iso_4217]
        return None

    @classmethod
    def with_id(cls: Type[Self], indexid: int) -> Optional[Self]:
        for key in Constants.ENUMERATIONS:
            if Constants.ENUMERATIONS[key]._indexid == indexid:
                return Constants.ENUMERATIONS[key]
        return None

    @classmethod
    def assertively_with_id(cls: Type[Self], indexid: int) -> Self:
        currency = cls.with_id(indexid)
        if currency is None:
            raise RuntimeError('No currency found w/ id ' + str(indexid))
        return currency

    def __eq__(self, other):
        if other._iso_4217 == self._iso_4217:
            return True
        return False

    def __reduce__(self):
        return (Currency, (
            self._indexid,
            self._name,
            self._iso_4217,
            self._exponent,
            self._symbol
        ))


class Constants:

    AUD = Currency(
        indexid=1,
        name='Australian Dollar',
        iso_4217='AUD',
        exponent=2,
        symbol='$'
    )

    NZD = Currency(
        indexid=2,
        name='New Zealand Dollar',
        iso_4217='NZD',
        exponent=2,
        symbol='$'
    )

    ENUMERATIONS = {
        AUD.iso_4217: AUD,
        NZD.iso_4217: NZD
    }
