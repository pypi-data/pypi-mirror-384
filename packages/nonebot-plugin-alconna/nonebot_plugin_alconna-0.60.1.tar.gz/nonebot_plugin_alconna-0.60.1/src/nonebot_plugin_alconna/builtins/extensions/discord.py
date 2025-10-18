from datetime import datetime, timedelta
from typing import Optional, Union

from arclet.alconna import Alconna, Args, Option, Subcommand
from nepattern import ANY, FLOAT, INTEGER, NUMBER, UnionPattern
from nonebot.adapters import Event
from nonebot.adapters.discord import Bot
from nonebot.adapters.discord.api import (
    AnyCommandOption,
    ApplicationCommandInteractionDataOption,
    ApplicationCommandOptionType,
    ApplicationCommandType,
    AttachmentOption,
    BooleanOption,
    IntegerOption,
    InteractionResponse,
    MentionableOption,
    MessageGet,
    NumberOption,
    OptionChoice,
    SnowflakeType,
    StringOption,
    SubCommandGroupOption,
    SubCommandOption,
)
from nonebot.adapters.discord.api.types import InteractionCallbackType, MessageFlag
from nonebot.adapters.discord.commands.matcher import ApplicationCommandConfig, SlashCommandMatcher, on_slash_command
from nonebot.adapters.discord.commands.storage import _application_command_storage
from nonebot.adapters.discord.event import ApplicationCommandInteractionEvent
from nonebot.adapters.discord.message import parse_message
from nonebot.dependencies import Dependent
from nonebot.internal.matcher.matcher import current_bot, current_event, current_matcher
from nonebot.permission import Permission
from nonebot.rule import Rule
from nonebot.typing import T_Handler, T_PermissionChecker, T_RuleChecker, T_State
from tarina import LRU, lang

from nonebot_plugin_alconna import At, Extension, Image, UniMessage, log
from nonebot_plugin_alconna.extension import cache_msg
from nonebot_plugin_alconna.matcher import _M, AlconnaMatcher


def _translate_args(args: Args) -> list[AnyCommandOption]:
    result = []
    for arg in args:
        if isinstance(arg.value, UnionPattern):
            if all(isinstance(x, str) for x in arg.value.base):
                result.append(
                    StringOption(
                        name=f"{arg.name}",
                        description=f"{arg.notice or arg.name}",
                        required=not arg.optional,
                        choices=[OptionChoice(name=x, value=x) for x in arg.value.base],  # type: ignore  # noqa: E501
                    )
                )
            elif all(isinstance(x, int) for x in arg.value.base):
                result.append(
                    IntegerOption(
                        name=f"{arg.name}",
                        description=f"{arg.notice or arg.name}",
                        required=not arg.optional,
                        choices=[
                            OptionChoice(name=str(x), value=x) for x in arg.value.base  # type: ignore  # noqa: E501
                        ],
                    )
                )
            elif all(isinstance(x, float) for x in arg.value.base):
                result.append(
                    NumberOption(
                        name=f"{arg.name}",
                        description=f"{arg.notice or arg.name}",
                        required=not arg.optional,
                        choices=[
                            OptionChoice(name=str(x), value=x) for x in arg.value.base  # type: ignore  # noqa: E501
                        ],
                    )
                )
            else:
                result.append(
                    StringOption(
                        name=f"{arg.name}",
                        description=f"{arg.notice or arg.name}",
                        required=not arg.optional,
                        choices=[OptionChoice(name=str(x), value=str(x)) for x in arg.value.base],
                    )
                )
            continue
        if arg.value == ANY:
            result.append(
                StringOption(
                    name=f"{arg.name}",
                    description=f"{arg.notice or arg.name}",
                    required=not arg.optional,
                )
            )
        elif arg.value == INTEGER:
            result.append(
                IntegerOption(
                    name=f"{arg.name}",
                    description=f"{arg.notice or arg.name}",
                    required=not arg.optional,
                )
            )
        elif arg.value in (FLOAT, NUMBER):
            result.append(
                NumberOption(
                    name=f"{arg.name}",
                    description=f"{arg.notice or arg.name}",
                    required=not arg.optional,
                )
            )
        elif arg.value.origin is str:
            result.append(
                StringOption(
                    name=f"{arg.name}",
                    description=f"{arg.notice or arg.name}",
                    required=not arg.optional,
                )
            )
        elif arg.value.origin is bool:
            result.append(
                BooleanOption(
                    name=f"{arg.name}",
                    description=f"{arg.notice or arg.name}",
                    required=not arg.optional,
                )
            )
        elif arg.value is Image:
            result.append(
                AttachmentOption(
                    name=f"{arg.name}",
                    description=f"{arg.notice or arg.name}",
                    required=not arg.optional,
                )
            )
        # elif arg.value == MentionUser:
        #     result.append(
        #         UserOption(
        #             name=f"{arg.name}",
        #             description=f"{arg.notice or arg.name}",
        #             required=not arg.optional,
        #         )
        #     )
        # elif arg.value == MentionChannel:
        #     result.append(
        #         ChannelOption(
        #             name=f"{arg.name}",
        #             description=f"{arg.notice or arg.name}",
        #             required=not arg.optional,
        #         )
        #     )
        # elif arg.value == MentionRole:
        #     result.append(
        #         RoleOption(
        #             name=f"{arg.name}",
        #             description=f"{arg.notice or arg.name}",
        #             required=not arg.optional,
        #         )
        #     )
        elif arg.value.origin is At:
            result.append(
                MentionableOption(
                    name=f"{arg.name}",
                    description=f"{arg.notice or arg.name}",
                    required=not arg.optional,
                )
            )
        else:
            result.append(
                StringOption(
                    name=f"{arg.name}",
                    description=f"{arg.notice or arg.name}",
                    required=not arg.optional,
                )
            )
    return result


def _translate_options(opt: Union[Option, Subcommand]) -> Union[SubCommandGroupOption, SubCommandOption]:
    if isinstance(opt, Option):
        return SubCommandOption(
            name=f"{opt.name}",
            description=f"{opt.help_text}",
            options=_translate_args(opt.args),  # type: ignore
        )
    if not opt.args.empty and opt.options:
        log(
            "WARNING",
            lang.require("nbp-alc", "log.discord.ambiguous_subcommand").format(name=opt.name),
        )
    if not opt.args.empty:
        return SubCommandOption(
            name=f"{opt.name}", description=f"{opt.help_text}", options=_translate_args(opt.args)  # type: ignore
        )
    return SubCommandGroupOption(
        name=f"{opt.name}",
        description=f"{opt.help_text}",
        options=[_translate_options(sub) for sub in opt.options],  # type: ignore
    )


def translate(
    alc: Alconna,
    internal_id: Optional[str] = None,
    rule: Union[Rule, T_RuleChecker, None] = None,
    permission: Union[Permission, T_PermissionChecker, None] = None,
    *,
    name_localizations: Optional[dict[str, str]] = None,
    description_localizations: Optional[dict[str, str]] = None,
    default_member_permissions: Optional[str] = None,
    dm_permission: Optional[bool] = None,
    default_permission: Optional[bool] = None,
    nsfw: Optional[bool] = None,
    handlers: Optional[list[Union[T_Handler, Dependent]]] = None,
    temp: bool = False,
    expire_time: Union[datetime, timedelta, None] = None,
    priority: int = 1,
    block: bool = True,
    state: Optional[T_State] = None,
    _depth: int = 0,
) -> type[SlashCommandMatcher]:
    if alc.prefixes != ["/"] or (not alc.prefixes and isinstance(alc.command, str) and not alc.command.startswith("/")):
        raise ValueError(lang.require("nbp-alc", "error.discord_prefix"))
    allow_opt = [
        opt
        for opt in alc.options
        if opt.name not in set().union(*alc.namespace_config.builtin_option_name.values())  # type: ignore
    ]
    if not alc.args.empty and allow_opt:
        log(
            "WARNING",
            lang.require("nbp-alc", "log.discord.ambiguous_command").format(cmd=alc.path),
        )
    if not (options := _translate_args(alc.args)):
        options = [_translate_options(opt) for opt in allow_opt]
    buffer = {
        "name": f"{alc.command}",
        "description": f"{alc.meta.description}",
        "options": options,
        **locals(),
    }
    buffer["_depth"] += 1
    buffer.pop("alc")
    return on_slash_command(**buffer)


class DiscordSlashExtension(Extension):
    """
    用于将 Alconna 的命令自动转换为 Discord 的 Slash Command，并将 Slash Command 的交互事件转换为消息交给 Alconna 处理。

    Example:
        >>> from nonebot_plugin_alconna import on_alconna
        >>> from nonebot_plugin_alconna.builtins.extensions.discord import DiscordSlashExtension
        >>>
        >>> matcher = on_alconna("...", extensions=[DiscordSlashExtension(...)])
        >>>
        >>> @matcher.handle()
        >>> async def handle(ext: DiscordSlashExtension):
        >>>     await ext.send_response("Hello, world!")
    """

    application_command: ApplicationCommandConfig

    @property
    def priority(self) -> int:
        return 10

    @property
    def id(self) -> str:
        return "builtins.extensions.discord:DiscordSlashExtension"

    def __init__(
        self,
        internal_id: Optional[str] = None,
        name_localizations: Optional[dict[str, str]] = None,
        description: Optional[str] = None,
        description_localizations: Optional[dict[str, str]] = None,
        default_member_permissions: Optional[str] = None,
        dm_permission: Optional[bool] = None,
        default_permission: Optional[bool] = None,
        nsfw: Optional[bool] = None,
    ):
        self.internal_id = internal_id
        self.name_localizations = name_localizations
        self.description = description
        self.description_localizations = description_localizations
        self.default_member_permissions = default_member_permissions
        self.dm_permission = dm_permission
        self.default_permission = default_permission
        self.nsfw = nsfw
        super().__init__()
        self.using = False
        self.cache: "LRU[int, UniMessage]" = LRU(20)  # noqa: UP037

    def post_init(self, alc: Alconna) -> None:
        if "/" not in alc.prefixes or (
            not alc.prefixes and isinstance(alc.command, str) and not alc.command.startswith("/")
        ):
            return
        self.using = True
        allow_opt = [
            opt
            for opt in alc.options
            if opt.name not in set().union(*alc.namespace_config.builtin_option_name.values())  # type: ignore
        ]
        if not alc.args.empty and allow_opt:
            log(
                "WARNING",
                lang.require("nbp-alc", "log.discord.ambiguous_command").format(cmd=alc.path),
            )
        if not (options := _translate_args(alc.args)):
            options = [_translate_options(opt) for opt in allow_opt]
        config = ApplicationCommandConfig(
            type=ApplicationCommandType.CHAT_INPUT,
            name=alc.command,
            name_localizations=self.name_localizations,
            description=self.description or alc.meta.description,
            description_localizations=self.description_localizations,
            options=options,  # type: ignore
            default_member_permissions=self.default_member_permissions,
            dm_permission=self.dm_permission,
            default_permission=self.default_permission,
            nsfw=self.nsfw,
        )
        _application_command_storage[self.internal_id or config.name] = config
        self.application_command = config

    def validate(self, bot, event: Event) -> bool:
        if not self.using:
            return False
        if not isinstance(event, ApplicationCommandInteractionEvent):
            return False
        if event.data.name != self.application_command.name or event.data.type != self.application_command.type:
            return False
        if not event.data.guild_id and self.application_command.guild_ids is None:
            return True
        return bool(
            event.data.guild_id
            and self.application_command.guild_ids
            and event.data.guild_id in self.application_command.guild_ids
        )

    async def message_provider(self, event: Event, state: T_State, bot, use_origin: bool = False):
        if not isinstance(event, ApplicationCommandInteractionEvent):
            return None
        if cache_msg and event.id in self.cache:
            return self.cache[event.id]
        data = event.data
        cmd = f"/{data.name}"

        def _handle_options(options: list[ApplicationCommandInteractionDataOption]):
            for opt in options:
                if opt.type in (
                    ApplicationCommandOptionType.SUB_COMMAND,
                    ApplicationCommandOptionType.SUB_COMMAND_GROUP,
                ):
                    yield f"{opt.name}"
                    if opt.options:
                        yield from _handle_options(opt.options)
                else:
                    yield f"{opt.value}"

        if data.options:
            cmd += " "
            cmd += " ".join(_handle_options(data.options))

        res = UniMessage(cmd.rstrip())
        self.cache[event.id] = res
        return res

    @classmethod
    async def send_deferred_response(cls) -> None:
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        await bot.create_interaction_response(
            interaction_id=event.id,
            interaction_token=event.token,
            response=InteractionResponse(type=InteractionCallbackType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE),
        )

    @classmethod
    async def send_response(cls, message: _M, fallback: bool = False):
        matcher: AlconnaMatcher = current_matcher.get()  # type: ignore
        return await matcher.send(message, fallback)

    @classmethod
    async def get_response(cls) -> MessageGet:
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        return await bot.get_origin_interaction_response(
            application_id=bot.application_id,
            interaction_token=event.token,
        )

    async def edit_response(
        self,
        message: _M,
        fallback: bool = False,
    ) -> None:
        matcher: AlconnaMatcher = current_matcher.get()  # type: ignore
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        _message = await matcher.executor.send_wrapper(bot, event, matcher.convert(message))
        if isinstance(_message, UniMessage):
            message_data = parse_message(await _message.export(bot, fallback))  # type: ignore
        else:
            message_data = parse_message(_message)  # type: ignore
        await bot.edit_origin_interaction_response(
            application_id=bot.application_id,
            interaction_token=event.token,
            **message_data,
        )

    @classmethod
    async def delete_response(cls) -> None:
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        await bot.delete_origin_interaction_response(
            application_id=bot.application_id,
            interaction_token=event.token,
        )

    async def send_followup_msg(
        self,
        message: _M,
        fallback: bool = False,
        flags: Optional[MessageFlag] = None,
    ) -> MessageGet:
        matcher: AlconnaMatcher = current_matcher.get()  # type: ignore
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        _message = await matcher.executor.send_wrapper(bot, event, matcher.convert(message))
        if isinstance(_message, UniMessage):
            message_data = parse_message(await _message.export(bot, fallback))  # type: ignore
        else:
            message_data = parse_message(_message)  # type: ignore
        if flags:
            message_data["flags"] = int(flags)
        return await bot.create_followup_message(
            application_id=bot.application_id,
            interaction_token=event.token,
            **message_data,
        )

    @classmethod
    async def get_followup_msg(cls, message_id: SnowflakeType):
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        return await bot.get_followup_message(
            application_id=bot.application_id,
            interaction_token=event.token,
            message_id=message_id,
        )

    async def edit_followup_msg(
        self,
        message_id: SnowflakeType,
        message: _M,
        fallback: bool = False,
    ) -> MessageGet:
        matcher: AlconnaMatcher = current_matcher.get()  # type: ignore
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        _message = await matcher.executor.send_wrapper(bot, event, matcher.convert(message))
        if isinstance(_message, UniMessage):
            message_data = parse_message(await _message.export(bot, fallback))  # type: ignore
        else:
            message_data = parse_message(_message)  # type: ignore
        return await bot.edit_followup_message(
            application_id=bot.application_id,
            interaction_token=event.token,
            message_id=message_id,
            **message_data,
        )

    @classmethod
    async def delete_followup_msg(cls, message_id: SnowflakeType) -> None:
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        await bot.delete_followup_message(
            application_id=bot.application_id,
            interaction_token=event.token,
            message_id=message_id,
        )


__extension__ = DiscordSlashExtension
