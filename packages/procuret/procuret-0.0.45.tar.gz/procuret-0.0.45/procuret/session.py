"""
Procuret Python
Session Module
author: hugh@blinkybeach.com
"""
import json
from procuret.data.codable import CodingDefinition as CD
from procuret.ancillary.abstract_session import AbstractSession
from procuret.ancillary.session_lifecycle import Lifecycle
from procuret.ancillary.session_perspective import Perspective
from procuret.http.api_request import ApiRequest
from procuret.http.method import HTTPMethod
from typing import TypeVar, Type, Optional
from procuret.errors.inconsistent import InconsistentState
from procuret.security.second_factor_code import SecondFactorCode
from getpass import getpass
from base64 import b64decode, b64encode

Self = TypeVar('Self', bound='Session')


class Session(AbstractSession):

    PATH = '/session'

    coding_map = {
        'session_id': CD(int),
        'session_key': CD(str),
        'api_key': CD(str),
        'lifecycle': CD(Lifecycle),
        'perspective': CD(Perspective)
    }

    def __init__(
        self,
        session_id: int,
        session_key: str,
        api_key: str,
        lifecycle: Lifecycle,
        perspective: Perspective,
        on_behalf_of: Optional[int] = None
    ) -> None:

        self._session_id = session_id
        self._session_key = session_key
        self._api_key = api_key
        self._lifecycle = lifecycle
        self._perspective = perspective
        self._on_behalf_of = on_behalf_of

        return

    session_id = property(lambda s: s._session_id)
    session_key = property(lambda s: s._session_key)
    api_key = property(lambda s: s._api_key)
    lifecycle = property(lambda s: s._lifecycle)
    perspective = property(lambda s: s._perspective)
    on_behalf_of = property(lambda s: s._on_behalf_of)

    acts_for_another_agent = property(lambda s: s.on_behalf_of is not None)

    def _to_storage_format(self) -> str:
        return b64encode(
            json.dumps(self.encode()).encode('utf-8')
        ).decode('utf-8')


    def save_to_file(
        self,
        filepath: str
    ) -> None:

        with open(filepath, 'w') as wfile:
            wfile.write(self._to_storage_format())

        return None

    def acting_for(self, agent: int) -> Self:
        return Session(
            session_id=self._session_id,
            session_key=self._session_key,
            api_key=self._api_key,
            lifecycle=self._lifecycle,
            perspective=self._perspective,
            on_behalf_of=agent
        )

    @classmethod
    def load_from_file(
        self,
        filepath: str
    ) -> Self:

        with open(filepath, 'r') as rfile:
            return Session._from_storage_format(rfile.read())

    @classmethod
    def create_with_email(
        Self: Type[Self],
        email: str,
        plaintext_secret: str,
        perspective: Perspective,
        code: str,
        lifecycle: Lifecycle = Lifecycle.LONG_LIVED
    ) -> Self:

        data = {
            'email': email,
            'secret': plaintext_secret,
            'perspective': perspective.value,
            'lifecycle': lifecycle.value,
            'code': code
        }

        result = ApiRequest.make(
            path=Self.PATH,
            method=HTTPMethod.POST,
            data=data,
            session=None,
            query_parameters=None
        )
        if result is None:
            raise InconsistentState

        return Self.decode(result)

    def interactively_to_file(
        self
    ) -> None:

        print('Enter the filepath into which you with to save this Session.')
        filepath = input('filepath: ')

        self.save_to_file(filepath)

        print(f'This Session has been saved to {filepath}')

        return None

    @classmethod
    def from_interactive_prompt(
        Self: Type[Self]
    ) -> Self:

        print('\nInteractive Procuret Session Creation Prompt\n')
        print('*** Be careful with Sessions! Never store them where someone el\
se could access them. Never give them to anyone who asks, even if they say the\
y are from Procuret. Always keep your passphrase a secret. ***')

        print("""
What perspective would you like the Session to have?
"1" for supplier
"2" for business (Customer)
"3" for administrator
"4" for sales (PM)
"5" for treasury
"6" for investor
"7" for customer_support (Customer Success)
""")
        perspective = Perspective(int(input('perspective: ')))

        print("""
Would you like the Session to be long lived, or short lived? Choose long-lived
if the Session will be used for a very long time. If unsure, choose
short-lived.
"1" for short lived
"2" for long lived
""")
        lifecycle = Lifecycle(int(input('lifecycle: ')))

        print("Now, input your Procuret account credentials.")
        email_address = input('email: ')
        secret = getpass('password: ')

        print('Requesting second factor code...')

        SecondFactorCode.create_with_email(
            email=email_address,
            plaintext_secret=secret,
            perspective=perspective
        )

        print(f'Enter the six digit code Procuret just sent to \
{email_address}')

        code = input('code: ')

        print('Creating Session...')
    
        session = Self.create_with_email(
            email=email_address,
            plaintext_secret=secret,
            perspective=perspective,
            lifecycle=lifecycle,
            code=code
        )

        print(f'Session created with ID {session._session_id}')

        return session

    @classmethod
    def _from_storage_format(
        Self: Type[Self],
        data: str
    ) -> Self:

        return Self.decode(json.loads(b64decode(data).decode('utf-8')))
