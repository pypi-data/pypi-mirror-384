"""
Procuret Python
Unit of Account Module
author: hugh@blinkybeach.com
"""
from decimal import Decimal


class UnitOfAccount:
    """
    Abstract class defining a protocol for classes that represent units of
    account
    """

    exponent: int = NotImplemented

    def round_to_maximum_precision(self, amount: Decimal) -> Decimal:
        if not isinstance(self.exponent, int):
            raise NotImplementedError('Implement .exponent integer')
        return round(amount, self.exponent)

    def to_integer_smallest_unit(self, amount: Decimal) -> int:
        """
        Return an integer number of the smallest unit of this Unit that
        together comprise the supplied amount. For example, for USD 1,
        return 100.
        """
        return int(amount * (10**self.exponent))

    def from_integer_smallest_unit(self, amount: int) -> Decimal:
        """
        Return a Decimal magnitude value extracted from an integer
        representation of that value in the Unit's smallest possible
        denomination. For example, extract integer values from Stripe.
        """
        value = amount / Decimal(10**self.exponent)
        assert isinstance(value, Decimal)
        return value
