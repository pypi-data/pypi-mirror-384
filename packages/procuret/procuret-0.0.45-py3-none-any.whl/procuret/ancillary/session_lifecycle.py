"""
Procuret Python
Session Lifecycle Enumeration
author: hugh@blinkybeach.com
"""
from enum import Enum


class Lifecycle(Enum):
    SHORT_LIVED = 1
    LONG_LIVED = 2
