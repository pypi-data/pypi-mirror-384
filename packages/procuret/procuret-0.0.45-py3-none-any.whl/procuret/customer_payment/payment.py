"""
Procuret Python
Customer Payment Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD 
from procuret.time.time import ProcuretTime
from decimal import Decimal
from procuret.human.headline import HumanHeadline
from procuret.data.disposition import Disposition
from procuret.payment_method.headline import PaymentMethodHeadline
from procuret.money.currency import Currency
from typing import Optional


class CustomerPayment(Codable):

    coding_map = {
        'public_id': CD(str),
        'executor': CD(HumanHeadline),
        'created': CD(ProcuretTime),
        'executed': CD(ProcuretTime),
        'magnitude': CD(Decimal),
        'disposition': CD(Disposition),
        'active': CD(bool),
        'payment_method': CD(PaymentMethodHeadline, optional=True),
        'commitment_id': CD(str),
        'denomination': CD(Currency)
    }

    def __init__(
        self,
        public_id: str,
        executor: HumanHeadline,
        created: ProcuretTime,
        executed: ProcuretTime,
        magnitude: Decimal,
        disposition: Disposition,
        active: bool,
        payment_method: Optional[PaymentMethodHeadline],
        commitment_id: str,
        denomination: Currency
    ) -> None:

        self._public_id = public_id
        self._executor = executor
        self._created = created
        self._executed = executed
        self._disposition = disposition
        self._magnitude = magnitude
        self._active = active
        self._payment_method = payment_method
        self._commitment_id = commitment_id
        self._denomination = denomination

        return

    public_id: str = property(lambda s: s._public_id)
    executor: HumanHeadline = property(lambda s: s._executor)
    created: ProcuretTime = property(lambda s: s._created)
    executed: ProcuretTime = property(lambda s: s._executed)
    magnitude: Decimal = property(lambda s: s._magnitude)
    disposition: Disposition = property(lambda s: s._disposition)
    active: bool = property(lambda s: s._active)
    payment_method: Optional[PaymentMethodHeadline] = property(
        lambda s: s._payment_method
    )
    commitment_id: str = property(lambda s: s._commitment_id)
    denomination: Currency = property(lambda s: s._denomination)
