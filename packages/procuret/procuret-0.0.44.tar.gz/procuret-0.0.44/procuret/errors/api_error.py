"""
Procuret Python
Api Error Module
author: hugh@blinkybeach.com
"""
from procuret.errors.error import ProcuretError


class ProcuretApiError(RuntimeError, ProcuretError):

    def __init__(
        self,
        http_code: int
    ) -> None:
        super().__init__('Procuret API responded to your request with an error\
code - {c}. There may be a bug in the Procuret Python library, or Procuret API\
 may be experiencing a temporary disruption. If this happens repeatedly, pleas\
e contact us at support@procuret.com'.format(c=str(http_code)))
