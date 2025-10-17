"""
Procuret Python
Payment Series Module
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
from procuret.payment_series.payment_mechanism import PaymentMechanism

Self = TypeVar('Self', bound='PaymentSeries')


class OrderBy(Enum):
    CREATED = 'created'


class PaymentSeries(Codable):

    path = '/payment/series'

    coding_map = {
        'public_id': CD(str),
        'created': CD(ProcuretTime),
        'creating_agent': CD(int),
        'payment_method': CD(PaymentMethodHeadline, optional=True),
        'customer': CD(EntityHeadline),
        'supplier': CD(EntityHeadline),
        'exchange_id': CD(str),
        'amount': CD(Amount),
        'sum_payments': CD(Amount),
        'total_payable': CD(Amount),
        'identifier': CD(str),
        'mechanism': CD(PaymentMechanism),
        'disposition': CD(Disposition)
    }

    OrderBy = OrderBy
  
    def __init__(
        self,
        public_id: str,
        created: ProcuretTime,
        creating_agent: str,
        payment_method: Optional[PaymentMethodHeadline],
        customer: EntityHeadline,
        supplier: EntityHeadline,
        exchange_id: str,
        amount: Amount,
        sum_payments: Amount,
        total_payable: Amount,
        identifier: str,
        mechanism: PaymentMechanism,
        disposition: Disposition
    ) -> None:

        self._public_id = public_id
        self._created = created
        self._creating_agent = creating_agent
        self._payment_method = payment_method
        self._customer = customer
        self._supplier = supplier
        self._exchange_id = exchange_id
        self._amount = amount
        self._sum_payments = sum_payments
        self._total_payable = total_payable
        self._identifier = identifier
        self._mechanism = mechanism
        self._disposition = disposition

        return

    public_id: str = property(lambda s: s._public_id)
    created: ProcuretTime = property(lambda s: s._created)
    creating_agent: int = property(lambda s: s._creating_agent)
    payment_method: Optional[PaymentMethodHeadline] = property(
        lambda s: s._payment_method
    )
    customer: EntityHeadline = property(lambda s: s._customer)
    supplier: EntityHeadline = property(lambda s: s._supplier)
    exchange_id: str = property(lambda s: s._exchange_id)
    amount: Amount = property(lambda s: s._amount)
    sum_payments: Amount = property(lambda s: s._sum_payments)
    total_payable: Amount = property(lambda s: s._total_payable)
    identifier: str = property(lambda s: s._identifier)
    mechanism: PaymentMechanism = property(lambda s: s._mechanism)
    disposition: Disposition = property(lambda s: s._disposition)

    @classmethod
    def retrieve(
        Self: Type[Self],
        session: Session,
        public_id: str
    ) -> Optional[Self]:

        if not isinstance(public_id, str):
            raise TypeError('`public_id` must be of type `str`')

        result = Self.retrieve_many(
            session=session,
            public_id=public_id
        )

        if len(result) < 1:
            return None
        
        return result[0]

    @classmethod
    def retrieve_many(
        Self: Type[Self],
        session: Session,
        public_id: Optional[str] = None,
        text_fragment: Optional[str] = None,
        business_id: Optional[str] = None,
        method_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        order: Order = Order.DESCENDING,
        order_by: OrderBy = OrderBy.CREATED
    ) -> List[Self]:

        QP = QueryParameter
        aq = [
            QP('limit', limit),
            QP('offset', offset),
            QP('order', order.value),
            QP('order_by', order_by.value),
            QP.optionally('any_fragment', text_fragment),
            QP.optionally('business_id', business_id),
            QP.optionally('method_id', method_id),
            QP.optionally('public_id', public_id)
        ]

        result = ApiRequest.make(
            path=Self.path + '/list',
            method=HTTPMethod.GET,
            data=None,
            session=session,
            query_parameters=QueryParameters([q for q in aq if q is not None])
        )

        return Self.decode_many(result) or []
