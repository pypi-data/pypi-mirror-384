from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class TimePicker(BaseElement):
    def __init__(
        self,
        value: typing.Optional[TMaybeRef[str]] = None,
        *,
        model_value: typing.Optional[TMaybeRef[str]] = None,
        **kwargs: Unpack[TTimePickerProps],
    ):
        super().__init__("t-time-picker")

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

    def on_close(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "close",
            handler,
            extends=extends,
        )
        return self

    def on_confirm(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "confirm",
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

    def on_input(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "input",
            handler,
            extends=extends,
        )
        return self

    def on_open(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "open",
            handler,
            extends=extends,
        )
        return self

    def on_pick(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "pick",
            handler,
            extends=extends,
        )
        return self


class TimeRangePicker(BaseElement):
    def __init__(
        self,
        value: typing.Optional[TMaybeRef[typing.List]] = None,
        *,
        model_value: typing.Optional[TMaybeRef[typing.List]] = None,
        **kwargs: Unpack[TTimeRangePickerProps],
    ):
        super().__init__("t-time-range-picker")

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

    def on_input(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "input",
            handler,
            extends=extends,
        )
        return self

    def on_pick(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "pick",
            handler,
            extends=extends,
        )
        return self


class TTimePickerProps(TypedDict, total=False):
    allow_input: TMaybeRef[bool]
    borderless: TMaybeRef[bool]
    clearable: TMaybeRef[bool]
    disable_time: TMaybeRef[str]
    disabled: TMaybeRef[bool]
    format: TMaybeRef[str]
    hide_disabled_time: TMaybeRef[bool]
    input_props: TMaybeRef[typing.Dict]
    label: TMaybeRef[str]
    placeholder: TMaybeRef[str]
    popup_props: TMaybeRef[typing.Dict]
    presets: TMaybeRef[typing.Dict]
    readonly: TMaybeRef[bool]
    select_input_props: TMaybeRef[typing.Dict]
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    status: TMaybeRef[typing.Literal["default", "success", "warning", "error"]]
    steps: TMaybeRef[typing.List]
    tips: TMaybeRef[str]
    default_value: TMaybeRef[str]
    value_display: TMaybeRef[str]
    on_blur: EventMixin
    on_change: EventMixin
    on_clear: EventMixin
    on_close: EventMixin
    on_confirm: EventMixin
    on_focus: EventMixin
    on_input: EventMixin
    on_open: EventMixin
    on_pick: EventMixin


class TTimeRangePickerProps(TypedDict, total=False):
    allow_input: TMaybeRef[bool]
    auto_swap: TMaybeRef[bool]
    borderless: TMaybeRef[bool]
    clearable: TMaybeRef[bool]
    disable_time: TMaybeRef[str]
    disabled: TMaybeRef[typing.Union[TMaybeRef[bool], TMaybeRef[typing.List]]]
    format: TMaybeRef[str]
    hide_disabled_time: TMaybeRef[bool]
    label: TMaybeRef[typing.Literal["TNode"]]
    placeholder: TMaybeRef[typing.Literal["Array"]]
    popup_props: TMaybeRef[typing.Dict]
    presets: TMaybeRef[typing.Dict]
    range_input_props: TMaybeRef[typing.Dict]
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    status: TMaybeRef[typing.Literal["default", "success", "warning", "error"]]
    steps: TMaybeRef[typing.List]
    tips: TMaybeRef[typing.Literal["TNode"]]
    default_value: TMaybeRef[typing.List]
    on_blur: EventMixin
    on_change: EventMixin
    on_focus: EventMixin
    on_input: EventMixin
    on_pick: EventMixin
