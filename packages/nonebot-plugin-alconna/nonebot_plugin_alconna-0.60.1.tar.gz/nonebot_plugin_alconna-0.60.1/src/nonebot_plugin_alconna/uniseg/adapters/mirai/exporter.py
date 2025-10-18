from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from nonebot.adapters import Bot, Event
from nonebot.adapters.mirai.bot import Bot as MiraiBot
from nonebot.adapters.mirai.bot import UploadMethod
from nonebot.adapters.mirai.event import (
    ActiveMessage,
    BotMuteEvent,
    BotUnmuteEvent,
    FriendEvent,
    GroupEvent,
    GroupMessage,
    MemberEvent,
    MessageEvent,
    NudgeEvent,
)
from nonebot.adapters.mirai.message import Message, MessageSegment
from nonebot.adapters.mirai.message import Video as VideoSegment
from nonebot.adapters.mirai.model.common import FileInfo
from nonebot.internal.driver import Request
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
    Reference,
    RefNode,
    Reply,
    Text,
    Video,
    Voice,
)


class MiraiMessageExporter(MessageExporter[Message]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.mirai

    def get_message_type(self):
        return Message

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, GroupMessage):
            return Target(
                str(event.sender.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        if isinstance(event, MessageEvent):
            return Target(
                str(event.sender.id),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        if isinstance(event, (BotMuteEvent, BotUnmuteEvent)):
            return Target(
                str(event.operator.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        if isinstance(event, MemberEvent):
            return Target(
                str(event.member.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        if isinstance(event, GroupEvent):
            return Target(
                str(event.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        if isinstance(event, FriendEvent):
            return Target(
                str(event.friend.id),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        if isinstance(event, NudgeEvent):
            return Target(
                str(event.subject.id),  # type: ignore
                private=event.scene != "group",
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
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
        return MessageSegment.at(int(seg.target), seg.display)

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.at_all()

    @export
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.face(int(seg.id), seg.name)

    @export
    async def media(self, seg: Union[Image, Voice, Audio], bot: Union[Bot, None]) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "voice": MessageSegment.voice,
            "audio": MessageSegment.voice,
        }[name]
        if seg.id:
            return method(seg.id)
        if seg.url:
            return method(url=seg.url)
        if seg.path:
            return method(path=str(seg.path))
        if seg.__class__.to_url and seg.raw:
            return method(
                url=await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def video(self, seg: Video, bot: Union[Bot, None]) -> "MessageSegment":
        if TYPE_CHECKING:
            assert isinstance(bot, MiraiBot)
        if seg.id:
            return VideoSegment.parse({"videoId": seg.id})
        if seg.thumbnail:
            if seg.raw_bytes:
                video_data: Union[bytes, Path] = seg.raw_bytes
            elif seg.path:
                video_data: Union[bytes, Path] = Path(seg.path)
            elif seg.url:
                resp = await bot.adapter.request(Request("GET", seg.url))
                video_data: Union[bytes, Path] = resp.content  # type: ignore
            else:
                raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="video", seg=seg))
            if seg.thumbnail.raw_bytes:
                thumbnail_data: Union[bytes, Path] = seg.thumbnail.raw_bytes
            elif seg.thumbnail.path:
                thumbnail_data: Union[bytes, Path] = Path(seg.thumbnail.path)
            elif seg.thumbnail.url:
                resp = await bot.adapter.request(Request("GET", seg.thumbnail.url))
                thumbnail_data: Union[bytes, Path] = resp.content  # type: ignore
            else:
                raise SerializeFailed(
                    lang.require("nbp-uniseg", "invalid_segment").format(type="thumbnail", seg=seg.thumbnail)
                )
            return await bot.upload_video(
                method=UploadMethod.Group,
                data=video_data,
                thumbnail=thumbnail_data,
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="video", seg=seg))

    @export
    async def file(self, seg: File, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.path:
            return MessageSegment(
                "mirai:file",
                {
                    "data": Path(seg.path).read_bytes(),
                    "name": Path(seg.path).name if seg.name == seg.__default_name__ else seg.name,
                },
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="file", seg=seg))

    @export
    async def hyper(self, seg: Hyper, bot: Union[Bot, None]) -> "MessageSegment":
        assert seg.raw, lang.require("nbp-uniseg", "invalid_segment").format(type="hyper", seg=seg)
        return MessageSegment.xml(seg.raw) if seg.format == "xml" else MessageSegment.app(seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.reply(int(seg.id))

    @export
    async def reference(self, seg: Reference, bot: Union[Bot, None]) -> "MessageSegment":
        if not seg.children:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg))
        nodes = []
        for node in seg.children:
            if isinstance(node, RefNode):
                if node.context:
                    nodes.append(MessageSegment.ref_node(int(node.id), int(node.context)))
                else:
                    nodes.append(MessageSegment.id_node(int(node.id)))
            else:
                content = self.get_message_type()([])
                if isinstance(node.content, str):
                    content.extend(self.get_message_type()(node.content))
                else:
                    content.extend(await self.export(node.content, bot, True))
                nodes.append(
                    MessageSegment.custom_node(
                        int(node.uid),
                        node.time,
                        node.name,
                        content,
                    )
                )
        return MessageSegment.forward(nodes)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, MiraiBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            _target = self.get_target(target, bot)
        else:
            _target = target

        if msg := message.include("mirai:file"):
            if _target.private:
                method = UploadMethod.Friend
            else:
                method = UploadMethod.Group
            return await bot.upload_file(
                data=msg[0].data["data"], method=method, name=msg[0].data["name"], target=int(_target.id)
            )
        if isinstance(target, Event):
            return await bot.send(target, message)  # type: ignore

        if _target.private:
            return await bot.send_friend_message(target=int(target.id), message=message)
        return await bot.send_group_message(target=int(target.id), message=message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, MiraiBot)
        if isinstance(mid, FileInfo):
            if isinstance(context, Event):
                _target = self.get_target(context, bot)
            else:
                _target = context
            if mid.id:
                await bot.delete_file(target=int(_target.id), id=mid.id)
        else:
            if TYPE_CHECKING:
                assert isinstance(mid, ActiveMessage)
            await bot.recall_message(message=mid)

    def get_reply(self, mid: Any):
        if TYPE_CHECKING:
            assert isinstance(mid, ActiveMessage)
        return Reply(str(mid.message_id))
