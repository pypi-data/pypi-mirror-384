"""
Procuret Python
Human Identity Document
author: hugh@blinkybeach.com
"""
from procuret.human_identity_document.type import HumanIdentityDocumentType
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.time.time import ProcuretTime
from procuret.human.headline import HumanHeadline
from procuret.human_identity_document.state import HumanIdentityDocumentState
from procuret.data.disposition import Disposition


class HumanIdentityDocument(Codable):

    coding_map = {
        'public_id': CD(str),
        'created': CD(ProcuretTime),
        'document_type': CD(HumanIdentityDocumentType),
        'document_identifier': CD(str),
        'human': CD(HumanHeadline),
        'state': CD(HumanIdentityDocumentState),
        'active': CD(bool),
        'disposition': CD(Disposition)
    }

    def __init__(
        self,
        public_id: str,
        created: ProcuretTime,
        document_type: HumanIdentityDocumentType,
        document_identifier: str,
        human: HumanHeadline,
        state: HumanIdentityDocumentState,
        active: bool,
        disposition: Disposition
    ) -> None:

        self._public_id = public_id
        self._created = created
        self._document_type = document_type
        self._document_identifier = document_identifier
        self._human = human
        self._state = state
        self._active = active
        self._disposition = disposition

        return
    
    public_id = property(lambda s: s._public_id)
    created = property(lambda s: s._created)
    document_type = property(lambda s: s._document_type)
    document_identifier = property(lambda s: s._document_identifier)
    human = property(lambda s: s._human)
    state = property(lambda s: s._state)
    active = property(lambda s: s._active)
    disposition = property(lambda s: s._disposition)
