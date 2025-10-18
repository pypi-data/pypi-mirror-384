from arclet.alconna import Alconna, Args
from nonebot import get_adapter
from nonebot.adapters.onebot.v11 import Adapter, Bot, Message
from nonebug import App
import pytest

from tests.fake import fake_group_message_event_v11


@pytest.mark.asyncio()
async def test_unmatch(app: App):
    from nonebot_plugin_alconna import Match, UniMessage, on_alconna

    test_cmd = on_alconna(Alconna("test", Args["target", int]), skip_for_unmatch=False, auto_send_output=True)

    @test_cmd.handle()
    async def tt_h(target: Match[int]):
        await test_cmd.send(UniMessage(["ok\n", str(target.result)]))

    async with app.test_matcher(test_cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_group_message_event_v11(message=Message("tes 1234"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule()

        event = fake_group_message_event_v11(message=Message("test 1234"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message("ok\n1234"))

        event = fake_group_message_event_v11(message=Message("test abcd"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule()
        ctx.should_call_send(event, "参数 'abcd' 不正确, 其应该符合 'int'", bot=bot)
