"""
Procuret Python
Human Identity Document State Module
author: hugh@blinkybeach.com
"""
from enum import Enum


class HumanIdentityDocumentState(Enum):
    NOT_VERIFIED = 1
    VERIFIED_VALID = 2
    INVALID = 3
