"""
Procuret Python
Inconsistent State Error
author: hugh@blinkybeach.com
"""
from procuret.errors.error import ProcuretError


class InconsistentState(RuntimeError, ProcuretError):

    def __init__(self) -> None:
        super().__init__('Procuret API responded in a manner inconsistent wit\
h Procuret Python\'s expectations. This may indicate that there is a bug in t\
he Procuret Python library, or that Procuret API has responded in a manner in\
consistent with its documentation. Please contact us at support@procuret.com')
