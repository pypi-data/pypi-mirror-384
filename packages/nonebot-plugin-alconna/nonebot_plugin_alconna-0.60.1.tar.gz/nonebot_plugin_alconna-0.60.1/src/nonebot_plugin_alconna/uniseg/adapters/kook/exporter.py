from typing import TYPE_CHECKING, Any, Sequence, Union, cast

from nonebot.adapters import Bot, Event
from nonebot.adapters.kaiheila.api.model import MessageCreateReturn
from nonebot.adapters.kaiheila.bot import Bot as KBot
from nonebot.adapters.kaiheila.event import MessageEvent, PrivateMessageEvent
from nonebot.adapters.kaiheila.message import Message, MessageSegment, MessageSerializer
from tarina import lang

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SerializeFailed, SupportAdapter, Target, export
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    AtAll,
    Audio,
    Emoji,
    File,
    Hyper,
    Image,
    Reply,
    Segment,
    Text,
    Video,
    Voice,
)


class KookMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.kook

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.msg_id)

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if group_id := getattr(event, "group_id", None):
            return Target(
                str(group_id), adapter=self.get_adapter(), self_id=bot.self_id if bot else None, scope=SupportScope.kook
            )
        if user_id := getattr(event, "user_id", None):
            return Target(
                str(user_id),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.kook,
            )
        raise NotImplementedError

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.extract_most_style() == "markdown":
            return MessageSegment.KMarkdown(seg.text)
        if seg.styles:
            return MessageSegment.KMarkdown(str(seg))
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag == "role":
            return MessageSegment.mention_role(seg.target)
        if seg.flag == "channel":
            return MessageSegment.KMarkdown(f"(chn){seg.target}(chn)")
        return MessageSegment.mention(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.mention_here() if seg.here else MessageSegment.mention_all()

    @export
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.name:
            return MessageSegment.KMarkdown(f"(emj){seg.name}(emj)[{seg.id}]")
        return MessageSegment.KMarkdown(f":{seg.id}:")

    @export
    async def image(self, seg: Image, bot: Union[Bot, None]) -> "MessageSegment":
        if TYPE_CHECKING:
            assert isinstance(bot, KBot)
        name = seg.__class__.__name__.lower()
        if seg.id:
            return MessageSegment.image(seg.id)
        if seg.url:
            return MessageSegment.image(seg.url)
        if seg.__class__.to_url and seg.raw:
            return MessageSegment.image(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        if seg.__class__.to_url and seg.path:
            return MessageSegment.image(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        if seg.raw:
            return MessageSegment.local_image(seg.raw_bytes)
        if seg.path:
            return MessageSegment.local_image(seg.path)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def media(self, seg: Union[Voice, Video, Audio, File], bot: Union[Bot, None]) -> "MessageSegment":
        if TYPE_CHECKING:
            assert isinstance(bot, KBot)
        name = seg.__class__.__name__.lower()
        title = None if seg.name == seg.__default_name__ else seg.name
        method = {
            "voice": MessageSegment.audio,
            "audio": MessageSegment.audio,
            "video": MessageSegment.video,
            "file": MessageSegment.file,
        }[name]
        if seg.id or seg.url:
            return method(seg.id or seg.url, title)
        if seg.__class__.to_url and seg.raw:
            return method(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name), title
            )
        if seg.__class__.to_url and seg.path:
            return method(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name), title
            )
        local_method = {
            "voice": MessageSegment.local_audio,
            "audio": MessageSegment.local_audio,
            "video": MessageSegment.local_video,
            "file": MessageSegment.local_file,
        }[name]
        if seg.raw:
            return local_method(seg.raw_bytes, title)
        if seg.path:
            return local_method(seg.path, title)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def hyper(self, seg: Hyper, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.format == "xml":
            raise SerializeFailed(
                lang.require("nbp-uniseg", "failed_segment").format(adapter="kook", seg=seg, target="Card")
            )
        return MessageSegment.Card(seg.content or seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.quote(seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, KBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore

        if target.private:
            return await bot.send_msg(message_type="private", user_id=target.id, message=message, **kwargs)
        return await bot.send_msg(message_type="channel", channel_id=target.id, message=message, **kwargs)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        if isinstance(mid, str):
            if isinstance(context, PrivateMessageEvent):
                await bot.directMessage_delete(msg_id=mid)
            else:
                await bot.message_delete(msg_id=mid)
        _mid: MessageCreateReturn = cast(MessageCreateReturn, mid)

        assert _mid.msg_id

        assert isinstance(bot, KBot)
        if isinstance(context, Target):
            if context.private:
                await bot.directMessage_delete(msg_id=_mid.msg_id)
            else:
                await bot.message_delete(msg_id=_mid.msg_id)
        elif isinstance(context, PrivateMessageEvent):
            await bot.directMessage_delete(msg_id=_mid.msg_id)
        else:
            await bot.message_delete(msg_id=_mid.msg_id)

    async def edit(self, new: Sequence[Segment], mid: Any, bot: Bot, context: Union[Target, Event]):
        if TYPE_CHECKING:
            assert isinstance(bot, KBot)

        data = await MessageSerializer(await self.export(new, bot, True)).serialize(bot=bot)
        data.pop("type", None)
        if isinstance(mid, str):
            data["msg_id"] = mid
        else:
            _mid: MessageCreateReturn = cast(MessageCreateReturn, mid)
            if not _mid.msg_id:
                return
            data["msg_id"] = _mid.msg_id
        if isinstance(context, Target):
            if context.private:
                data.pop("quote", None)
                await bot.directMessage_update(**data)
            else:
                await bot.message_update(**data)
        elif isinstance(context, PrivateMessageEvent):
            data.pop("quote", None)
            await bot.directMessage_update(**data)
        else:
            await bot.message_update(**data)
        return

    async def reaction(
        self,
        emoji: Emoji,
        mid: Any,
        bot: Bot,
        context: Union[Target, Event],
        delete: bool = False,
    ):
        assert isinstance(bot, KBot)
        if isinstance(mid, str):
            msg_id = mid
        else:
            _mid: MessageCreateReturn = cast(MessageCreateReturn, mid)
            if not _mid.msg_id:
                return
            msg_id = _mid.msg_id
        if isinstance(context, Target):
            if context.private:
                if delete:
                    return await bot.directMessage_deleteReaction(msg_id=msg_id, emoji=emoji.id)
                return await bot.directMessage_addReaction(msg_id=msg_id, emoji=emoji.id)
            if delete:
                return await bot.message_deleteReaction(msg_id=msg_id, emoji=emoji.id)
            return await bot.message_addReaction(msg_id=msg_id, emoji=emoji.id)
        if isinstance(context, PrivateMessageEvent):
            if delete:
                return await bot.directMessage_deleteReaction(msg_id=msg_id, emoji=emoji.id)
            return await bot.directMessage_addReaction(msg_id=msg_id, emoji=emoji.id)
        if delete:
            return await bot.message_deleteReaction(msg_id=msg_id, emoji=emoji.id)
        return await bot.message_addReaction(msg_id=msg_id, emoji=emoji.id)

    def get_reply(self, mid: Any):
        _mid: MessageCreateReturn = cast(MessageCreateReturn, mid)
        if not _mid.msg_id:
            raise NotImplementedError
        return Reply(_mid.msg_id)
