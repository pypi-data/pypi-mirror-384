"""
Procuret Python
Address Module
author: hugh@blinkybeach.com
"""
from typing import Optional
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.time.time import ProcuretTime
from procuret.region.region import Region
from procuret.country.country import Country


class Address(Codable):

    coding_map = {
        'created': CD(ProcuretTime),
        'line_1': CD(str),
        'line_2': CD(str, optional=True),
        'line_3': CD(str, optional=True),
        'line_4': CD(str, optional=True),
        'locality': CD(str),
        'region': CD(Region, optional=True),
        'postal_code': CD(str),
        'country': CD(Country, optional=True)
    }

    def __init__(
        self,
        created: ProcuretTime,
        line_1: str,
        line_2: Optional[str],
        line_3: Optional[str],
        line_4: Optional[str],
        locality: str,
        region: Optional[Region],
        postal_code: str,
        country: Optional[Country]
    ) -> None:

        self._created = created
        self._line_1 = line_1
        self._line_2 = line_2
        self._line_3 = line_3
        self._line_4 = line_4
        self._locality = locality
        self._region = region
        self._postal_code = postal_code
        self._country = country

        return

    created = property(lambda s: s._created)
    line_1 = property(lambda s: s._line_1)
    line_2 = property(lambda s: s._line_2)
    line_3 = property(lambda s: s._line_3)
    line_4 = property(lambda s: s._line_4)
    locality = property(lambda s: s._locality)
    region = property(lambda s: s._region)
    postal_code = property(lambda s: s._postal_code)
    country = property(lambda s: s._country)

    one_line = property(lambda s: s._in_one_line())

    def _in_one_line(self) -> str:
        """Return this Address a single line string"""
        line = self._line_1.value
        if self._line_2:
            line += ', ' + self._line_2.value
        if self._line_3:
            line += ', ' + self._line_3.value
        if self._line_4:
            line += ', ' + self._line_4.value
        if self._locality:
            line += ', ' + self._locality
        if self._region:
            line += ' ' + self._region.abbreviation
        line += ' ' + self._postal_code
        return line + ' ' + self._country.iso_3166_a3
