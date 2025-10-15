from .msgpacket import SenderModel, SessionModel, MessageModel, TextObjectModel, ButtonCallbackModel, UserChangedModel

def decode_msg(msg: dict):
    try:
        mtype = msg["header"]["eventType"]
        event = msg["event"]
        if mtype in ["message.receive.normal", "message.receive.instruction"]:
            # Session
            if event["chat"]["chatType"] == "bot":
                session = SessionModel(recvId=event["sender"]["senderId"], recvType="user")
            else:
                session = SessionModel(recvId=event["chat"]["chatId"], recvType="group")
            # Content type
            if event["message"]["contentType"] in ["text", "html", "markdown"]:
                print("EOK")
                content = TextObjectModel(method=event["message"]["contentType"], text=event["message"]["content"]["text"])
            else:
                return None
            # Build object
            return MessageModel(
                type=mtype,
                msgId=event["message"]["msgId"],
                parentId=(None if event["message"]["parentId"] == "" else event["message"]["parentId"]),
                sender=SenderModel(
                    senderId=event["sender"]["senderId"],
                    senderLevel=("indenpendent" if (session.recvType == "user") else event["sender"]["senderUserLevel"])
                ),
                session=session,
                content=content,
                actionId=(0 if mtype == "message.receive.normal" else event["message"]["commandId"])
            )
        elif mtype == "button.report.inline":
            return ButtonCallbackModel(
                type="button.report.inline",
                msgId=event["msgId"],
                sender=event["userId"],
                value=event["value"]
            )
        elif mtype in ["group.join", "group.leave"]:
            return UserChangedModel(
                type=mtype,
                user=event["userId"],
                group=event["chatId"]
            )
        elif mtype in ["bot.follow", "bot.unfollow"]:
            return UserChangedModel(
                type=mtype,
                user=event["userId"],
                group=None
            )
    except Exception:
        return None