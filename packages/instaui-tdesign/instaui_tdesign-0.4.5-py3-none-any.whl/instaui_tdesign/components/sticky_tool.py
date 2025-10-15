from __future__ import annotations
import typing

from instaui_tdesign.components._icon_param_utils import make_icon_for_str
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack

from ._utils import handle_props, handle_event_from_props


class StickyTool(BaseElement):
    def __init__(
        self,
        list: typing.Optional[typing.List[TStickyItemProps]] = None,
        **kwargs: Unpack[TStickyToolProps],
    ):
        super().__init__("t-sticky-tool")
        self.props({"list": list})

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

    def on_hover(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "hover",
            handler,
            extends=extends,
        )
        return self


class StickyItem(BaseElement):
    def __init__(
        self,
        label: typing.Optional[str] = None,
        *,
        icon: typing.Optional[str] = None,
        **kwargs: Unpack[TStickyItemProps],
    ):
        super().__init__("t-sticky-item")
        self.props({"label": label})
        make_icon_for_str(self, icon)

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TStickyToolProps(TypedDict, total=False):
    offset: typing.List
    placement: typing.Literal[
        "right-top",
        "right-center",
        "right-bottom",
        "left-top",
        "left-center",
        "left-bottom",
    ]
    popup_props: typing.Dict
    shape: typing.Literal["square", "round"]
    type: typing.Literal["normal", "compact"]
    width: typing.Union[float, str]
    on_click: EventMixin
    on_hover: EventMixin


class TStickyItemProps(TypedDict, total=False):
    popup: str
    popup_props: typing.Dict
    trigger: typing.Literal["hover", "click"]
