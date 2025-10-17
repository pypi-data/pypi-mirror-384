"""
Procuret Python
Entity Headline Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD


class EntityHeadline(Codable):

    coding_map = {
        'legal_entity_name': CD(str),
        'entity_id': CD(int)
    }

    def __init__(
        self,
        legal_entity_name: str,
        entity_id: int
    ) -> None:

        self._legal_entity_name = legal_entity_name
        self._entity_id = entity_id

        return

    legal_entity_name = property(lambda s: s._legal_entity_name)
    entity_id = property(lambda s: s._entity_id)
