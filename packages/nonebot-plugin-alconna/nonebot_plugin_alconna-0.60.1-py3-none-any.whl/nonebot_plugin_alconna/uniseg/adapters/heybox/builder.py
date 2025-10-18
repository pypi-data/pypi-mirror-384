from nonebot.adapters.heybox.message import MessageSegment  # type: ignore

from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.segment import Text


class HeyboxMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.heybox

    @build("text")
    def text(self, seg: MessageSegment):
        return Text(seg.data["text"])
