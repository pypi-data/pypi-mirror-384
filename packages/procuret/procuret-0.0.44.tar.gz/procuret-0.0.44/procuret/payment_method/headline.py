"""
Procuret Python
Payment Method Headline Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD


class PaymentMethodHeadline(Codable):

    coding_map = {
        'public_id': CD(str),
        'description': CD(str)
    }

    def __init__(
        self,
        public_id: str,
        description: str
    ) -> None:

        self._public_id = public_id
        self._description = description

        return

    public_id = property(lambda s: s._public_id)
    description = property(lambda s: s._description)
