"""
Procuret API
Entity Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.data.disposition import Disposition
from typing import List, TypeVar, Type, Optional
from procuret.session import Session
from procuret.entity_identifier.identifier import EntityIdentifier
from procuret.http.api_request import ApiRequest, HTTPMethod, QueryParameters
from procuret.http.query_parameter import QueryParameter
from procuret.address.address import Address

Self = TypeVar('Self', bound='Entity')


class Entity(Codable):

    path = '/entity'

    coding_map = {
        'public_id': CD(int),
        'public_id_short': CD(str),
        'entity_identifiers': CD(EntityIdentifier, array=True),
        'legal_entity_name': CD(str),
        'business_address': CD(Address),
        'disposition': CD(Disposition)
    }

    def __init__(
        self,
        public_id: str,
        public_id_short: str,
        entity_identifiers: List[EntityIdentifier],
        legal_entity_name: str,
        business_address: Address,
        disposition: Disposition
    ) -> None:

        self._public_id = public_id
        self._public_id_short = public_id_short
        self._entity_identifiers = entity_identifiers
        self._legal_entity_name = legal_entity_name
        self._business_address = business_address
        self._disposition = disposition

        return

    public_id: int = property(lambda s: s._public_id)
    public_id_short: str = property(lambda s: s._public_id_short)
    entity_identifiers: List[EntityIdentifier] = property(
        lambda s: s._entity_identifiers
    )
    legal_entity_name: str = property(lambda s: s._legal_entity_name)
    disposition: Disposition = property(lambda s: s._disposition)
    address: Address = property(lambda s: s._business_address)

    @classmethod
    def retrieve(
        Self: Type[Self],
        public_id: int,
        session: Session
    ) -> Optional[Self]:

        result = ApiRequest.make(
            path=Self.path,
            method=HTTPMethod.GET,
            data=None,
            session=session,
            query_parameters=QueryParameters([QueryParameter(
                key='entity_id',
                value=public_id
            )])
        )

        return Self.optionally_decode(result)
