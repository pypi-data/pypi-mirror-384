from ..utils import parse_response, MyAsyncClient, MyClient
from .. import enums
from pydantic import BaseModel, Field
from typing import Protocol, List
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


class Chat(BaseModel):
    num: int
    id: int
    name: str
    chat_type: enums.ChatType = Field(..., alias="chatType")
    count_of_members: int = Field(..., alias="countOfMembers")
    admin_name: str = Field(..., alias="adminName")


async def get_chats_async(client: MyAsyncClient) -> List[Chat]:
    r = await client.get("/integration/chatManagement/chats/current")
    return parse_response(r, [Chat])


def get_chats_sync(client: MyClient) -> List[Chat]:
    r = client.get("/integration/chatManagement/chats/current")
    return parse_response(r, [Chat])


class AsyncGetChatsMethod:
    async def get_chats(self: AsyncASURSO) -> List[Chat]:
        return await get_chats_async(self._client)


class GetChatsMethod:
    def get_chats(self: ASURSO) -> List[Chat]:
        return get_chats_sync(self._client)
