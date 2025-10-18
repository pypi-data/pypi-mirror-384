from arclet.alconna import Alconna, Args
from nepattern import Dot
from nonebot import get_adapter
from nonebot.adapters.satori import Adapter, Bot, Message, MessageSegment
from nonebot.adapters.satori.element import parse
from nonebug import App
import pytest

from tests.fake import fake_message_event_satori, fake_satori_bot_params


def test_message_rollback():
    from nonebot_plugin_alconna import Image, UniMessage, select

    text = """\
捏<chronocat:marketface tab-id="237834" face-id="a651cf5813ba41587b22d273682e01ae" key="e08787120cade0a5">
  <img src="http://127.0.0.1:5500/v1/assets/eyJ0eXBlIjoibWF..."/>
</chronocat:marketface>
    """
    msg = Message.from_satori_element(parse(text))

    text1 = '捏<img src="http://127.0.0.1:5500/v1/assets/eyJ0eXBlIjoibWF..." />'

    msg1 = Message.from_satori_element(parse(text1))

    alc = Alconna("捏", Args["img", Dot(select(Image).first, str, "url")])

    res = alc.parse(msg, {"$adapter.name": "Satori"})
    assert res.matched
    assert res.query[str]("img") == "http://127.0.0.1:5500/v1/assets/eyJ0eXBlIjoibWF..."

    res1 = alc.parse(msg1, {"$adapter.name": "Satori"})
    assert res1.matched
    assert res1.query[str]("img") == "http://127.0.0.1:5500/v1/assets/eyJ0eXBlIjoibWF..."

    assert UniMessage.text("123").style("\n", "br").text("456").export_sync(adapter="Satori") == Message(
        [
            MessageSegment.text("123"),
            MessageSegment.br(),
            MessageSegment.text("456"),
        ]
    )


@pytest.mark.asyncio()
async def test_satori(app: App):
    from nonebot_plugin_alconna import Bold, Italic, Underline

    msg = Message("/com<b>mand s<i>ome</i>_arg</b> <u>some_arg</u> <b><i>some_arg</i></b>")

    alc = Alconna("/command", Args["some_arg", Bold]["some_arg1", Underline]["some_arg2", Bold + Italic])

    res = alc.parse(msg, {"$adapter.name": "Satori"})
    assert res.matched
    some_arg: MessageSegment = res["some_arg"]
    assert some_arg.type == "text"
    assert str(some_arg) == "<bold>s<italic>ome</italic>_arg</bold>"
    some_arg1: MessageSegment = res["some_arg1"]
    assert some_arg1.type == "text"
    assert some_arg1.data["styles"] == {(0, 8): ["underline"]}
    some_arg2: MessageSegment = res["some_arg2"]
    assert some_arg2.type == "text"
    assert some_arg2.data["styles"] == {(0, 8): ["bold", "italic"]}

    msg1 = "/command " + Bold("foo bar baz")

    alc1 = Alconna("/command", Args["foo", str]["bar", Bold]["baz", Bold])

    res1 = alc1.parse(msg1)
    assert res1.matched
    assert isinstance(res1.foo, str)
    assert res1["bar"].type == "text"
    assert res1["baz"].data["text"] == "baz"

    msg2 = "/command " + Bold("foo bar baz")

    alc2 = Alconna("/command", Args["foo", str]["bar", Bold]["baz", Underline])
    assert not alc2.parse(msg2).matched


@pytest.mark.asyncio()
async def test_send(app: App):
    from nonebot_plugin_alconna import Image, Text, on_alconna

    test_cmd = on_alconna(Alconna("test", Args["img", Image]))

    @test_cmd.handle()
    async def tt_h(img: Image):
        await test_cmd.send(Text("ok") + img)

    async with app.test_matcher(test_cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, **fake_satori_bot_params())
        msg = "test" + MessageSegment.image(raw=b"123", mime="image/png")
        event = fake_message_event_satori(message=msg, id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message('ok<img src="data:image/png;base64,MTIz" />'))
