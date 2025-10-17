"""
Procuret Python
Country Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD


class Country(Codable):

    coding_map = {
        'country_id': CD(int),
        'name': CD(str),
        'iso_3166_a2': CD(str),
        'iso_3166_a3': CD(str)
    }

    def __init__(
        self,
        country_id: int,
        name: CD(str),
        iso_3166_a2: CD(str),
        iso_3166_a3: CD(str)
    ) -> None:

        self._country_id = country_id
        self._name = name
        self._iso_3166_a2 = iso_3166_a2
        self._iso_3166_a3 = iso_3166_a3

        return

    country_id = property(lambda s: s._country_id)
    name = property(lambda s: s._name)
    iso_3166_a2 = property(lambda s: s._iso_3166_a2)
    iso_3166_a3 = property(lambda s: s._iso_3166_a3)
