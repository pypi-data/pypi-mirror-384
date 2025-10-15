from __future__ import annotations
import typing

from instaui_tdesign.components._icon_param_utils import make_icon_for_str
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Tag(BaseElement):
    def __init__(
        self,
        content: typing.Optional[str] = None,
        *,
        icon: typing.Optional[str] = None,
        **kwargs: Unpack[TTagProps],
    ):
        super().__init__("t-tag")
        self.props({"content": content})

        make_icon_for_str(self, icon)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "click",
            handler,
            extends=extends,
        )
        return self

    def on_close(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "close",
            handler,
            extends=extends,
        )
        return self


class TTagProps(TypedDict, total=False):
    closable: TMaybeRef[bool]
    color: TMaybeRef[str]
    disabled: TMaybeRef[bool]
    max_width: TMaybeRef[typing.Union[float, str]]
    shape: TMaybeRef[typing.Literal["square", "round", "mark"]]
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    theme: TMaybeRef[
        typing.Literal["default", "primary", "warning", "danger", "success"]
    ]
    title: TMaybeRef[str]
    variant: TMaybeRef[typing.Literal["dark", "light", "outline", "light-outline"]]
    on_click: EventMixin
    on_close: EventMixin


class TCheckTagProps(TypedDict, total=False):
    checked: TMaybeRef[bool]
    default_checked: TMaybeRef[bool]
    checked_props: TMaybeRef[typing.Dict]
    content: TMaybeRef[typing.Literal["number"]]
    default: TMaybeRef[typing.Literal["TNode"]]
    disabled: TMaybeRef[bool]
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    unchecked_props: TMaybeRef[typing.Dict]
    value: TMaybeRef[typing.Union[TMaybeRef[float], TMaybeRef[str]]]
    on_change: EventMixin
    on_click: EventMixin


class TCheckTagGroupProps(TypedDict, total=False):
    checked_props: TMaybeRef[typing.Dict]
    multiple: TMaybeRef[bool]
    options: TMaybeRef[typing.List]
    unchecked_props: TMaybeRef[typing.Dict]
    value: TMaybeRef[typing.List]
    default_value: TMaybeRef[typing.List]
    on_change: EventMixin
