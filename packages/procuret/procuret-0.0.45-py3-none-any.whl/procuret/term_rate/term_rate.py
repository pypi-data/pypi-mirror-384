"""
Procuret Python
Term Rate Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from decimal import Decimal


class TermRate(Codable):

    path = '/term-rate'

    coding_map = {
        'supplier_entity_id': CD(int),
        'periods': CD(int),
        'periods_in_year': CD(Decimal)
    }

    def __init__(
        self,
        supplier_entity_id: int,
        periods: int,
        periods_in_year: Decimal
    ) -> None:

        self._supplier_entity_id = supplier_entity_id
        self._periods = periods
        self._periods_in_year = periods_in_year

        return

    periods = property(lambda s: s._periods)
    periods_in_year = property(lambda s: s._periods_in_year)
    supplier_entity_id = property(lambda s: s._supplier_entity_id)
