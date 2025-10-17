"""
Procuret Python
HTTP Method Module
author: hugh@blinkybeach.com
"""
from enum import Enum


class HTTPMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    DELETE = 'DELETE'
    PUT = 'PUT'
    PATCH = 'PATCH'
