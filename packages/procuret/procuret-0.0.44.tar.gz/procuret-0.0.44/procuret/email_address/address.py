"""
Procuret API
Email Address Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.time.time import ProcuretTime


class EmailAddress(Codable):

    def __init__(
        self,
        created: ProcuretTime,
        email_address: str,
        confirmation_required: bool
    ) -> None:

        self._created = created
        self._email_address = email_address
        self._confirmation_required = confirmation_required

        return
    
    created = property(lambda s: s._created)
    email_address = property(lambda s: s._email_address)
    confirmation_required = property(lambda s: s._confirmation_required)
