"""
Procuret Python
Region Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD


class Region(Codable):

    coding_map = {
        'indexid': CD(int),
        'name': CD(str),
        'abbreviation': CD(str),
        'country_id': CD(int)
    }

    def __init__(
        self,
        indexid: int,
        name: str,
        abbreviation: str,
        country_id: int
    ) -> None:

        self._indexid = indexid
        self._name = name
        self._abbreviation = abbreviation
        self._country_id = country_id

        return

    indexid = property(lambda s: s._indexid)
    name = property(lambda s: s._name)
    abbreviation = property(lambda s: s._abbreviation)
    country_id = property(lambda s: s._country_id)
