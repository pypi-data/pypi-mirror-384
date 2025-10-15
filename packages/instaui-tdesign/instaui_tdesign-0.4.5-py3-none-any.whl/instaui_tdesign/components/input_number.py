from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack

from ._utils import handle_props, handle_event_from_props, try_setup_vmodel


class InputNumber(BaseElement):
    def __init__(
        self,
        value: typing.Optional[typing.Union[str, int, float]] = None,
        *,
        model_value: typing.Optional[typing.Union[str, int, float]] = None,
        **kwargs: Unpack[TInputNumberProps],
    ):
        super().__init__("t-input-number")

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


class TInputNumberProps(TypedDict, total=False):
    align: typing.Literal["left", "center", "right"]
    allow_input_over_limit: bool
    auto_width: bool
    decimal_places: typing.Union[float, typing.Dict]
    disabled: bool
    format: str
    input_props: typing.Dict
    label: str
    large_number: bool
    max: typing.Union[float, str]
    min: typing.Union[float, str]
    placeholder: str
    readonly: bool
    size: typing.Literal["small", "medium", "large"]
    status: typing.Literal["default", "success", "warning", "error"]
    step: typing.Union[float, str]
    suffix: str
    theme: typing.Literal["column", "row", "normal"]
    tips: str
    default_value: typing.Union[str, int, float]
    on_blur: EventMixin
    on_change: EventMixin
    on_enter: EventMixin
    on_focus: EventMixin
    on_keydown: EventMixin
    on_keypress: EventMixin
    on_keyup: EventMixin
    on_validate: EventMixin
