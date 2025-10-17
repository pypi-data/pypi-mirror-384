"""
Procuret Python
Commitment Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.human.human import Human
from typing import TypeVar, Type, Optional
from procuret.session import Session
from procuret.http.api_request import ApiRequest, HTTPMethod, QueryParameters
from procuret.http.query_parameter import QueryParameter

Self = TypeVar('Self', bound='Commitment')


class Commitment(Codable):

    path = '/commitment'

    coding_map = {
        'public_id': CD(str),
        'committed_human': CD(Human)
    }

    def __init__(
        self,
        public_id: str,
        committed_human: Human
    ) -> None:

        self._public_id = public_id
        self._committed_human = committed_human

        return

    public_id = property(lambda s: s._public_id)
    committed_human = property(lambda s: s._committed_human)

    @classmethod
    def retrieve(
        Self: Type[Self],
        exchange_id: str,
        session: Session
    ) -> Optional[Self]:

        result = ApiRequest.make(
            path=Self.path,
            method=HTTPMethod.GET,
            data=None,
            session=session,
            query_parameters=QueryParameters([QueryParameter(
                key='setup_id',
                value=exchange_id
            )])
        )

        return Self.optionally_decode(result)
