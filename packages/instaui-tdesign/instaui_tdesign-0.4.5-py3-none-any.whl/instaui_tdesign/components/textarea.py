from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Textarea(BaseElement):
    def __init__(
        self,
        value: typing.Optional[TMaybeRef[str]] = None,
        *,
        model_value: typing.Optional[TMaybeRef[str]] = None,
        **kwargs: Unpack[TTextareaProps],
    ):
        super().__init__("t-textarea")

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


class TTextareaProps(TypedDict, total=False):
    allow_input_over_max: TMaybeRef[bool]
    autofocus: TMaybeRef[bool]
    autosize: TMaybeRef[typing.Union[bool, typing.Dict]]
    disabled: TMaybeRef[bool]
    maxcharacter: TMaybeRef[float]
    maxlength: TMaybeRef[int]
    name: TMaybeRef[str]
    placeholder: TMaybeRef[str]
    readonly: TMaybeRef[bool]
    status: TMaybeRef[typing.Literal["default", "success", "warning", "error"]]
    tips: TMaybeRef[str]
    default_value: TMaybeRef[str]
    on_blur: EventMixin
    on_change: EventMixin
    on_focus: EventMixin
    on_keydown: EventMixin
    on_keypress: EventMixin
    on_keyup: EventMixin
    on_validate: EventMixin
