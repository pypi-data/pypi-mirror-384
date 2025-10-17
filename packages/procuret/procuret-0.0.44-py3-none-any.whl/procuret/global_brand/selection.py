"""
Procuret Python
Global Brand Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.global_brand.brand import GlobalBrand
from procuret.time.time import ProcuretTime


class GlobalBrandSelection(Codable):

    coding_map = {
        'created': CD(ProcuretTime),
        'brand': CD(GlobalBrand)
    }

    def __init__(
        self,
        created: ProcuretTime,
        brand: GlobalBrand
    ) -> None:

        self._created = created
        self._brand = brand

        return

    created = property(lambda s: s._created)
    brand = property(lambda s: s._brand)
