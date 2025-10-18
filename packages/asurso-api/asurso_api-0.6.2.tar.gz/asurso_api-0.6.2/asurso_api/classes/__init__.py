from ..functions.attestation import Attestation
from ..functions.chats import Chat
from ..functions.dashboard import Dashboard
from ..functions.login import LoginInfo, LoginInfoPerm, LoginInfoTemp
from ..functions.info import Info
from ..functions.lessons import LessonsDay, Lesson
from ..functions.organization import Organization
from ..functions.reports import GroupAttestation, CurrentPerformance
from ..functions import (
    attestation,
    chats,
    dashboard,
    login,
    info,
    lessons,
    organization,
    reports,
)

from ..functions import AsyncMethods, Methods
from ..utils import hash_password, MyClient, MyAsyncClient
from typing import Union
import httpx


class AsyncASURSO(AsyncMethods):
    _login: str
    _password: str
    _client: "MyAsyncClient"
    _SID: str

    def __init__(
        self,
        login: str,
        password: str,
        timeout: int = 60,
        proxy: Union[httpx.URL, str, httpx.Proxy, None] = None,
        password_is_hashed: bool = False
    ):
        """
        Args:
            login (str): your ASURSO account's login.
            password (str): your ASURSO account's password.
            timeout (int): httpx.AsyncClient's timeout in seconds. Defaults to 60.
            proxy (Union[httpx.Proxy, None], optional): proxy for httpx.AsyncClient. Defaults to None.
            password_is_hashed (bool): password is needed to be hashed or not. Defaults to False.
        """
        self._login = login
        self._password = password if password_is_hashed else hash_password(password)

        self._SID = ""
        self._client = MyAsyncClient(
            base_url="https://spo.asurso.ru", timeout=timeout, proxy=proxy
        )

    async def __aenter__(self):
        await self.login(True)
        return self

    async def __aexit__(self, *exc):
        await self.logout()
        if exc and any(exc):
            builded_exc = exc[1]
            builded_exc.with_traceback(exc[2])
            raise builded_exc


class ASURSO(Methods):
    _login: str
    _password: str
    _client: "MyClient"
    _SID: str

    def __init__(
        self,
        login: str,
        password: str,
        timeout: int = 60,
        proxy: Union[httpx.URL, str, httpx.Proxy, None] = None,
        password_is_hashed: bool = False
    ):
        """Just create ASURSO object to use this API

        Args:
            login (str): your ASURSO account's login.
            password (str): your ASURSO account's password.
            timeout (int): httpx.AsyncClient's timeout in seconds. Defaults to 60.
            proxy (Union[httpx.Proxy, None], optional): proxy for httpx.AsyncClient. Defaults to None.
            password_is_hashed (bool): password is needed to be hashed or not. Defaults to False.
        """
        self._login = login
        self._password = password if password_is_hashed else hash_password(password)

        self._SID = ""
        self._client = MyClient(
            base_url="https://spo.asurso.ru", timeout=timeout, proxy=proxy
        )

    def __enter__(self):
        self.login(True)
        return self

    def __exit__(self, *exc):
        self.logout()
        if exc and any(exc):
            builded_exc = exc[1]
            builded_exc.with_traceback(exc[2])
            raise builded_exc
