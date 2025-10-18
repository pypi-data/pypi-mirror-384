from typing import TYPE_CHECKING, Any, Union

from nonebot.adapters import Bot, Event
from nonebot_adapter_tailchat.bot import Bot as TailChatBot
from nonebot_adapter_tailchat.event import AtMessageEvent, DefaultMessageEvent
from nonebot_adapter_tailchat.message import Message, MessageSegment
from nonebot_adapter_tailchat.model import MessageRet

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SerializeFailed, SupportAdapter, Target, export
from nonebot_plugin_alconna.uniseg.segment import At, Emoji, File, Image, Reply, Text


class TailChatMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.tail_chat

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, (AtMessageEvent, DefaultMessageEvent)):
            if gid := event.get_group_id():
                return Target(
                    event.get_converse_id(),
                    gid,
                    channel=True,
                    adapter=self.get_adapter(),
                    self_id=event.self_id,
                    scope=SupportScope.tail_chat,
                )
            return Target(
                event.get_converse_id(),
                private=True,
                channel=True,
                adapter=self.get_adapter(),
                self_id=event.self_id,
                scope=SupportScope.tail_chat,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, (AtMessageEvent, DefaultMessageEvent))
        return str(event.get_message_id())

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        if not seg.styles:
            return MessageSegment.text(seg.text)
        if seg.extract_most_style() == "link":
            if not getattr(seg, "_children", []):
                return MessageSegment.url(url=seg.text)
            return MessageSegment.url(url=seg.text, text=seg._children[0].text)  # type: ignore
        if seg.extract_most_style() == "markdown":
            return MessageSegment.md(seg.text)
        if seg.extract_most_style() == "code":
            return MessageSegment.code(seg.text)
        styles = {"b": False, "i": False, "u": False, "s": False}
        for style in seg.extract_most_styles():
            if style in {"bold", "italic", "underline", "strikethrough"}:
                styles[style[0]] = True
        return MessageSegment.text(seg.text, **styles)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.type == "channel" and seg.display:
            return MessageSegment.url(url=f"/main/group/{seg.target}", text=seg.display)
        return MessageSegment.at(uid=seg.target, nickname=seg.display)

    @export
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.emoji(text=seg.id)

    @export
    async def image(self, seg: Image, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.url:
            return MessageSegment.img(seg.url, width=seg.width, height=seg.height)
        if seg.__class__.to_url and seg.path:
            url = await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name)
            return MessageSegment.img(url, width=seg.width, height=seg.height)
        if seg.__class__.to_url and seg.raw:
            url = await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            return MessageSegment.img(url, width=seg.width, height=seg.height)
        raise SerializeFailed("tailchat image segment must have url")

    @export
    async def file(self, seg: File, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.url:
            return MessageSegment.file(name=seg.name, url=seg.url)
        if seg.__class__.to_url and seg.path:
            url = await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name)
            return MessageSegment.file(name=seg.name, url=url)
        if seg.__class__.to_url and seg.raw:
            url = await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            return MessageSegment.file(name=seg.name, url=url)
        raise SerializeFailed("tailchat file segment must have url")

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment("$tailchat:reply", {"extra": {"message_id": seg.id}})  # type: ignore

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, TailChatBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if message.has("$tailchat:reply"):
            reply_id = message.pop(message.index("$tailchat:reply")).data["extra"]["message_id"]
        else:
            reply_id = None
        if isinstance(target, Event):
            return await bot.send(target, message, meta={"reply": {"_id": reply_id}} if reply_id else None, **kwargs)  # type: ignore
        return await bot.sendMessage(
            content=message.decode(),
            converseId=target.id,
            groupId=None if target.private else target.parent_id,
            meta={"reply": {"_id": reply_id}} if reply_id else None,
            **kwargs,
        )

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, TailChatBot)
        if isinstance(mid, str):
            message_id = mid
        else:
            assert isinstance(mid, MessageRet)
            message_id = mid.id
        try:
            return await bot.recallMessage(messageId=message_id)
        except Exception:
            return await bot.deleteMessage(messageId=message_id)

    def get_reply(self, mid: Any):
        assert isinstance(mid, MessageRet)
        return Reply(mid.id, mid.content)
