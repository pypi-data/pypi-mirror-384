from __future__ import annotations
import typing

from instaui_tdesign.components._icon_param_utils import make_icon_for_bool_or_str
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Message(BaseElement):
    def __init__(
        self,
        content: typing.Optional[TMaybeRef[str]] = None,
        *,
        icon: typing.Union[str, bool, None] = None,
        **kwargs: Unpack[TMessageProps],
    ):
        super().__init__("t-message")
        self.props({"content": content})
        make_icon_for_bool_or_str(self, "icon", icon)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

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

    def on_close_btn_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "close_btn_click",
            handler,
            extends=extends,
        )
        return self

    def on_duration_end(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "duration_end",
            handler,
            extends=extends,
        )
        return self


class TMessageProps(TypedDict, total=False):
    close_btn: TMaybeRef[typing.Union[str, bool]]
    duration: TMaybeRef[float]
    theme: TMaybeRef[
        typing.Literal["info", "success", "warning", "error", "question", "loading"]
    ]
    on_close: EventMixin
    on_close_btn_click: EventMixin
    on_duration_end: EventMixin
