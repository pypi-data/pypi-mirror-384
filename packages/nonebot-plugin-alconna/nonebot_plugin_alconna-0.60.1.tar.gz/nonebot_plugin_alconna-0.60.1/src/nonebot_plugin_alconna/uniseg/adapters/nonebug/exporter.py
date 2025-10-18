from typing import Union

from nonebot.adapters import Bot, Event

from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SupportAdapter, Target, export
from nonebot_plugin_alconna.uniseg.fallback import FallbackMessage, FallbackSegment
from nonebot_plugin_alconna.uniseg.segment import Text


class NonebugMessageExporter(MessageExporter[FallbackMessage]):
    def get_message_type(self):
        return FallbackMessage

    def get_message_id(self, event: Event) -> str:
        return event.get_session_id()

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.nonebug

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "FallbackSegment":
        return FallbackSegment.text(seg.text)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: FallbackMessage, **kwargs):
        return await bot.send(target, message, **kwargs)  # type: ignore
