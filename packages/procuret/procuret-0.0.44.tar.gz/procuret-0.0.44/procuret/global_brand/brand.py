"""
Procuret Python
Global Brand Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD


class GlobalBrand(Codable):

    coding_map = {
        'indexid': CD(int),
        'name': CD(str),
        'logo_url_light': CD(str),
        'logo_url_dark': CD(str)
    }

    def __init__(
        self,
        indexid: int,
        name: str,
        logo_url_light: str,
        logo_url_dark: str
    ) -> None:

        self._indexid = indexid
        self._name = name
        self._logo_url_light = logo_url_light
        self._logo_url_dark = logo_url_dark

        return

    indexid = property(lambda s: s._indexid)
    name = property(lambda s: s._name)
    logo_url_light = property(lambda s: s._logo_url_light)
    logo_url_dark = property(lambda s: s._logo_url_dark)
