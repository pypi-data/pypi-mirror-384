from __future__ import annotations
import typing

from instaui_tdesign.components._icon_param_utils import make_icon_for_bool_or_str
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack

from ._utils import handle_props, handle_event_from_props


class Form(BaseElement):
    def __init__(
        self,
        *,
        status_icon: typing.Union[bool, str, None] = True,
        **kwargs: Unpack[TFormProps],
    ):
        super().__init__("t-form")

        make_icon_for_bool_or_str(self, "statusIcon", status_icon)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_reset(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "reset",
            handler,
            extends=extends,
        )
        return self

    def on_submit(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "submit",
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


class FormItem(BaseElement):
    def __init__(
        self,
        *,
        status_icon: typing.Union[bool, str, None] = True,
        **kwargs: Unpack[TFormItemProps],
    ):
        super().__init__("t-form-item")
        make_icon_for_bool_or_str(self, "statusIcon", status_icon)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TFormProps(TypedDict, total=False):
    colon: bool
    data: typing.Dict
    disabled: bool
    error_message: typing.Dict
    id: str
    label_align: typing.Literal["left", "right", "top"]
    label_width: typing.Union[float, str]
    layout: typing.Literal["vertical", "inline"]
    prevent_submit_default: bool
    readonly: bool
    required_mark: bool
    required_mark_position: typing.Literal["left", "right"]
    reset_type: typing.Literal["empty", "initial"]
    rules: typing.Dict
    scroll_to_first_error: str
    show_error_message: bool
    submit_with_warning_message: bool
    on_reset: EventMixin
    on_submit: EventMixin
    on_validate: EventMixin


class TFormItemProps(TypedDict, total=False):
    for_: str
    help: str
    label: str
    label_align: typing.Literal["left", "right", "top"]
    label_width: typing.Union[float, str]
    name: str
    required_mark: bool
    rules: typing.List
    show_error_message: bool
    status: str
    success_border: bool
    tips: str
