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


class Input(BaseElement):
    def __init__(
        self,
        value: typing.Optional[typing.Union[str, int, float]] = None,
        *,
        model_value: typing.Optional[typing.Union[str, int, float]] = None,
        prefix_icon: typing.Optional[str] = None,
        suffix_icon: typing.Optional[str] = None,
        **kwargs: Unpack[TInputProps],
    ):
        super().__init__("t-input")

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

    def on_compositionend(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "compositionend",
            handler,
            extends=extends,
        )
        return self

    def on_compositionstart(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "compositionstart",
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

    def on_keydown(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "keydown",
            handler,
            extends=extends,
        )
        return self

    def on_keypress(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "keypress",
            handler,
            extends=extends,
        )
        return self

    def on_keyup(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "keyup",
            handler,
            extends=extends,
        )
        return self

    def on_mouseenter(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "mouseenter",
            handler,
            extends=extends,
        )
        return self

    def on_mouseleave(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "mouseleave",
            handler,
            extends=extends,
        )
        return self

    def on_paste(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "paste",
            handler,
            extends=extends,
        )
        return self

    def on_validate(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "validate",
            handler,
            extends=extends,
        )
        return self

    def on_wheel(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "wheel",
            handler,
            extends=extends,
        )
        return self


class InputGroup(BaseElement):
    def __init__(
        self,
        *,
        separate: typing.Optional[bool] = None,
    ):
        super().__init__("t-input-group")

        self.props({"separate": separate})


class TInputProps(TypedDict, total=False):
    align: typing.Literal["left", "center", "right"]
    allow_input_over_max: bool
    auto_width: bool
    autocomplete: str
    autofocus: bool
    borderless: bool
    clearable: bool
    disabled: bool
    format: str
    input_class: typing.Union[str, typing.Dict, typing.List]
    label: str
    maxcharacter: float
    maxlength: typing.Union[float, str]
    name: str
    placeholder: str
    readonly: bool
    show_clear_icon_on_empty: bool
    show_limit_number: bool
    size: typing.Literal["small", "medium", "large"]
    spell_check: bool
    status: typing.Literal["default", "success", "warning", "error"]
    suffix: str
    tips: str
    type: typing.Literal[
        "text", "number", "url", "tel", "password", "search", "submit", "hidden"
    ]
    default_value: typing.Union[str, int, float]
    on_blur: EventMixin
    on_change: EventMixin
    on_clear: EventMixin
    on_click: EventMixin
    on_compositionend: EventMixin
    on_compositionstart: EventMixin
    on_enter: EventMixin
    on_focus: EventMixin
    on_keydown: EventMixin
    on_keypress: EventMixin
    on_keyup: EventMixin
    on_mouseenter: EventMixin
    on_mouseleave: EventMixin
    on_paste: EventMixin
    on_validate: EventMixin
    on_wheel: EventMixin
