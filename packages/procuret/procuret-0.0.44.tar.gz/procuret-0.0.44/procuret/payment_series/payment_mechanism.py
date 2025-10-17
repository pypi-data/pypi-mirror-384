"""
Procuret Python
Payment Mechanism Module
author: inkalchemi@gmail.com
"""
from enum import IntEnum
from typing import TypeVar

Self = TypeVar('Self', bound='PaymentMechanism')


class PaymentMechanism(IntEnum):

    ON_PLATFORM = 1
    OFF_PLATFORM = 2
    STRIPE_SUBSCRIPTION = 3
    UNKNOWN = 4


    @staticmethod
    def name_for(mechanism: Self) -> str:
        return {
            PaymentMechanism.ON_PLATFORM: 'On Platform',
            PaymentMechanism.OFF_PLATFORM: 'Off Platform',
            PaymentMechanism.UNKNOWN: 'Unknown',
            PaymentMechanism.STRIPE_SUBSCRIPTION: 'Stripe Subscription'
        }[mechanism]
