from arclet.alconna import Alconna, Args, CommandMeta, Option, Subcommand
from nonebot import get_adapter
from nonebot.adapters.discord import Adapter, Bot
from nonebot.adapters.discord.api.model import (
    ApplicationCommandData,
    ApplicationCommandInteractionDataOption,
    Snowflake,
)
from nonebot.adapters.discord.api.types import ApplicationCommandOptionType, ApplicationCommandType
from nonebug import App
import pytest

from tests.fake import fake_discord_interaction_event


@pytest.mark.asyncio()
async def test_dc_ext(app: App):
    from nonebot_plugin_alconna import Match, on_alconna
    from nonebot_plugin_alconna.builtins.extensions.discord import DiscordSlashExtension

    alc = Alconna(
        ["/"],
        "permission",
        Subcommand("add", Args["plugin", str]["priority?", int]),
        Option("remove", Args["plugin", str]["time?", int]),
        meta=CommandMeta(description="权限管理"),
    )
    matcher = on_alconna(alc, extensions=[DiscordSlashExtension()])

    @matcher.assign("add")
    async def add(plugin: Match[str], priority: Match[int]):
        await matcher.finish(f"added {plugin.result} with {priority.result if priority.available else 0}")

    @matcher.assign("remove")
    async def remove(plugin: Match[str], time: Match[int]):
        await matcher.finish(f"removed {plugin.result} with {time.result if time.available else -1}")

    assert alc.parse("/permission add test 99").matched
    async with app.test_matcher(matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, bot_info=None, self_id="12345", auto_connect=False)
        event = fake_discord_interaction_event(
            data=ApplicationCommandData(
                id=Snowflake(1234567890),
                name="permission",
                type=ApplicationCommandType.CHAT_INPUT,
                options=[
                    ApplicationCommandInteractionDataOption(
                        name="add",
                        type=ApplicationCommandOptionType.SUB_COMMAND,
                        options=[
                            ApplicationCommandInteractionDataOption(
                                name="plugin", type=ApplicationCommandOptionType.STRING, value="test"
                            ),
                            ApplicationCommandInteractionDataOption(
                                name="priority", type=ApplicationCommandOptionType.INTEGER, value=99
                            ),
                        ],
                    )
                ],
            )
        )
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "added test with 99")
        ctx.should_finished(matcher)

    assert alc.parse("/permission remove test 123").matched
    async with app.test_matcher(matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, bot_info=None, self_id="12345", auto_connect=False)
        event = fake_discord_interaction_event(
            data=ApplicationCommandData(
                id=Snowflake(1234567890),
                name="permission",
                type=ApplicationCommandType.CHAT_INPUT,
                options=[
                    ApplicationCommandInteractionDataOption(
                        name="remove",
                        type=ApplicationCommandOptionType.SUB_COMMAND,
                        options=[
                            ApplicationCommandInteractionDataOption(
                                name="plugin", type=ApplicationCommandOptionType.STRING, value="test"
                            ),
                            ApplicationCommandInteractionDataOption(
                                name="time", type=ApplicationCommandOptionType.INTEGER, value=123
                            ),
                        ],
                    )
                ],
            )
        )
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "removed test with 123")
        ctx.should_finished(matcher)
