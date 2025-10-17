"""
Procuret Python
Xero Organisation Module
author: hugh@blinkybeach.com
"""
from procuret.errors.type_error import ProcuretTypeError
from typing import Optional, TypeVar, Type
from procuret.http.query_parameters import QueryParameter, QueryParameters
from procuret.data.codable import CodingDefinition as CD, Codable
from procuret.http.api_request import ApiRequest, HTTPMethod
from procuret.session import Session

Self = TypeVar('Self', bound='XeroOrganisation')


class XeroOrganisation(Codable):

    path = '/xero/organisation'

    coding_map = {
        'short_code': CD(str),
        'entity_id': CD(int)
    }

    def __init__(
        self,
        short_code: str,
        entity_id: int
    ) -> None:

        self._short_code = short_code
        self._entity_id = entity_id

        return

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
