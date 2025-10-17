"""
Procuret API
Entity Identifier Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.entity_id_type.type import EntityIdType

class EntityIdentifier(Codable):

    coding_map = {
        'id': CD(str),
        'id_type': CD(EntityIdType)
    }

    def __init__(
        self,
        id: str,
        id_type: EntityIdType
    ) -> None:

        self._id = id
        self._id_type = id_type

        return
    
    identifier: str = property(lambda s: s._id)
    id_type: EntityIdType = property(lambda s: s._entity_id_type)
