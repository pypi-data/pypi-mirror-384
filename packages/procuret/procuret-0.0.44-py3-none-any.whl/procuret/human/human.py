"""
Procuret Python
Human Module
author: hugh@blinkybeach.com
"""
from enum import Enum
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.money.amount import Amount
from procuret.ancillary.entity_headline import EntityHeadline
from procuret.time.time import ProcuretTime
from procuret.payment_method.headline import PaymentMethodHeadline
from procuret.data.disposition import Disposition
from typing import TypeVar, Type, Optional, List
from procuret.data.order import Order
from procuret.session import Session
from procuret.http.api_request import ApiRequest, HTTPMethod, QueryParameters
from procuret.http.query_parameter import QueryParameter
from procuret.human_identity.identity import HumanIdentity
from procuret.human_identity_document.document import HumanIdentityDocument
from procuret.email_address.address import EmailAddress
from procuret.phone_number.number import PhoneNumber
from procuret.session import Session

Self = TypeVar('Self', bound='Human')


class Human(Codable):

    path = '/human'

    coding_map = {
        'public_id': CD(int),
        'agent_id': CD(int),
        'first_name': CD(str),
        'other_name': CD(str, optional=True),
        'last_name': CD(str),
        'identity': CD(HumanIdentity, optional=True),
        'documents': CD(
            HumanIdentityDocument,
            array=True,
            optional=True
        ),
        'created': CD(ProcuretTime, optional=True),
        'modified': CD(ProcuretTime, optional=True),
        'email_address': CD(EmailAddress),
        'phone_number': CD(PhoneNumber),
        'disposition': CD(Disposition)
    }
    
    def __init__(
        self,
        public_id: int,
        agent_id: int,
        first_name: str,
        other_name: Optional[str],
        last_name: str,
        identity: Optional[HumanIdentity],
        documents: Optional[List[HumanIdentityDocument]],
        created: Optional[ProcuretTime],
        modified: Optional[ProcuretTime],
        email_address: EmailAddress,
        phone_number: PhoneNumber,
        disposition: Disposition
    ) -> None:

        self._public_id = public_id
        self._agent_id = agent_id
        self._first_name = first_name
        self._other_name = other_name
        self._last_name = last_name
        self._identity = identity
        self._documents = documents
        self._created = created
        self._modified = modified
        self._email_address = email_address
        self._phone_number = phone_number
        self._disposition = disposition

        return

    public_id: int = property(lambda s: s._public_id)
    agent_id: int = property(lambda s: s._agent_id)
    first_name: str = property(lambda s: s._first_name)
    other_name: Optional[str] = property(lambda s: s._other_name)
    last_name: str = property(lambda s: s._last_name)
    identity: Optional[HumanIdentity] = property(lambda s: s._identity)
    documents: List[HumanIdentityDocument] = property(
        lambda s: s._documents or []
    )
    created: Optional[ProcuretTime] = property(lambda s: s._created)
    modified: Optional[ProcuretTime] = property(lambda s: s._modified)
    email_address: EmailAddress = property(lambda s: s._email_address)
    phone_number: PhoneNumber = property(lambda s: s._phone_number)
    disposition: Disposition = property(lambda s: s._disposition)

    @classmethod
    def retrieve(
        Self: Type[Self],
        public_id: str,
        session: Session
    ) -> Optional[Self]:

        result = ApiRequest.make(
            path=Self.path,
            method=HTTPMethod.GET,
            data=None,
            session=session,
            query_parameters=QueryParameters([
                QueryParameter('human_id', public_id)
            ])
        )

        return Self.optionally_decode(result)
