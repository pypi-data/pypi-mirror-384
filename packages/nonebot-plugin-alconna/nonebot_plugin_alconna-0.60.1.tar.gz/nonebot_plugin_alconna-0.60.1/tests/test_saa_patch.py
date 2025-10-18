from arclet.alconna import Alconna, Args
from nonebot import get_adapter, require
from nonebot.adapters.satori import Adapter, Bot, MessageSegment
from nonebug import App
import pytest

from tests.fake import fake_message_event_satori, fake_satori_bot_params


@pytest.mark.asyncio()
async def test_patch(app: App):
    require("nonebot_plugin_saa")
    from nonebot_plugin_saa import Mention, MessageFactory, Text

    from nonebot_plugin_alconna import At, on_alconna, patch_saa

    test_cmd = on_alconna(Alconna("test", Args["target", At]))

    @test_cmd.handle()
    async def tt_h(target: At):
        await MessageFactory(
            [
                Text("ok\n"),
                Mention(target.target),
            ]
        ).send()

    dispose = patch_saa()

    async with app.test_matcher(test_cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, **fake_satori_bot_params())
        msg = "test" + MessageSegment.at("234")
        event = fake_message_event_satori(message=msg, id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, MessageSegment.text("ok\n") + MessageSegment.at("234"))  # type: ignore

    dispose()
