from __future__ import annotations
import typing

from instaui_tdesign.components._icon_param_utils import make_icon_for_str
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Popconfirm(BaseElement):
    def __init__(
        self,
        content: typing.Optional[TMaybeRef[str]] = None,
        *,
        theme: typing.Optional[
            TMaybeRef[typing.Literal["default", "warning", "danger"]]
        ] = None,
        icon: typing.Union[str, None] = None,
        **kwargs: Unpack[TPopconfirmProps],
    ):
        super().__init__("t-popconfirm")
        self.props({"content": content})
        make_icon_for_str(self, icon)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_cancel(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "cancel",
            handler,
            extends=extends,
        )
        return self

    def on_confirm(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "confirm",
            handler,
            extends=extends,
        )
        return self

    def on_visible_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "visible_change",
            handler,
            extends=extends,
        )
        return self


class TPopconfirmProps(TypedDict, total=False):
    cancel_btn: TMaybeRef[typing.Union[str, typing.Dict]]
    confirm_btn: TMaybeRef[typing.Union[str, typing.Dict]]
    destroy_on_close: TMaybeRef[bool]
    placement: TMaybeRef[
        typing.Literal[
            "top",
            "left",
            "right",
            "bottom",
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
            "left-top",
            "left-bottom",
            "right-top",
            "right-bottom",
        ]
    ]
    popup_props: TMaybeRef[typing.Dict]
    show_arrow: TMaybeRef[bool]
    trigger_element: TMaybeRef[str]
    visible: TMaybeRef[bool]
    default_visible: TMaybeRef[bool]
    on_cancel: EventMixin
    on_confirm: EventMixin
    on_visible_change: EventMixin
