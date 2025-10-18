from base64 import b64decode
from collections.abc import Awaitable
from pathlib import Path
import random
from typing import TYPE_CHECKING, Callable, Literal, Optional, Union, overload

from nonebot import get_bot as _get_bot
from nonebot import get_bots
from nonebot.exception import ActionFailed
from nonebot.internal.adapter import Adapter, Bot, Event
from nonebot.internal.driver.model import Request
from nonebot.internal.matcher import current_bot, current_event
from nonebot.typing import T_State
from yarl import URL

from .constraint import log
from .segment import Image


async def reply_fetch(event: Optional[Event] = None, bot: Optional[Bot] = None):
    from .adapters import alter_get_builder

    if not event:
        try:
            event = current_event.get()
        except LookupError:
            return None
    if not bot:
        try:
            bot = current_bot.get()
        except LookupError:
            return None
    _adapter = bot.adapter
    adapter = _adapter.get_name()
    if not (fn := alter_get_builder(adapter)):
        return None
    return await fn.extract_reply(event, bot)


async def image_fetch(event: Event, bot: Bot, state: T_State, img: Image, **kwargs) -> Optional[bytes]:
    if img.raw:
        return img.raw_bytes
    if img.path:
        return Path(img.path).read_bytes()
    adapter_name = bot.adapter.get_name()
    if adapter_name == "RedProtocol":
        origin = img.origin
        if TYPE_CHECKING:
            from nonebot.adapters.red.bot import Bot
            from nonebot.adapters.red.message import MediaMessageSegment

            assert isinstance(bot, Bot)
            assert isinstance(origin, MediaMessageSegment)

        return await origin.download(bot)

    if img.url:  # mirai, qqguild, kook, villa, minecraft, ding
        req = Request("GET", img.url, **kwargs)
        resp = await bot.adapter.request(req)
        return resp.content  # type: ignore
    if not img.id:
        return None
    if adapter_name == "OneBot V11":
        if TYPE_CHECKING:
            from nonebot.adapters.onebot.v11.bot import Bot

            assert isinstance(bot, Bot)
        url = (await bot.get_image(file=img.id))["data"]["url"]
        req = Request("GET", url, **kwargs)
        resp = await bot.adapter.request(req)
        return resp.content  # type: ignore
    if adapter_name == "OneBot V12":
        if TYPE_CHECKING:
            from nonebot.adapters.onebot.v12.bot import Bot

            assert isinstance(bot, Bot)
        resp = (await bot.get_file(type="data", file_id=img.id))["data"]
        return b64decode(resp) if isinstance(resp, str) else bytes(resp)
    if adapter_name == "Mirai":
        url = f"https://gchat.qpic.cn/gchatpic_new/0/0-0-" f"{img.id.replace('-', '').upper()}/0"
        req = Request("GET", url, **kwargs)
        resp = await bot.adapter.request(req)
        return resp.content  # type: ignore
    if adapter_name == "Telegram":
        if TYPE_CHECKING:
            from nonebot.adapters.telegram.bot import Bot

            assert isinstance(bot, Bot)
        res = await bot.get_file(file_id=img.id)
        if not res.file_path:
            raise ActionFailed("Telegram", "get file failed")
        if (p := Path(res.file_path)).exists():  # telegram api local mode
            return p.read_bytes()
        url = URL(bot.bot_config.api_server) / "file" / f"bot{bot.bot_config.token}" / res.file_path
        req = Request("GET", url, **kwargs)
        resp = await bot.adapter.request(req)
        return resp.content  # type: ignore
    if adapter_name == "Feishu":
        if TYPE_CHECKING:
            from nonebot.adapters.feishu.bot import Bot
            from nonebot.adapters.feishu.event import MessageEvent

            assert isinstance(bot, Bot)
            assert isinstance(event, MessageEvent)
        return await bot.get_msg_resource(message_id=event.message_id, file_key=img.id, type_="image")
    if adapter_name == "ntchat":
        raise NotImplementedError("ntchat image fetch not implemented")
    return None


@overload
async def get_bot(*, index: int) -> Bot: ...


@overload
async def get_bot(*, rand: Literal[True]) -> Bot: ...


@overload
async def get_bot(*, bot_id: str) -> Bot: ...


@overload
async def get_bot(*, predicate: Callable[[Bot], Awaitable[bool]]) -> list[Bot]: ...


@overload
async def get_bot(*, predicate: Callable[[Bot], Awaitable[bool]], index: int) -> Bot: ...


@overload
async def get_bot(*, predicate: Callable[[Bot], Awaitable[bool]], rand: Literal[True]) -> Bot: ...


@overload
async def get_bot(*, predicate: Callable[[Bot], Awaitable[bool]], bot_id: str) -> Bot: ...


@overload
async def get_bot(*, adapter: Union[type[Adapter], str]) -> list[Bot]: ...


@overload
async def get_bot(*, adapter: Union[type[Adapter], str], index: int) -> Bot: ...


@overload
async def get_bot(*, adapter: Union[type[Adapter], str], rand: Literal[True]) -> Bot: ...


@overload
async def get_bot(*, adapter: Union[type[Adapter], str], bot_id: str) -> Bot: ...


async def get_bot(
    *,
    adapter: Union[type[Adapter], str, None] = None,
    bot_id: Optional[str] = None,
    index: Optional[int] = None,
    rand: bool = False,
    predicate: Union[Callable[[Bot], Awaitable[bool]], None] = None,
) -> Union[list[Bot], Bot]:
    if not predicate and not adapter:
        if rand:
            return random.choice(list(get_bots().values()))
        if index is not None:
            return list(get_bots().values())[index]
        return _get_bot(bot_id)
    bots = []
    for bot in get_bots().values():
        if not predicate:

            async def _check_adapter(bot: Bot):
                _adapter = bot.adapter
                if isinstance(adapter, str):
                    return _adapter.get_name() == adapter
                return isinstance(_adapter, adapter)  # type: ignore

            predicate = _check_adapter
        if await predicate(bot):
            bots.append(bot)
    log("TRACE", f"get bots: {bots}")
    if not bot_id:
        if rand:
            return random.choice(bots)
        if index is not None:
            return bots[index]
        return bots
    return next(bot for bot in bots if bot.self_id == bot_id)
