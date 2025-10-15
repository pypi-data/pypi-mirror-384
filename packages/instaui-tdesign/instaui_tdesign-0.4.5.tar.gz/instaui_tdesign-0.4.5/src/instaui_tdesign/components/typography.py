from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class TypographyText(BaseElement):
    def __init__(
        self,
        content: typing.Optional[TMaybeRef[str]] = None,
        **kwargs: Unpack[TTextProps],
    ):
        super().__init__("t-typography-text")
        self.props({"content": content})

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TypographyTitle(BaseElement):
    def __init__(
        self,
        content: typing.Optional[str] = None,
        **kwargs: Unpack[TTitleProps],
    ):
        super().__init__("t-typography-title")
        self.props({"content": content})

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TypographyParagraph(BaseElement):
    def __init__(
        self,
        content: typing.Optional[str] = None,
        **kwargs: Unpack[TParagraphProps],
    ):
        super().__init__("t-typography-paragraph")
        self.props({"content": content})

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TTextProps(TypedDict, total=False):
    code: bool
    copyable: typing.Union[bool, typing.Dict]
    delete: bool
    disabled: bool
    ellipsis: typing.Union[bool, typing.Dict]
    italic: bool
    keyboard: bool
    mark: typing.Union[bool, str]
    strong: bool
    theme: typing.Literal["primary", "secondary", "success", "warning", "error"]
    underline: bool


class TTitleProps(TypedDict, total=False):
    ellipsis: typing.Union[bool, typing.Dict]
    level: typing.Literal["h1", "h2", "h3", "h4", "h5", "h6"]


class TParagraphProps(TypedDict, total=False):
    ellipsis: typing.Union[bool, typing.Dict]
