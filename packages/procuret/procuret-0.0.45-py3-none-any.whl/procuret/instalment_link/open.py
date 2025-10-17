"""
Procuret Python
Instalment Link Open Module
author: hugh@blinkybeach.com
"""
from procuret.time.time import ProcuretTime
from procuret.data.codable import Codable, CodingDefinition as CD
from typing import TypeVar, Type
from procuret.http.api_request import ApiRequest, HTTPMethod
from procuret.session import Session
from procuret.errors.type_error import ProcuretTypeError

Self = TypeVar('Self', bound='InstalmentLinkOpen')


class InstalmentLinkOpen(Codable):

    path = '/instalment-link/open'

    coding_map = {
        'sequence': CD(int),
        'created': CD(ProcuretTime)
    }

    def __init__(
        self,
        sequence: int,
        created: ProcuretTime
    ) -> None:

        self._sequence = sequence
        self._created = created

        return

    sequence = property(lambda s: s._sequence)
    created = property(lambda s: s._created)

    @classmethod
    def create(
        cls: Type[Self],
        link_id: str,
        session: Session
    ) -> None:

        if not isinstance(link_id, str):
            raise ProcuretTypeError('str', link_id, 'link_id')

        if not isinstance(session, Session):
            raise ProcuretTypeError('Session', session, 'session')

        _ = ApiRequest.make(
            path=cls.path,
            method=HTTPMethod.POST,
            data={'link_id': link_id},
            session=session
        )

        return None
