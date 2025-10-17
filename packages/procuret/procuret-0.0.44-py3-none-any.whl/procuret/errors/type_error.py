"""
Procuret Python
Type Error Module
author: hugh@blinkybeach.com
"""
from procuret.errors.error import ProcuretError
from typing import Union, Tuple, Any


class ProcuretTypeError(TypeError, ProcuretError):

    _PLURAL_TEMPLATE = '{v} must be an instance of one of types {t1} or {t2}, \
not {s}'

    _SINGULAR_TEMPLATE = '{v} must be an instance of type {t}, not {s}'

    def __init__(
        self,
        valid_types: Union[Tuple[str], str],
        supplied_variable: Any,
        variable_name: str
    ) -> None:

        if isinstance(valid_types, tuple):
            return super().__init__(self._PLURAL_TEMPLATE.format(
                v=variable_name,
                t1=', '.join(str(valid_types[:-1])),
                t2=valid_types[-1],
                s=str(type(supplied_variable))
            ))

        return super().__init__(self._SINGULAR_TEMPLATE.format(
            v=variable_name,
            t=valid_types,
            s=str(type(supplied_variable))
        ))
