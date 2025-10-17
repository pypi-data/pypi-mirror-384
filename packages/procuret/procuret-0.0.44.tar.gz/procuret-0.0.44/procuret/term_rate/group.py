"""
Procuret Python
Term Rate Group Module
author: hugh@blinkybeach.com
"""
from procuret.data.order import Order
from procuret.data.codable import Codable, CodingDefinition as CD
from enum import Enum
from typing import Optional, List, TypeVar, Type
from procuret.time.time import ProcuretTime
from procuret.data.disposition import Disposition
from procuret.term_rate.term_rate import TermRate
from procuret.http.api_request import ApiRequest, HTTPMethod
from procuret.http.query_parameters import QueryParameter, QueryParameters
from procuret.errors.type_error import ProcuretTypeError
from procuret.session import Session

Self = TypeVar('Self', bound='TermRateGroup')


class OrderBy(Enum):
    CREATED = 'created'


class TermRateGroup(Codable):

    path = TermRate.path + '/group'
    list_path = path + '/list'

    coding_map = {
        'public_id': CD(str),
        'rates': CD(TermRate, array=True),
        'created': CD(ProcuretTime),
        'active': CD(bool),
        'disposition': CD(Disposition, optional=True)
    }

    def __init__(
        self,
        public_id: str,
        rates: List[TermRate],
        created: ProcuretTime,
        active: bool,
        disposition: Optional[Disposition]
    ) -> None:

        self._public_id = public_id
        self._rates = rates
        self._created = created
        self._active = active
        self._disposition = disposition

        return

    public_id = property(lambda s: s._public_id)
    rates = property(lambda s: s._rates)
    created = property(lambda s: s._created)
    active = property(lambda s: s._active)
    disposition = property(lambda s: s._disposition)

    @classmethod
    def retrieve(
        cls: Type[Self],
        public_id: str,
        session: Session
    ) -> Optional[Self]:

        if not isinstance(public_id, str):
            raise ProcuretTypeError('str', public_id, 'public_id')

        if not isinstance(session, Session):
            raise ProcuretTypeError('Session', session, 'session')

        parameters = [QueryParameter('public_id', public_id)]

        result = ApiRequest.make(
            path=cls.path,
            method=HTTPMethod.GET,
            data=None,
            session=session,
            query_parameters=QueryParameters(parameters)
        )

        return cls.optionally_decode(result)
