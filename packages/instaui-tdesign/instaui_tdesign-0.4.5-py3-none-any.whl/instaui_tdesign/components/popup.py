from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Popup(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TPopupProps],
    ):
        super().__init__("t-popup")
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

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

    def on_scroll(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "scroll",
            handler,
            extends=extends,
        )
        return self

    def on_scroll_to_bottom(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "scroll_to_bottom",
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


class TPopupProps(TypedDict, total=False):
    content: TMaybeRef[str]
    attach: TMaybeRef[str]
    delay: TMaybeRef[typing.Union[float, typing.List]]
    destroy_on_close: TMaybeRef[bool]
    disabled: TMaybeRef[bool]
    hide_empty_popup: TMaybeRef[bool]
    overlay_class_name: TMaybeRef[typing.Union[str, typing.Dict, typing.List]]
    overlay_inner_class_name: TMaybeRef[typing.Union[str, typing.Dict, typing.List]]
    overlay_inner_style: TMaybeRef[typing.Union[str, typing.Dict, typing.List]]
    overlay_style: TMaybeRef[typing.Union[str, typing.Dict, typing.List]]
    placement: TMaybeRef[str]
    popper_options: TMaybeRef[typing.Dict]
    show_arrow: TMaybeRef[bool]
    trigger: TMaybeRef[
        typing.Literal["hover", "click", "focus", "mousedown", "context-menu"]
    ]
    trigger_element: TMaybeRef[str]
    visible: TMaybeRef[bool]
    z_index: TMaybeRef[float]
    on_overlay_click: EventMixin
    on_scroll: EventMixin
    on_scroll_to_bottom: EventMixin
    on_visible_change: EventMixin


TPopupPlacementValue = typing.Literal[
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
