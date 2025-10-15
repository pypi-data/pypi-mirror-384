import pydantic as pd
import typing

class SenderModel(pd.BaseModel):
    senderId: str
    senderLevel: typing.Literal["owner", "administrator", "member", "indenpendent"]

class SessionModel(pd.BaseModel):
    recvId: str
    recvType: typing.Literal["user", "group"]

class TextObjectModel(pd.BaseModel):
    method: typing.Literal["markdown", "text", "html"]
    text: str

class MessageModel(pd.BaseModel):
    type: typing.Literal["message.receive.normal", "message.receive.instruction"]
    msgId: str
    parentId: typing.Optional[str]
    sender: SenderModel
    session: SessionModel
    content: TextObjectModel
    actionId: int

class ButtonCallbackModel(pd.BaseModel):
    type: typing.Literal["button.report.inline"]
    msgId: str
    sender: str
    value: str

class UserChangedModel(pd.BaseModel):
    type: typing.Literal["group.join", "group.leave", "bot.followed", "bot.unfollowed"]
    user: str
    group: typing.Optional[str]

EventModel = typing.Union[MessageModel, ButtonCallbackModel, UserChangedModel]