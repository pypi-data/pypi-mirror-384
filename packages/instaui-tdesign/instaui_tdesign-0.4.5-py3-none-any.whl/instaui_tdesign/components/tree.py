from __future__ import annotations
import typing

from instaui_tdesign.components._icon_param_utils import make_icon_for_bool_or_str
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Tree(BaseElement):
    def __init__(
        self,
        data: TMaybeRef[typing.List],
        *,
        activable: typing.Optional[TMaybeRef[bool]] = None,
        hover: typing.Optional[TMaybeRef[bool]] = None,
        transition: typing.Optional[TMaybeRef[bool]] = None,
        icon: typing.Union[str, bool, None] = None,
        **kwargs: Unpack[TTreeProps],
    ):
        super().__init__("t-tree")
        self.props(
            {
                "data": data,
                "activable": activable,
                "hover": hover,
                "transition": transition,
            }
        )
        make_icon_for_bool_or_str(self, "icon", icon)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_active(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "active",
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

    def on_drag_end(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "drag_end",
            handler,
            extends=extends,
        )
        return self

    def on_drag_leave(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "drag_leave",
            handler,
            extends=extends,
        )
        return self

    def on_drag_over(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "drag_over",
            handler,
            extends=extends,
        )
        return self

    def on_drag_start(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "drag_start",
            handler,
            extends=extends,
        )
        return self

    def on_drop(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "drop",
            handler,
            extends=extends,
        )
        return self

    def on_expand(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "expand",
            handler,
            extends=extends,
        )
        return self

    def on_load(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "load",
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


class TTreeProps(TypedDict, total=False):
    active_multiple: TMaybeRef[bool]
    actived: TMaybeRef[typing.List]
    allow_drop: TMaybeRef[str]
    allow_fold_node_on_filter: TMaybeRef[bool]
    check_props: TMaybeRef[typing.Dict]
    check_strictly: TMaybeRef[bool]
    checkable: TMaybeRef[bool]
    disable_check: TMaybeRef[typing.Union[TMaybeRef[bool], TMaybeRef[str]]]
    disabled: TMaybeRef[bool]
    draggable: TMaybeRef[bool]
    empty: TMaybeRef[str]
    expand_all: TMaybeRef[bool]
    expand_level: TMaybeRef[float]
    expand_mutex: TMaybeRef[bool]
    expand_on_click_node: TMaybeRef[bool]
    expand_parent: TMaybeRef[bool]
    expanded: TMaybeRef[typing.List]
    filter: TMaybeRef[str]
    height: TMaybeRef[typing.Union[float, str]]
    keys: TMaybeRef[typing.Dict]
    label: TMaybeRef[typing.Literal["boolean"]]
    lazy: TMaybeRef[bool]
    line: TMaybeRef[typing.Union[bool, str]]
    load: TMaybeRef[str]
    max_height: TMaybeRef[typing.Union[float, str]]
    operations: TMaybeRef[str]
    scroll: TMaybeRef[typing.Dict]
    value: TMaybeRef[typing.List]
    default_value: TMaybeRef[typing.List]
    value_mode: TMaybeRef[typing.Literal["onlyLeaf", "parentFirst", "all"]]
    on_active: EventMixin
    on_change: EventMixin
    on_click: EventMixin
    on_drag_end: EventMixin
    on_drag_leave: EventMixin
    on_drag_over: EventMixin
    on_drag_start: EventMixin
    on_drop: EventMixin
    on_expand: EventMixin
    on_load: EventMixin
    on_scroll: EventMixin
