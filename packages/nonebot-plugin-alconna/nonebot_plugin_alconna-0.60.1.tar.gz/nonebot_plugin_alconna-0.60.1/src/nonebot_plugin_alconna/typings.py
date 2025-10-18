from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, Callable, Generic, Literal, TypeVar, Union
from typing_extensions import ParamSpec, TypeAlias

from arclet.alconna import Arparma
from nepattern import URL, BasePattern, MatchFailed, MatchMode, UnionPattern
from nonebot.internal.adapter import Bot, Event, Message, MessageSegment
from nonebot.typing import T_State
from tarina import lang

from .argv import text
from .uniseg import At, Image, Segment, Text, UniMessage
from .uniseg.segment import env

T = TypeVar("T")
TS = TypeVar("TS", bound=Segment)
TS1 = TypeVar("TS1", bound=Segment)
TMS = TypeVar("TMS", bound=MessageSegment)
TCallable = TypeVar("TCallable", bound=Callable[..., Any])
P = ParamSpec("P")


env[Text] = text

ImageOrUrl = (
    UnionPattern[Union[str, Image]](
        [
            BasePattern(
                mode=MatchMode.TYPE_CONVERT,
                origin=str,
                converter=lambda _, x: x.url,  # type: ignore
                alias="img",
                accepts=Image,
            ),
            URL,  # type: ignore
        ]
    )
    @ "img_url"
)
"""
内置类型, 允许传入图片元素(Image)或者链接(URL)，返回链接
"""

_AtID = BasePattern(mode=MatchMode.TYPE_CONVERT, origin=str, alias="At", accepts=At, converter=lambda _, x: x.target)
_AtText = BasePattern(
    r"@(.+)",
    mode=MatchMode.REGEX_CONVERT,
    origin=str,
    alias="@xxx",
    converter=lambda _, x: x[1],
)

AtID = UnionPattern[Union[str, At]]([_AtID, _AtText]) @ "notice_id"  # type: ignore
"""
内置类型，允许传入@元素(At)或者'@xxxx'式样的字符串, 返回字符串形式的 id
"""


class SegmentPattern(BasePattern[TMS, TS, Literal[MatchMode.TYPE_CONVERT]], Generic[TS, TMS, P]):
    def __init__(
        self,
        name: str,
        origin: type[TMS],
        accept: type[TS],
        call: Callable[P, TMS],
        additional: Callable[[TS], bool] | None = None,
        handle: Callable[[TS], TMS] | None = None,
    ):
        super().__init__(
            mode=MatchMode.TYPE_CONVERT,
            origin=origin,
            alias=name,
            accepts=accept,
        )
        self.target = accept
        self.pattern = name
        self.call = call
        self.validator: Callable[[TS], bool] = (
            lambda s: isinstance(s.origin, origin) and s.origin.type == name and (additional or (lambda _: True))(s)
        )
        self.handle = handle or (lambda s: s.origin)

    def match(self, input_: TS) -> TMS:
        if not isinstance(input_, self.target):
            raise MatchFailed(lang.require("nepattern", "type_error").format(target=type(input_)))
        if self.validator(input_):
            return self.handle(input_)  # type: ignore
        raise MatchFailed(lang.require("nepattern", "content_error").format(target=input_))

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TMS:
        return self.call(*args, **kwargs)  # type: ignore


class TextSegmentPattern(BasePattern[TMS, Union[str, Text], Literal[MatchMode.TYPE_CONVERT]], Generic[TMS, P]):
    def __init__(
        self,
        name: str,
        origin: type[TMS],
        call: Callable[P, TMS],
        converter: Callable[[Any, Text], TMS | None],
    ):
        super().__init__(
            mode=MatchMode.TYPE_CONVERT,
            origin=origin,
            alias=name,
            converter=converter,
            accepts=Text,
            previous=text,
        )
        self.pattern = name
        self.call = call

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TMS:
        return self.call(*args, **kwargs)  # type: ignore

    def __calc_repr__(self):
        return self.pattern


class Style(BasePattern[Text, Union[str, Text], Literal[MatchMode.VALUE_OPERATE]]):
    def __init__(
        self,
        expect: str,
    ):
        self.expected = [expect]
        super().__init__(
            mode=MatchMode.VALUE_OPERATE,
            origin=Text,
            previous=text,
            converter=lambda _, x: x if x.styles and all(set(style).issuperset(_.expected) for style in x.styles.values()) else None,  # type: ignore  # noqa: E501
            alias=expect.capitalize(),
        )
        self.pattern = expect

    def __calc_repr__(self):
        return self.alias

    def __call__(self, text: str):
        return Text(text).mark(0, len(text), *self.expected)

    def __add__(self, other: Style) -> Style:
        obj = Style(self.pattern)
        obj.expected = self.expected.copy()
        if not isinstance(other, Style):
            raise TypeError(other)
        if other.pattern not in self.expected:
            obj.expected.append(other.pattern)
        obj.alias = "+".join(obj.expected)
        obj.alias = obj.alias.capitalize()
        obj.refresh()
        return obj


Link = Style("link")
Bold = Style("bold")
Italic = Style("italic")
Underline = Style("underline")
Strikethrough = Style("strikethrough")
Spoiler = Style("spoiler")
Code = Style("code")

MReturn: TypeAlias = Union[
    Union[str, Segment, UniMessage, Message, MessageSegment],
    Awaitable[Union[str, Segment, UniMessage, Message, MessageSegment]],
]
MIDDLEWARE: TypeAlias = Callable[[Event, Bot, T_State, Any], Any]
CHECK: TypeAlias = Callable[[Event, Bot, T_State, Arparma], Awaitable[bool]]
