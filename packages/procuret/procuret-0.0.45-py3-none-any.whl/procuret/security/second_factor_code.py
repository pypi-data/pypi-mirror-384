"""
Procuret Python
Second Factor Code Module
author: hugh@blinkybeach.com
"""
from pydoc import plain
from procuret.ancillary.session_perspective import Perspective
from typing import Optional
from procuret.http.method import HTTPMethod
from procuret.http.api_request import ApiRequest


class SecondFactorCode:

    PATH = '/second-factor-code'

    @staticmethod
    def create_with_email(
        email: str,
        plaintext_secret: str,
        perspective: Optional[Perspective]
    ) -> None:

        return SecondFactorCode._create(
            email=email,
            agent_id=None,
            plaintext_secret=plaintext_secret,
            perspective=perspective
        )

    @staticmethod
    def create_with_agent_id(
        agent_id: int,
        plaintext_secret: str,
        perspective: Optional[Perspective]
    ) -> None:

        return SecondFactorCode._create(
            email=None,
            agent_id=agent_id,
            plaintext_secret=plaintext_secret,
            perspective=perspective
        )

    @staticmethod
    def _create(
        email: Optional[str],
        agent_id: Optional[int],
        plaintext_secret: str,
        perspective: Optional[Perspective]
    ) -> None:

        data = {
            'email': email,
            'plaintext_secret': plaintext_secret,
            'agent_id': agent_id,
            'perspective': (
                perspective.value if perspective is not None else None
            )
        }

        ApiRequest.make(
            path=SecondFactorCode.PATH,
            method=HTTPMethod.POST,
            data=data,
            session=None,
            query_parameters=None
        )

        return None
