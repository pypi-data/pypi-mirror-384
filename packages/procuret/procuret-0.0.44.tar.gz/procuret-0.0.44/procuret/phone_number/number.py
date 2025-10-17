"""
Procuret Python
Phone Number Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD


class PhoneNumber(Codable):

    coding_map = {
        'indexid': CD(int),
        'digits': CD(str),
        'confirmed': CD(bool, optional=True),
        'confirmation_required': CD(bool, optional=True),
        'confirmation_request_sent': CD(bool, optional=True)
    }

    def __init__(
        self,
        indexid: int,
        digits: str,
        confirmed: bool,
        confirmation_required: bool,
        confirmation_request_sent: bool
    ) -> None:

        self._indexid = indexid
        self._digits = digits
        self._confirmed = confirmed
        self._confirmation_required = confirmation_required
        self._confirmation_request_sent = confirmation_request_sent

        return

    indexid = property(lambda s: s._indexid)
    digits = property(lambda s: s._digits)
    confirmed = property(lambda s: s._confirmed)
    confirmation_required = property(lambda s: s._confirmation_required)
    confirmation_request_sent = property(
        lambda s: s._confirmation_request_sent
    )
