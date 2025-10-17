"""
Procuret Python
Instalment Total Row Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from decimal import Decimal
from procuret.money.currency import Currency


class InstalmentTotalRow(Codable):

    coding_map = {
        'total_payments': CD(Decimal),
        'total_principal': CD(Decimal),
        'total_principal_discount': CD(Decimal),
        'total_interest': CD(Decimal),
        'denomination': CD(Currency)
    }

    def __init__(
        self,
        total_payments: Decimal,
        total_principal: Decimal,
        total_principal_discount: Decimal,
        total_interest: Decimal,
        denomination: Currency
    ) -> None:

        self._total_payments = total_payments
        self._total_principal = total_principal
        self._total_principal_discount = total_principal_discount
        self._total_interest = total_interest
        self._denomination = denomination

        return
    
    total_payments: Decimal = property(lambda s: s._total_payments)
    total_principal: Decimal = property(lambda s: s._decimal)
    total_principal_discount: Decimal = property(
        lambda s: s._total_principal_discount
    )
    total_interest: Decimal = property(lambda s: s._total_interest)
    denomination: Currency = property(lambda s: s._denomination)
