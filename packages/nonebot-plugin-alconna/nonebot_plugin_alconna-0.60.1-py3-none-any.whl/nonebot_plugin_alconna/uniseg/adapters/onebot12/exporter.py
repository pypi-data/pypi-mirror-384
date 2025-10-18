from pathlib import Path
from typing import TYPE_CHECKING, Any, Union, cast

from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v12.bot import Bot as OnebotBot
from nonebot.adapters.onebot.v12.event import MessageEvent
from nonebot.adapters.onebot.v12.message import Message, MessageSegment
from tarina import lang

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SerializeFailed, SupportAdapter, Target, export
from nonebot_plugin_alconna.uniseg.segment import At, AtAll, Audio, File, Image, Reply, Text, Video, Voice


class Onebot12MessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.onebot12

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if TYPE_CHECKING:
            bot = cast(Union[OnebotBot, None], bot)
        if channel_id := getattr(event, "channel_id", None):
            guild_id = getattr(event, "guild_id", None)
            return Target(
                str(channel_id),
                str(guild_id) if guild_id else "",
                channel=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                platform=bot.platform if bot else None,
                scope=SupportScope.ensure_ob12(bot.platform) if bot else SupportScope.onebot12_other,
            )
        if guild_id := getattr(event, "guild_id", None):
            return Target(
                str(guild_id),
                channel=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                platform=bot.platform if bot else None,
                scope=SupportScope.ensure_ob12(bot.platform) if bot else SupportScope.onebot12_other,
            )
        if group_id := getattr(event, "group_id", None):
            return Target(
                str(group_id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                platform=bot.platform if bot else None,
                scope=SupportScope.ensure_ob12(bot.platform) if bot else SupportScope.onebot12_other,
            )
        if user_id := getattr(event, "user_id", None):
            return Target(
                str(user_id),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                platform=bot.platform if bot else None,
                scope=SupportScope.ensure_ob12(bot.platform) if bot else SupportScope.onebot12_other,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.message_id)

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag != "user":
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))
        return MessageSegment.mention(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.mention_all()

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Union[Bot, None]) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "voice": MessageSegment.voice,
            "video": MessageSegment.video,
            "audio": MessageSegment.audio,
            "file": MessageSegment.file,
        }[name]
        if seg.id:
            return method(seg.id)
        if not bot:
            raise NotImplementedError
        if seg.url:
            resp = await bot.upload_file(type="url", name=seg.name, url=seg.url)
            return method(resp["file_id"])
        if seg.path:
            if seg.__class__.to_url:
                resp = await bot.upload_file(
                    type="url",
                    name=Path(seg.path).name if seg.name == seg.__default_name__ else seg.name,
                    url=await seg.__class__.to_url(
                        seg.path, bot, None if seg.name == seg.__default_name__ else seg.name
                    ),
                )
            else:
                resp = await bot.upload_file(type="path", path=str(seg.path), name=Path(seg.path).name)
            return method(resp["file_id"])
        if seg.raw:
            if seg.__class__.to_url:
                resp = await bot.upload_file(
                    type="url",
                    name=seg.name,
                    url=await seg.__class__.to_url(
                        seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name
                    ),
                )
            else:
                resp = await bot.upload_file(type="data", data=seg.raw_bytes, name=seg.name)
            return method(resp["file_id"])
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.reply(seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, OnebotBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore
        if target.private:
            return await bot.send_message(detail_type="private", user_id=target.id, message=message, **kwargs)
        if target.channel:
            return await bot.send_message(
                detail_type="channel", channel_id=target.id, guild_id=target.parent_id, message=message, **kwargs
            )
        return await bot.send_message(detail_type="group", group_id=target.id, message=message, **kwargs)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, OnebotBot)

        await bot.delete_message(message_id=mid["message_id"] if isinstance(mid, dict) else mid)

    def get_reply(self, mid: Any):
        return Reply(mid["message_id"])
