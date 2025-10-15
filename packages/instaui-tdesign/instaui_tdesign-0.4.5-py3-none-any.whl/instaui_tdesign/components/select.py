from __future__ import annotations
import typing
from instaui import ui

from instaui_tdesign.components._icon_param_utils import (
    make_prefix_icon,
    make_suffix_icon,
)
from ._base_element import BaseElement
from instaui.components.content import Content
from instaui.event.event_mixin import EventMixin
from instaui.vars.mixin_types.element_binding import ElementBindingMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Select(BaseElement):
    def __init__(
        self,
        options: TMaybeRef[
            typing.Union[
                typing.List,
                typing.List[typing.Dict],
                None,
            ]
        ],
        value: typing.Optional[TMaybeRef[typing.Any]] = None,
        *,
        model_value: typing.Optional[TMaybeRef[typing.Any]] = None,
        prefix_icon: typing.Optional[str] = None,
        suffix_icon: typing.Optional[str] = None,
        **kwargs: Unpack[TSelectProps],
    ):
        super().__init__("t-select")

        if isinstance(options, ElementBindingMixin):
            options = ui.js_computed(
                inputs=[options],
                code=r"""opts=>{
    if(opts.length===0){return opts}
    const data = opts[0]
    if(typeof data === 'object'){return opts}
    return opts.map(item=>({label:item.toString(),value:item}))                   
}""",
            )  # type: ignore

        elif isinstance(options, list) and options and not isinstance(options[0], dict):
            options = [{"label": str(item), "value": item} for item in options]
        make_prefix_icon(self, prefix_icon)
        make_suffix_icon(self, suffix_icon)
        self.props({"options": options})
        try_setup_vmodel(self, value)

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

    def on_create(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "create",
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


class Option(BaseElement):
    def __init__(
        self,
        content: typing.Optional[TMaybeRef[str]],
        **kwargs: Unpack[TOptionProps],
    ):
        super().__init__("t-option")

        if content is not None:
            with self:
                Content(content)

        self.props(handle_props(kwargs))  # type: ignore


class TSelectProps(TypedDict, total=False):
    auto_width: TMaybeRef[bool]
    autofocus: TMaybeRef[bool]
    borderless: TMaybeRef[bool]
    clearable: TMaybeRef[bool]
    collapsed_items: TMaybeRef[str]
    creatable: TMaybeRef[bool]
    disabled: TMaybeRef[bool]
    empty: TMaybeRef[str]
    filter: TMaybeRef[str]
    filterable: TMaybeRef[bool]
    input_props: TMaybeRef[typing.Dict]
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
    scroll: TMaybeRef[typing.Dict]
    select_input_props: TMaybeRef[typing.Dict]
    show_arrow: TMaybeRef[bool]
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    status: TMaybeRef[typing.Literal["default", "success", "warning", "error"]]
    suffix: TMaybeRef[str]
    tag_input_props: TMaybeRef[typing.Dict]
    tag_props: TMaybeRef[typing.Dict]
    tips: TMaybeRef[str]
    default_value: TMaybeRef[typing.Literal["number"]]
    value_display: TMaybeRef[str]
    value_type: TMaybeRef[typing.Literal["value", "object"]]
    on_blur: EventMixin
    on_change: EventMixin
    on_clear: EventMixin
    on_create: EventMixin
    on_enter: EventMixin
    on_focus: EventMixin
    on_input_change: EventMixin
    on_popup_visible_change: EventMixin
    on_remove: EventMixin
    on_search: EventMixin


class TOptionProps(TypedDict, total=False):
    check_all: TMaybeRef[bool]
    disabled: TMaybeRef[bool]
    label: TMaybeRef[str]
    title: TMaybeRef[str]
    value: TMaybeRef[typing.Union[bool, float, str]]


class TOptionGroupProps(TypedDict, total=False):
    divider: TMaybeRef[bool]
    label: TMaybeRef[str]
