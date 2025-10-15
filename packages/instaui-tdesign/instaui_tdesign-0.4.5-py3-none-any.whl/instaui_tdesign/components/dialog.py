from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Dialog(BaseElement):
    def __init__(
        self,
        visible: TMaybeRef[bool],
        *,
        header: typing.Optional[TMaybeRef[str]] = None,
        body: typing.Optional[TMaybeRef[str]] = None,
        theme: typing.Optional[
            TMaybeRef[typing.Literal["default", "info", "warning", "danger", "success"]]
        ] = None,
        **kwargs: Unpack[TDialogProps],
    ):
        super().__init__("t-dialog")

        try_setup_vmodel(self, visible, prop_name="visible")
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_before_close(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "before_close",
            handler,
            extends=extends,
        )
        return self

    def on_before_open(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "before_open",
            handler,
            extends=extends,
        )
        return self

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

    def on_closed(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "closed",
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

    def on_esc_keydown(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "esc_keydown",
            handler,
            extends=extends,
        )
        return self

    def on_opened(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "opened",
            handler,
            extends=extends,
        )
        return self

    def on_overlay_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "overlay_click",
            handler,
            extends=extends,
        )
        return self


class TDialogCardProps(TypedDict, total=False):
    body: TMaybeRef[typing.Literal["TNode"]]
    cancel_btn: TMaybeRef[typing.Literal["ButtonProps"]]
    close_btn: TMaybeRef[typing.Literal["ButtonProps"]]
    confirm_btn: TMaybeRef[typing.Literal["ButtonProps"]]
    confirm_loading: TMaybeRef[bool]
    footer: TMaybeRef[typing.Union[TMaybeRef[bool], TMaybeRef[str]]]
    header: TMaybeRef[typing.Literal["boolean"]]
    theme: TMaybeRef[typing.Literal["default", "info", "warning", "danger", "success"]]
    on_cancel: EventMixin
    on_close_btn_click: EventMixin
    on_confirm: EventMixin


class TDialogProps(TypedDict, total=False):
    attach: TMaybeRef[str]
    cancel_btn: TMaybeRef[typing.Literal["ButtonProps"]]
    close_btn: TMaybeRef[typing.Literal["boolean"]]
    close_on_esc_keydown: TMaybeRef[bool]
    close_on_overlay_click: TMaybeRef[bool]
    confirm_btn: TMaybeRef[typing.Literal["ButtonProps"]]
    confirm_loading: TMaybeRef[bool]
    confirm_on_enter: TMaybeRef[bool]
    destroy_on_close: TMaybeRef[bool]
    dialog_class_name: TMaybeRef[str]
    dialog_style: TMaybeRef[typing.Dict]
    draggable: TMaybeRef[bool]
    footer: TMaybeRef[typing.Union[bool, str]]
    lazy: TMaybeRef[bool]
    mode: TMaybeRef[typing.Literal["modal", "modeless", "normal", "full-screen"]]
    placement: TMaybeRef[typing.Literal["top", "center"]]
    prevent_scroll_through: TMaybeRef[bool]
    show_in_attached_element: TMaybeRef[bool]
    show_overlay: TMaybeRef[bool]
    top: TMaybeRef[typing.Union[float, str]]
    width: TMaybeRef[typing.Union[float, str]]
    z_index: TMaybeRef[float]
    on_before_close: EventMixin
    on_before_open: EventMixin
    on_cancel: EventMixin
    on_close: EventMixin
    on_close_btn_click: EventMixin
    on_closed: EventMixin
    on_confirm: EventMixin
    on_esc_keydown: EventMixin
    on_opened: EventMixin
    on_overlay_click: EventMixin
