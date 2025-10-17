"""
Procuret API
Entity ID Type
author: hugh@blinkybeach.com
"""
from enum import Enum


class EntityIdType(Enum):

    ABN = 1
    ACN = 2
    NZBN = 3
    NZIRD = 5
