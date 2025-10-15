from __future__ import annotations
import typing

from instaui_tdesign.components._icon_param_utils import (
    make_prefix_icon,
    make_suffix_icon,
)
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class TreeSelect(BaseElement):
    def __init__(
        self,
        value: typing.Optional[TMaybeRef[typing.Union[str, int, typing.List]]] = None,
        *,
        model_value: typing.Optional[
            TMaybeRef[typing.Union[str, int, typing.List]]
        ] = None,
        prefix_icon: typing.Optional[str] = None,
        suffix_icon: typing.Optional[str] = None,
        **kwargs: Unpack[TTreeSelectProps],
    ):
        super().__init__("t-tree-select ")

        try_setup_vmodel(self, value)
        make_prefix_icon(self, prefix_icon)
        make_suffix_icon(self, suffix_icon)
        self.props(handle_props(kwargs, model_value=model_value))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_blur(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "blur",
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

    def on_clear(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "clear",
            handler,
            extends=extends,
        )
        return self

    def on_enter(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "enter",
            handler,
            extends=extends,
        )
        return self

    def on_focus(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "focus",
            handler,
            extends=extends,
        )
        return self

    def on_input_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "input_change",
            handler,
            extends=extends,
        )
        return self

    def on_popup_visible_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "popup_visible_change",
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

    def on_search(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "search",
            handler,
            extends=extends,
        )
        return self


class TTreeSelectProps(TypedDict, total=False):
    auto_width: TMaybeRef[bool]
    autofocus: TMaybeRef[bool]
    borderless: TMaybeRef[bool]
    clearable: TMaybeRef[bool]
    collapsed_items: TMaybeRef[str]
    data: TMaybeRef[typing.List]
    disabled: TMaybeRef[bool]
    empty: TMaybeRef[str]
    filter: TMaybeRef[str]
    filterable: TMaybeRef[bool]
    input_props: TMaybeRef[typing.Dict]
    input_value: TMaybeRef[typing.Union[TMaybeRef[float], TMaybeRef[str]]]
    default_input_value: TMaybeRef[typing.Union[TMaybeRef[float], TMaybeRef[str]]]
    keys: TMaybeRef[typing.Dict]
    label: TMaybeRef[str]
    loading: TMaybeRef[bool]
    loading_text: TMaybeRef[str]
    max: TMaybeRef[float]
    min_collapsed_num: TMaybeRef[float]
    multiple: TMaybeRef[bool]
    panel_bottom_content: TMaybeRef[str]
    panel_top_content: TMaybeRef[str]
    placeholder: TMaybeRef[str]
    popup_props: TMaybeRef[typing.Dict]
    popup_visible: TMaybeRef[bool]
    default_popup_visible: TMaybeRef[bool]
    readonly: TMaybeRef[bool]
    reserve_keyword: TMaybeRef[bool]
    select_input_props: TMaybeRef[typing.Dict]
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    status: TMaybeRef[typing.Literal["default", "success", "warning", "error"]]
    suffix: TMaybeRef[str]
    tag_props: TMaybeRef[typing.Dict]
    tips: TMaybeRef[str]
    tree_props: TMaybeRef[typing.Dict]
    default_value: TMaybeRef[typing.Union[str, int, typing.List]]
    value_display: TMaybeRef[str]
    value_type: TMaybeRef[typing.Literal["value", "object"]]
    on_blur: EventMixin
    on_change: EventMixin
    on_clear: EventMixin
    on_enter: EventMixin
    on_focus: EventMixin
    on_input_change: EventMixin
    on_popup_visible_change: EventMixin
    on_remove: EventMixin
    on_search: EventMixin
