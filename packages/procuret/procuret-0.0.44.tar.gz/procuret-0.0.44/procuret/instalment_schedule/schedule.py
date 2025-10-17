"""
Procuret Python
Instalment Schedule Module
author: hugh@blinkybeach.com
"""
from procuret.data.codable import Codable, CodingDefinition as CD
from typing import List, Any, TypeVar, Type, Optional
from procuret.instalment_line.line import InstalmentLine
from procuret.instalment_total_row.row import InstalmentTotalRow
from procuret.session import Session
from procuret.http.api_request import ApiRequest, HTTPMethod, QueryParameters
from procuret.http.query_parameter import QueryParameter

Self = TypeVar('Self', bound='InstalmentSchedule')


class InstalmentSchedule(Codable):

    coding_map = {
        'lines': CD(InstalmentLine, array=True),
        'series_id': CD(str),
        'has_interest': CD(bool),
        'total_row': CD(InstalmentTotalRow)
    }

    def __init__(
        self,
        lines: List[InstalmentLine],
        series_id: str,
        has_interest: bool,
        total_row: InstalmentTotalRow
    ) -> None:

        self._lines = lines
        self._series_id = series_id
        self._has_interest = has_interest
        self._total_row = total_row

        return

    lines: List[InstalmentLine] = property(lambda s: s._lines)
    series_id: str = property(lambda s: s._series_id)
    has_interest: bool = property(lambda s: s._has_interest)
    total_row: InstalmentTotalRow = property(lambda s: s._total_row)

    @classmethod
    def retrieve(
        Self: Type[Self],
        series_id: str,
        session: Session
    ) -> Optional[Self]:

        result = ApiRequest.make(
            path=Self.path,
            method=HTTPMethod.GET,
            data=None,
            session=session,
            query_parameters=QueryParameters([QueryParameter(
                key='entity_id',
                value=series_id
            )])
        )

        return Self.optionally_decode(result)
