"""
Procuret Python
HumanIdentity Module
author: hugh@blinkybeach.com
"""
from typing import Optional
from procuret.time.time import ProcuretTime
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.address.address import Address


class HumanIdentity(Codable):

    coding_map = {
        'indexid': CD(int),
        'created': CD(ProcuretTime),
        'modified': CD(ProcuretTime),
        'date_of_birth': CD(str, optional=True),
        'address': CD(Address, optional=True)
    }

    def __init__(
        self,
        indexid: int,
        created: ProcuretTime,
        modified: ProcuretTime,
        date_of_birth: Optional[str],
        address: Optional[Address]
    ) -> None:

        self._indexid = indexid
        self._created = created
        self._modified = modified
        self._date_of_birth = date_of_birth
        self._address = address

    indexid = property(lambda s: s._indexid)
    created = property(lambda s: s._created)
    modified = property(lambda s: s._modified)
    date_of_birth = property(lambda s: s._date_of_birth)
    address = property(lambda s: s._address)
