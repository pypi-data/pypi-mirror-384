from __future__ import annotations
import typing

from instaui_tdesign.components._icon_param_utils import make_icon_for_bool_or_str
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Collapse(BaseElement):
    def __init__(
        self,
        value: typing.Optional[TMaybeRef[typing.List]] = None,
        *,
        expand_icon: typing.Optional[typing.Union[bool, str]] = None,
        **kwargs: Unpack[TCollapseProps],
    ):
        super().__init__("t-collapse")
        try_setup_vmodel(self, value)

        make_icon_for_bool_or_str(self, "expandIcon", expand_icon)

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

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


class CollapsePanel(BaseElement):
    def __init__(
        self,
        header: typing.Optional[TMaybeRef[str]] = None,
        *,
        expand_icon: typing.Optional[typing.Union[bool, str]] = None,
        **kwargs: Unpack[TCollapsePanelProps],
    ):
        super().__init__("t-collapse-panel")
        self.props(
            {
                "header": header,
            }
        )
        make_icon_for_bool_or_str(self, "expandIcon", expand_icon)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TCollapseProps(TypedDict, total=False):
    borderless: TMaybeRef[bool]
    default_expand_all: TMaybeRef[bool]
    disabled: TMaybeRef[bool]
    expand_icon_placement: TMaybeRef[typing.Literal["left", "right"]]
    expand_mutex: TMaybeRef[bool]
    expand_on_row_click: TMaybeRef[bool]
    default_value: TMaybeRef[typing.List]
    on_change: EventMixin


class TCollapsePanelProps(TypedDict, total=False):
    content: TMaybeRef[str]
    destroy_on_collapse: TMaybeRef[bool]
    disabled: TMaybeRef[bool]
    header_right_content: TMaybeRef[str]
    value: TMaybeRef[typing.Union[int, str]]
