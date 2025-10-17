"""
Procuret API Python
Sale Nomenclature Module
author: hugh@blinkybeach.com
"""
from enum import IntEnum


class SaleNomenclature(IntEnum):

    INVOICE = 1
    ORDER = 2
    SHOPIFY_ORDER = 3
    REFERENCE = 4
