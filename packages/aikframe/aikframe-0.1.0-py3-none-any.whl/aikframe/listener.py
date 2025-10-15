from .decoder import decode_msg
from .msgpacket import *
import typing
import asyncio

class YunhuActivityManager:
    def __init__(self):
        # Unified hook
        self.unified_hook: set[typing.Callable[[EventModel], typing.Awaitable]] = set()
        # Message hook
        self.allmsg_hook: set[typing.Callable[[MessageModel], typing.Awaitable]] = set()
        self.instruct_hook: set[typing.Callable[[MessageModel], typing.Awaitable]] = set()
        self.msgtype_hook: dict[int, set[typing.Callable[[MessageModel], typing.Awaitable]]] = {}
        # Button click hook
        self.button_hook: set[typing.Callable[[ButtonCallbackModel], typing.Awaitable]] = set()
        # User change hook
        self.user_change_hook: set[typing.Callable[[UserChangedModel], typing.Awaitable]] = set()
        # Group joining hook
        self.group_join_hook: set[typing.Callable[[UserChangedModel], typing.Awaitable]] = set()
        self.group_exit_hook: set[typing.Callable[[UserChangedModel], typing.Awaitable]] = set()
        # Following hook
        self.follow_hook: set[typing.Callable[[UserChangedModel], typing.Awaitable]] = set()
        self.unfollow_hook: set[typing.Callable[[UserChangedModel], typing.Awaitable]] = set()
    def __get_hooks(self, e: EventModel) -> set[typing.Callable[[EventModel], typing.Awaitable]]:
        if e.type == "message.receive.normal":
            return set().union(
                self.unified_hook,
                self.allmsg_hook,
                self.msgtype_hook.get(0, set())
            )
        elif e.type == "message.receive.instruction":
            return set().union(
                self.unified_hook,
                self.allmsg_hook,
                self.instruct_hook,
                self.msgtype_hook.get(e.actionId, set())
            )
        elif e.type == "bot.followed":
            return set().union(
                self.unified_hook,
                self.user_change_hook,
                self.follow_hook
            )
        elif e.type == "bot.unfollowed":
            return set().union(
                self.unified_hook,
                self.user_change_hook,
                self.unfollow_hook
            )
        elif e.type == "group.join":
            return set().union(
                self.unified_hook,
                self.user_change_hook,
                self.group_join_hook
            )
        elif e.type == "group.leave":
            return set().union(
                self.unified_hook,
                self.user_change_hook,
                self.group_exit_hook
            )
        elif e.type == "button.report.inline":
            return set().union(
                self.unified_hook,
                self.button_hook
            )
        return set()
    async def receive_event(self, event: dict):
        rec = decode_msg(event)
        if rec is None:
            return
        hooks = self.__get_hooks(rec)
        for hook in hooks:
            asyncio.create_task(hook(rec))
        return rec
    # Registeration
    def register_unified(self):
        def __border(fn: typing.Callable[[EventModel], typing.Awaitable]):
            self.unified_hook.add(fn)
            return fn
        return __border
    def register_message(self, allow_instruct: bool = False):
        def __border(fn: typing.Callable[[MessageModel], typing.Awaitable]):
            if allow_instruct:
                self.allmsg_hook.add(fn)
            else:
                if 0 not in self.msgtype_hook:
                    self.msgtype_hook[0] = set()
                self.msgtype_hook[0].add(fn)
            return fn
        return __border
    def register_instruct(self, instruct: typing.Optional[int] = None):
        def __border(fn: typing.Callable[[MessageModel], typing.Awaitable]):
            if instruct is None:
                self.instruct_hook.add(fn)
            else:
                if instruct not in self.msgtype_hook:
                    self.msgtype_hook[instruct] = set()
                self.msgtype_hook[instruct].add(fn)
            return fn
        return __border
    # Register about change
    def register_user_changed(self):
        def __border(fn: typing.Callable[[UserChangedModel], typing.Awaitable]):
            self.user_change_hook.add(fn)
            return fn
        return __border
    def register_user_followed(self):
        def __border(fn: typing.Callable[[UserChangedModel], typing.Awaitable]):
            self.follow_hook.add(fn)
            return fn
        return __border
    def register_user_unfollowed(self):
        def __border(fn: typing.Callable[[UserChangedModel], typing.Awaitable]):
            self.unfollow_hook.add(fn)
            return fn
        return __border
    def register_user_joined(self):
        def __border(fn: typing.Callable[[UserChangedModel], typing.Awaitable]):
            self.group_join_hook.add(fn)
            return fn
        return __border
    def register_user_leaved(self):
        def __border(fn: typing.Callable[[UserChangedModel], typing.Awaitable]):
            self.group_exit_hook.add(fn)
            return fn
        return __border
    # Register about button
    def register_button(self):
        def __border(fn: typing.Callable[[ButtonCallbackModel], typing.Awaitable]):
            self.button_hook.add(fn)
            return fn
        return __border