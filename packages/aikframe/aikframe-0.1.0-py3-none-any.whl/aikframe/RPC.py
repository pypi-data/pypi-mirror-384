import aiohttp
from .msgpacket import SenderModel, SessionModel
from .streaming import YunhuStreamingContext
import typing
import os

_To = typing.Union[SenderModel, SessionModel, tuple[typing.Literal["user", "group"], typing.Union[str, int]], str, int]

def _normalize_to(to: _To):
    if isinstance(to, SessionModel):
        return to.recvId, to.recvType
    elif isinstance(to, SenderModel):
        return to.senderId, "user"
    elif isinstance(to, str) or isinstance(to, int):
        return str(to), "user"
    else:
        return str(to[1]), to[0]

async def send_message(
        to: _To, *,
        content: str,
        method: typing.Literal["text", "markdown", "html"],
        buttons: dict = {},
        parentId: typing.Optional[str] = None,
        token: typing.Optional[str] = None
    ):
    if token is None:
        if "YUNHU_API_TOKEN" not in os.environ:
            raise RuntimeError("Where is your yunhu token?")
        token = os.environ["YUNHU_API_TOKEN"]
    recvId, recvType = _normalize_to(to)
    cebber = {
        "recvId": recvId,
        "recvType": recvType,
        "contentType": method,
        "content": {
            "text": content,
            "buttons": buttons
        }
    }
    if parentId is not None:
        cebber["parentId"] = parentId
    async with aiohttp.ClientSession() as session:
        result = await session.post(
            url=f"https://chat-go.jwzhd.com/open-apis/v1/bot/send?token={token}",
            json=cebber
        )
        return await result.json()

async def set_board(
        to: _To, *,
        content: str,
        method: typing.Literal["text", "markdown", "html"],
        token: typing.Optional[str] = None
    ):
    if token is None:
        if "YUNHU_API_TOKEN" not in os.environ:
            raise RuntimeError("Where is your yunhu token?")
        token = os.environ["YUNHU_API_TOKEN"]
    recvId, recvType = _normalize_to(to)
    cebber = {
        "chatId": recvId,
        "chatType": recvType,
        "contentType": method,
        "content": content
    }
    async with aiohttp.ClientSession() as session:
        result = await session.post(
            url=f"https://chat-go.jwzhd.com/open-apis/v1/bot/board?token={token}",
            json=cebber
        )
        return await result.json()

def send_streaming_message(
        to: _To, *,
        method: typing.Literal["text", "markdown", "html"],
        token: typing.Optional[str] = None
    ):
    if token is None:
        if "YUNHU_API_TOKEN" not in os.environ:
            raise RuntimeError("Where is your yunhu token?")
        token = os.environ["YUNHU_API_TOKEN"]
    recvId, recvType = _normalize_to(to)
    return YunhuStreamingContext(token, recvId, recvType, method)