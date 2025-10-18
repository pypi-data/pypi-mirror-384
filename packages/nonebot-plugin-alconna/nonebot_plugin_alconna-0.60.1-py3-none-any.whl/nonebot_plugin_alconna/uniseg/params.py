from typing import Annotated

from nonebot.exception import SkippedException
from nonebot.internal.adapter import Bot, Event, Message
from nonebot.internal.params import Depends
from nonebot.typing import T_State

from .constraint import UNISEG_MESSAGE, UNISEG_MESSAGE_ID, UNISEG_TARGET
from .exporter import SerializeFailed, Target
from .functions import get_message_id, get_target
from .message import UniMessage
from .segment import TS


async def _uni_msg(bot: Bot, event: Event, state: T_State) -> UniMessage:
    if event.get_type() != "message":
        raise SkippedException from None
    if UNISEG_MESSAGE in state:
        return state[UNISEG_MESSAGE]
    try:
        msg = event.get_message()
    except (NotImplementedError, ValueError):
        raise SkippedException from None
    return UniMessage.of(msg, bot=bot)


async def _orig_uni_msg(bot: Bot, event: Event, state: T_State) -> UniMessage:
    if event.get_type() != "message":
        raise SkippedException from None
    try:
        msg: Message = event.get_message()
    except (NotImplementedError, ValueError):
        raise SkippedException from None
    try:
        msg: Message = getattr(event, "original_message", msg)  # type: ignore
    except (NotImplementedError, ValueError):
        pass
    ans = UniMessage.of(msg, bot=bot)
    return await ans.attach_reply(event=event, bot=bot)


def _target(bot: Bot, event: Event, state: T_State) -> Target:
    if UNISEG_TARGET in state:
        return state[UNISEG_TARGET]
    try:
        return get_target(event=event, bot=bot)
    except (SerializeFailed, NotImplementedError, ValueError):
        raise SkippedException from None


def _msg_id(bot: Bot, event: Event, state: T_State) -> str:
    if UNISEG_MESSAGE_ID in state:
        return state[UNISEG_MESSAGE_ID]
    try:
        event.get_message()
    except ValueError:
        raise SkippedException from None
    return get_message_id(event=event, bot=bot)


def MessageTarget() -> Target:
    return Depends(_target, use_cache=True)


def UniversalMessage(origin: bool = False) -> UniMessage:
    return Depends(_orig_uni_msg, use_cache=True) if origin else Depends(_uni_msg, use_cache=True)


def MessageId() -> str:
    return Depends(_msg_id, use_cache=True)


def UniversalSegment(t: type[TS], index: int = 0) -> TS:
    async def _uni_seg(bot: Bot, event: Event, state: T_State) -> TS:
        message = await _uni_msg(bot, event, state)
        return message[t, index]

    return Depends(_uni_seg, use_cache=True)


UniMsg = Annotated[UniMessage, UniversalMessage()]
OriginalUniMsg = Annotated[UniMessage, UniversalMessage(origin=True)]
MsgId = Annotated[str, MessageId()]
MsgTarget = Annotated[Target, MessageTarget()]
