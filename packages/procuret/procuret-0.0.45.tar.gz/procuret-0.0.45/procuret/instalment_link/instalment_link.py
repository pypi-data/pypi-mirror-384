"""
Procuret Python
Instalment Link Module
author: hugh@blinkybeach.com
"""
from xmlrpc.client import Boolean
from procuret.ancillary.communication_option import CommunicationOption
from typing import TypeVar, Type, Union, List
from procuret.data.codable import Codable, CodingDefinition as CD
from procuret.ancillary.entity_headline import EntityHeadline
from procuret.errors.type_error import ProcuretTypeError
from procuret.http.api_request import ApiRequest, HTTPMethod
from procuret.errors.inconsistent import InconsistentState
from procuret.session import Session
from decimal import Decimal
from enum import Enum
from procuret.data.order import Order
from procuret.http.query_parameters import QueryParameter, QueryParameters
from typing import Optional
from procuret.instalment_link.open import InstalmentLinkOpen
from procuret.time.time import ProcuretTime
from procuret.ancillary.sale_nomenclature import SaleNomenclature
from procuret.money.currency import Currency
from procuret.money.amount import Amount


Self = TypeVar('Self', bound='InstalmentLink')


class OrderBy(Enum):
    CREATED = 'created'


class InstalmentLink(Codable):

    path = '/instalment-link'
    list_path = path + '/list'

    _LINK_TEMPLATE = 'https://procuret.com/b?il={public_id}'

    coding_map = {
        'public_id': CD(str),
        'created': CD(ProcuretTime),
        'supplier': CD(EntityHeadline),
        'invoice_amount': CD(Decimal),
        'invitee_email': CD(str, optional=True),
        'invitee_phone_digits': CD(str, optional=True),
        'invitee_human_id': CD(int, optional=True),
        'invoice_identifier': CD(str),
        'opens': CD(InstalmentLinkOpen, array=True),
        'sale_name': CD(SaleNomenclature),
        'allow_edit': CD(bool),
        'denomination_id': CD(int)
    }

    def __init__(
        self,
        public_id: str,
        created: ProcuretTime,
        supplier: EntityHeadline,
        invitee_email: Optional[str],
        invitee_phone_digits: Optional[str],
        invitee_human_id: Optional[int],
        invoice_amount: Decimal,
        invoice_identifier: str,
        opens: List[InstalmentLinkOpen],
        sale_name: SaleNomenclature,
        allow_edit: bool,
        denomination_id: int
    ) -> None:

        self._supplier = supplier
        self._created = created
        self._public_id = public_id
        self._invitee_email = invitee_email
        self._invitee_phone_digits = invitee_phone_digits
        self._invitee_human_id = invitee_human_id
        self._invoice_amount = invoice_amount
        self._invoice_identifier = invoice_identifier
        self._opens = opens
        self._sale_name = sale_name
        self._allow_edit = allow_edit
        self._denomination_id = denomination_id

        return

    public_id = property(lambda s: s._public_id)
    created = property(lambda s: s._created)
    supplier = property(lambda s: s._supplier)
    invitee_email = property(lambda s: s._invitee_email)
    invitee_phone_digits = property(lambda s: s._invitee_phone_digits)
    invitee_human_id = property(lambda s: s._invitee_human_id)
    invoice_amount = property(lambda s: s._invoice_amount)
    invoice_identifier = property(lambda s: s._invoice_identifier)
    opens = property(lambda s: s._opens)
    sale_name = property(lambda s: s._sale_name)
    allow_edit = property(lambda s: s._allow_edit)
    denomination_id = property(lambda s: s._denomination_id)

    currency = property(lambda s: Currency.assertively_with_id(
        indexid=s._denomination_id
    ))

    invoice_amount_pretty = property(lambda s: '{:,}'.format(s.invoice_amount))
    has_been_opened = property(lambda s: len(s._opens) > 0)
    open_count = property(lambda s: len(s._opens))

    url = property(lambda s: s._LINK_TEMPLATE.format(public_id=s._public_id))

    amount: Amount = property(lambda s: Amount(
        magnitude=s._invoice_amount,
        denomination=Currency.assertively_with_id(s._denomination_id)
    ))

    @classmethod
    def create(
        cls: Type[Self],
        supplier: Union[int, EntityHeadline],
        invoice_amount: Decimal,
        invitee_email: str,
        invoice_identifier: str,
        communication: CommunicationOption,
        session: Session
    ) -> Self:

        def infer_supplier_id(x: Union[int, EntityHeadline]) -> int:
            if isinstance(x, int):
                return x
            if isinstance(x, EntityHeadline):
                return x.entity_id
            raise ProcuretTypeError(('int', 'EntityHeadline'), x, 'supplier')

        def infer_communication(y: CommunicationOption) -> bool:
            if not isinstance(communication, CommunicationOption):
                raise ProcuretTypeError(
                    'CommunicationOption',
                    y,
                    'communcation'
                )
            if communication == CommunicationOption.DO_NOT_CONTACT_CUSTOMER:
                return False
            if communication == CommunicationOption.EMAIL_CUSTOMER:
                return True
            raise NotImplementedError

        if not isinstance(invoice_amount, Decimal):
            raise ProcuretTypeError(
                'Decimal',
                invoice_amount,
                'invoice_amount'
            )

        if not isinstance(invitee_email, str):
            raise ProcuretTypeError('str', invitee_email, 'invitee_email')

        if not isinstance(invoice_identifier, str):
            raise ProcuretTypeError(
                'str',
                invoice_identifier,
                'invoice_identifier'
            )

        data = {
            'supplier_id': infer_supplier_id(supplier),
            'invoice_amount': str(invoice_amount),
            'invitee_email': invitee_email,
            'invoice_identifier': invoice_identifier,
            'communicate': infer_communication(communication)
        }

        result = ApiRequest.make(
            path=cls.path,
            method=HTTPMethod.POST,
            data=data,
            session=session,
            query_parameters=None
        )

        if result is None:
            raise InconsistentState

        return cls.decode(result)

    @classmethod
    def retrieve(
        cls: Type[Self],
        public_id: str,
        session: Session
    ) -> Optional[Self]:

        if not isinstance(public_id, str):
            raise TypeError('public_id must be a string')

        result = cls.retrieve_many(
            public_id=public_id,
            session=session
        )

        if len(result) < 1:
            return None

        return result[0]

    @classmethod
    def retrieve_many(
        cls: Type[Self],
        session: Session,
        public_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        order: Order = Order.ASCENDING,
        order_by: OrderBy = OrderBy.CREATED,
        opened: Optional[bool] = None
    ) -> List[Self]:

        if not isinstance(limit, int):
            raise TypeError('limit must be an integer')

        if not isinstance(offset, int):
            raise TypeError('offset must be an integer')

        if not isinstance(order, Order):
            raise TypeError('order must be of type Order')

        if not isinstance(order_by, OrderBy):
            raise TypeError('order must be of type InstalmentLink.OrderBy')

        if not isinstance(session, Session):
            raise TypeError('session must be of type Session')

        parameters = [
            QueryParameter('limit', limit),
            QueryParameter('offset', offset),
            QueryParameter('order', order.value),
            QueryParameter('order_by', order_by.value),
        ]

        if opened is not None:
            if not isinstance(opened, bool):
                raise TypeError('If supplied, opened must be a bool')
            parameters.append(QueryParameter('opened', opened))

        if public_id is not None:
            if not isinstance(public_id, str):
                raise TypeError('If supplied, public_id must be str')
            parameters.append(QueryParameter('public_id', public_id))

        result = ApiRequest.make(
            path=cls.list_path,
            method=HTTPMethod.GET,
            data=None,
            session=session,
            query_parameters=QueryParameters(parameters)
        )

        links = cls.optionally_decode_many(result, default_to_empty_list=True)
        assert links is not None
        return links
