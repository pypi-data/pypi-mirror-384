from ..utils import MyAsyncClient, MyClient
from typing import Protocol, Union
from httpx import Response
import logging


logger = logging.getLogger(__name__)


class AsyncASURSO(Protocol):
    _SID: str
    _login: str
    _password: str
    _client: MyAsyncClient


class ASURSO(Protocol):
    _SID: str
    _login: str
    _password: str
    _client: MyClient


def _parse(client: Union[MyAsyncClient, MyClient], r: Response):
    client.cookies.update(r.cookies)

    if r.status_code != 200:
        logger.error(f"{r=}, {r.text=}, {r.status_code=}")

    return r.status_code == 200


async def logout_async(client: MyAsyncClient) -> bool:
    r = await client.delete("/services/security/logout")
    return _parse(client, r)


def logout_sync(client: MyClient) -> bool:
    r = client.delete("/services/security/logout")
    return _parse(client, r)


class AsyncLogoutMethod:
    async def logout(self: AsyncASURSO):
        return await logout_async(self._client)


class LogoutMethod:
    def logout(self: ASURSO):
        return logout_sync(self._client)
