"""
Procuret Python
Communication Option Module
author: hugh@blinkybeach.com
"""
from enum import Enum


class CommunicationOption(Enum):
    EMAIL_CUSTOMER = 'email_customer'
    DO_NOT_CONTACT_CUSTOMER = 'do_not_contact'
