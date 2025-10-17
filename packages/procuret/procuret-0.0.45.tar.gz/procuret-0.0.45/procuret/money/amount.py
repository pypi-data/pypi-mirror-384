"""
Procuret Python
Amount Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.money.currency import Currency, Constants as Currencies
from decimal import Decimal
from typing import Type, TypeVar, List, Any

Self = TypeVar('Self', bound='Amount')


class Amount(Codable):

    coding_map = {
        'magnitude': CD(Decimal),
        'denomination': CD(Currency)
    }

    def __init__(
        self,
        magnitude: Decimal,
        denomination: Currency
    ) -> None:

        self._magnitude = magnitude
        self._denomination = denomination

        return

    magnitude = property(lambda s: s._magnitude)
    denomination = property(lambda s: s._denomination)

    string_magnitude = property(str(lambda s: s._magnitude))
    pretty_magnitude = property(
        lambda s: '{:,}'.format(s._magnitude)
    )

    as_integer_smallest_unit= property(
        lambda s: s._denomination.to_integer_smallest_unit(s._magnitude)
    )

    as_pretty_string = property(
        lambda s: s._denomination.to_pretty_string(s._magnitude)
    )

    as_symbolised_pretty_string = property(
        lambda s: s._denomination.to_symbolised_pretty_string(s._magnitude)
    )

    as_denominated_pretty_string = property(
        lambda s: '{d} {a}'.format(
            d=s.denomination.iso_4217.upper(),
            a=s.as_symbolised_pretty_string
        )
    )

    def is_denominated_in(self, currency: Currency) -> bool:
        if self._denomination.indexid == currency.indexid:
            return True
        return False

    @classmethod
    def decode(Self: Type[Self], data: Any) -> Self:

        if isinstance(data['denomination'], int):
            return Self(
                magnitude=Decimal(data['magnitude']),
                denomination=Currency.with_id(data['denomination'])
            )

        return super().decode(data)

    @classmethod
    def denominations_are_homogenous(
        Self: Type[Self],
        amounts: List[Self]
    ) -> bool:
        unique = set(amounts)
        if len(unique) > 1:
            return False
        return True

    def _affirm_comparability(self, other: Self) -> None:
        if not isinstance(other, Amount):
            raise TypeError('comparison candidate must be of type Amount')
        if other.denomination != self._denomination:
            raise ValueError('comparison candiates must share denomination')
        return None

    def __lt__(self, other: Self) -> bool:
        self._affirm_comparability(other)
        return (self._magnitude < other._magnitude)

    def __le__(self, other: Self) -> bool:
        self._affirm_comparability(other)
        return (self._magnitude <= other._magnitude)

    def __eq__(self, other: Self) -> bool:
        self._affirm_comparability(other)
        return self._magnitude == other._magnitude

    def __ne__(self, other: Self) -> bool:
        self._affirm_comparability(other)
        return self._magnitude != other.magnitude

    def __gt__(self, other: Self) -> bool:
        self._affirm_comparability(other)
        return (self._magnitude > other._magnitude)

    def __ge__(self, other: Self) -> bool:
        self._affirm_comparability(other)
        return (self._magnitude >= other._magnitude)

    def __add__(self, other: Self) -> Self:
        self._affirm_comparability(other)
        return Amount(
            magnitude=self._magnitude + other._magnitude,
            denomination=self._denomination
        )

    def __radd__(self, other: Any) -> Self:
        if other != 0:
            raise RuntimeError('Cannot add non-zero un-denominated value to \
Amount')
        return self

    def __sub__(self, other: Self) -> Self:
        self._affirm_comparability(other)
        return Amount(
            magnitude=self._magnitude - other._magnitude,
            denomination=self._denomination
        )

    def __mul__(self, other: Any) -> Self:
        if (isinstance(other, Amount)):
            self._affirm_comparability(other)
            return Amount(
                magnitude=self._magnitude * other._magnitude,
                denomination=self._denomination
            )
        return Amount(
            magnitude=self._magnitude * Decimal(other),
            denomination=self._denomination
        )

    def __rmul__(self, other: Any) -> Self:
        return self.__mul__(other)

    def __truediv__(self, other: Any) -> Self:
        if (isinstance(other, Amount)):
            self._affirm_comparability(other)
            return Amount(
                magnitude=self._magnitude / other._magnitude,
                denomination=self._denomination
            )
        return Amount(
            magnitude=self._magnitude / Decimal(other),
            denomination=self._denomination
        )

    def __repr__(self) -> str:
        return 'Amount: {a}'.format(a=self.as_denominated_pretty_string)

    def __str__(self) -> str:
        return self.as_denominated_pretty_string

    def __round__(self, exponent: int) -> Self:
        return Amount(
            magnitude=round(self.magnitude, exponent),
            denomination=self.denomination
        )

    @staticmethod
    def make_test_amount() -> Self:
        return Amount(Decimal(420), Currencies.AUD)
