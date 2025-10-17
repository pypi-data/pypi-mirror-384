"""
Procuret Python
Xero Entity Map Module
author: hugh@blinkybeach.com
"""
from procuret.errors.type_error import ProcuretTypeError
from typing import Optional, TypeVar, Type
from procuret.http.query_parameters import QueryParameter, QueryParameters
from procuret.data.codable import CodingDefinition as CD, Codable
from procuret.http.api_request import ApiRequest, HTTPMethod
from procuret.session import Session

Self = TypeVar('Self', bound='XeroEntityMap')


class XeroEntityMap(Codable):

    path = '/xero/entity-map'

    coding_map = {
        'entity_id': CD(int)
    }

    def __init__(
        self,
        entity_id: int
    ) -> None:

        self._entity_id = entity_id

        return

    entity_id = property(lambda s: s._entity_id)

    @classmethod
    def retrieve(
        cls: Type[Self],
        entity_id: int,
        session: Session
    ) -> Optional[Self]:

        if not isinstance(entity_id, int):
            raise ProcuretTypeError('int', entity_id, 'entity_id')

        result = ApiRequest.make(
            path=cls.path,
            method=HTTPMethod.GET,
            data=None,
            session=session,
            query_parameters=QueryParameters(targets=[
                QueryParameter('entity_id', entity_id)
            ])
        )

        return cls.optionally_decode(result)
