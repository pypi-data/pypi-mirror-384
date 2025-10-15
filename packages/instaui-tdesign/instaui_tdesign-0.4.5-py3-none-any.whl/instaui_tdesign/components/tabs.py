from __future__ import annotations
import typing
from instaui import custom
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack

from ._utils import handle_props, handle_event_from_props, try_setup_vmodel


class Tabs(custom.element):
    def __init__(
        self,
        value: typing.Optional[str] = None,
        **kwargs: Unpack[TTabsProps],
    ):
        super().__init__("t-tabs")
        custom.configure_slot_without_slot_prop(self, slot_names=["default"])
        try_setup_vmodel(self, value)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_add(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "add",
            handler,
            extends=extends,
        )
        return self

    def on_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "change",
            handler,
            extends=extends,
        )
        return self

    def on_drag_sort(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "drag_sort",
            handler,
            extends=extends,
        )
        return self

    def on_remove(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "remove",
            handler,
            extends=extends,
        )
        return self


class TabPanel(custom.element):
    def __init__(
        self,
        **kwargs: Unpack[TTabPanelProps],
    ):
        super().__init__("t-tab-panel")
        custom.configure_slot_without_slot_prop(self, slot_names=["default"])
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_remove(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "remove",
            handler,
            extends=extends,
        )
        return self


class TTabsProps(TypedDict, total=False):
    action: typing.Literal["TNode"]
    addable: bool
    disabled: bool
    drag_sort: bool
    list: typing.List[TTabPanelProps]
    placement: typing.Literal["left", "top", "bottom", "right"]
    scroll_position: typing.Literal["auto", "start", "center", "end"]
    size: typing.Literal["medium", "large"]
    theme: typing.Literal["normal", "card"]
    default_value: str
    on_add: EventMixin
    on_change: EventMixin
    on_drag_sort: EventMixin
    on_remove: EventMixin


class TTabPanelProps(TypedDict, total=False):
    default: str
    destroy_on_hide: bool
    disabled: bool
    draggable: bool
    label: str
    lazy: bool
    panel: str
    removable: bool
    value: str
    on_remove: EventMixin
