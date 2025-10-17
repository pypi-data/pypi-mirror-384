"""
Procuret Python
Instalment Line Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.time.date import ProcuretDate
from decimal import Decimal
from typing import Optional
from procuret.money.currency import Currency
from procuret.customer_payment.payment import CustomerPayment


class InstalmentLine(Codable):

    coding_map = {
        'sequence': CD(int),
        'date': CD(ProcuretDate),
        'nominal_payment': CD(Decimal),
        'opening_balance': CD(Decimal),
        'interest_paid': CD(Decimal),
        'principal_paid': CD(Decimal),
        'principal_discount': CD(Decimal),
        'closing_balance': CD(Decimal),
        'commitment_public_id': CD(str),
        'payment': CD(CustomerPayment, optional=True),
        'denomination': CD(Currency)
    }

    def __init__(
        self,
        sequence: int,
        date: ProcuretDate,
        nominal_payment: Decimal,
        opening_balance: Decimal,
        interest_paid: Decimal,
        principal_paid: Decimal,
        principal_discount: Decimal,
        closing_balance: Decimal,
        commitment_public_id: str,
        payment: Optional[CustomerPayment],
        denomination: Currency
    ) -> None:

        self._sequence = sequence
        self._date = date
        self._nominal_payment = nominal_payment
        self._opening_balance = opening_balance
        self._interest_paid = interest_paid
        self._principal_paid = principal_paid
        self._princiapl_discount = principal_discount
        self._closing_balance = closing_balance
        self._commitment_public_id = commitment_public_id
        self._payment = payment
        self._denomination = denomination

        return

    sequence: int = property(lambda s: s._sequence)
    date: ProcuretDate = property(lambda s: s._date)
    nominal_payment: Decimal = property(lambda s: s._nominal_payment)
    opening_balance: Decimal = property(lambda s: s._opening_balance)
    interest_paid: Decimal = property(lambda s: s._interest_paid)
    principal_paid: Decimal = property(lambda s: s._principal_paid)
    principal_discount: Decimal = property(lambda s: s._principal_discount)
    closing_balance: Decimal = property(lambda s: s._closing_balance)
    commitment_public_id: Decimal = property(lambda s: s._commitment_public_id)
    payment: Optional[CustomerPayment] = property(lambda s: s._payment)
    denomination: Currency = property(lambda s: s._denomination)
