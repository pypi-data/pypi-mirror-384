from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot, Event
from tarina import lang

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SerializeFailed, SupportAdapter, Target, export
from nonebot_plugin_alconna.uniseg.segment import File, Hyper, Image, Text, Video

if TYPE_CHECKING:
    from nonebot.adapters.ntchat.message import Message, MessageSegment  # type: ignore


class NTChatMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        from nonebot.adapters.ntchat.message import Message  # type: ignore

        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.ntchat

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        from_wxid = getattr(event, "from_wxid", None)
        room_wxid = getattr(event, "room_wxid", "")
        if from_wxid:
            return Target(
                from_wxid,
                room_wxid,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.wechat,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.ntchat.event import MessageEvent  # type: ignore

        assert isinstance(event, MessageEvent)
        return str(event.msgid)  # type: ignore

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        from nonebot.adapters.ntchat.message import MessageSegment  # type: ignore

        return MessageSegment.text(seg.text)

    @export
    async def res(self, seg: Union[Image, File, Video], bot: Union[Bot, None]) -> "MessageSegment":
        from nonebot.adapters.ntchat.message import MessageSegment  # type: ignore

        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "video": MessageSegment.video,
            "file": MessageSegment.file,
        }[name]
        if seg.path:
            return method(seg.path)
        if seg.raw:
            return method(seg.raw_bytes)
        if seg.url or seg.id:
            return method(seg.url or seg.id)  # type: ignore
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def hyper(self, seg: Hyper, bot: Union[Bot, None]) -> "MessageSegment":
        from nonebot.adapters.ntchat.message import MessageSegment  # type: ignore

        if seg.format == "json" and seg.content and "card_wxid" in seg.content:
            return MessageSegment.card(seg.content["card_wxid"])  # type: ignore
        if seg.format != "xml" or not seg.raw:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="hyper", seg=seg))
        return MessageSegment.xml(seg.raw)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: "Message", **kwargs):
        from nonebot.adapters.ntchat.bot import Bot as NTChatBot  # type: ignore
        from nonebot.adapters.ntchat.bot import send  # type: ignore

        assert isinstance(bot, NTChatBot)

        if isinstance(target, Event):
            return await send(bot, target, message, **kwargs)  # type: ignore

        class FakeEvent:
            from_wxid = target.id
            if target.parent_id:
                room_wxid = target.parent_id

        return await send(bot, FakeEvent, message, **kwargs)  # type: ignore
