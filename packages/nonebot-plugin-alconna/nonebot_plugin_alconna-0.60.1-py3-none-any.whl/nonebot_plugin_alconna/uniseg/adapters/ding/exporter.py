from typing import Union

from nonebot.adapters import Bot, Event
from nonebot.adapters.ding import Bot as DingBot
from nonebot.adapters.ding.event import ConversationType, MessageEvent
from nonebot.adapters.ding.message import Message, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SupportAdapter, Target, export
from nonebot_plugin_alconna.uniseg.segment import At, AtAll, Image, Text


class DingMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.ding

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, MessageEvent):
            if event.conversationType == ConversationType.private:
                return Target(
                    event.senderId,
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.ding,
                )
            return Target(
                event.conversationId,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.ding,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.msgId)

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.atDingtalkIds(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.atAll()

    @export
    async def image(self, seg: Image, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.url:
            return MessageSegment.image(seg.url)
        if seg.__class__.to_url and seg.path:
            return MessageSegment.image(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        if seg.__class__.to_url and seg.raw:
            return MessageSegment.image(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        raise ValueError("github image segment must have url")

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, DingBot)
        if isinstance(target, Target):
            raise NotImplementedError
        return await DingBot.send(bot, target, message=message, **kwargs)  # type: ignore
