from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Checkbox(BaseElement):
    def __init__(
        self,
        checked: typing.Optional[TMaybeRef[bool]] = None,
        *,
        label: typing.Optional[TMaybeRef[str]] = None,
        checked_value: typing.Optional[TMaybeRef[bool]] = None,
        **kwargs: Unpack[TCheckboxProps],
    ):
        super().__init__("t-checkbox")
        self.props({"label": label})

        try_setup_vmodel(self, checked)
        self.props(handle_props(kwargs, model_value=checked_value))  # type: ignore
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


class CheckboxGroup(BaseElement):
    def __init__(
        self,
        options: typing.Optional[
            typing.List[typing.Union[str, TCheckboxOption]]
        ] = None,
        value: typing.Optional[typing.List[typing.Union[int, str, bool]]] = None,
        *,
        model_value: typing.Optional[typing.List[typing.Union[int, str, bool]]] = None,
        **kwargs: Unpack[TCheckboxGroupProps],
    ):
        super().__init__("t-checkbox-group")

        self.props({"options": options})
        try_setup_vmodel(self, value)
        self.props(handle_props(kwargs, model_value=model_value))  # type: ignore
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


class TCheckboxProps(TypedDict, total=False):
    check_all: TMaybeRef[bool]
    default_checked: TMaybeRef[bool]
    disabled: TMaybeRef[bool]
    indeterminate: TMaybeRef[bool]
    lazy_load: TMaybeRef[bool]
    name: TMaybeRef[str]
    readonly: TMaybeRef[bool]
    title: TMaybeRef[str]
    value: TMaybeRef[typing.Union[int, str, bool]]
    on_change: EventMixin


class TCheckboxGroupProps(TypedDict, total=False):
    disabled: TMaybeRef[bool]
    lazy_load: TMaybeRef[bool]
    max: TMaybeRef[float]
    name: TMaybeRef[str]
    readonly: TMaybeRef[bool]
    default_value: typing.List
    on_change: EventMixin


class TCheckboxOption(TypedDict, total=False):
    label: TMaybeRef[str]
    checkAll: TMaybeRef[bool]
    value: TMaybeRef[typing.Union[int, str]]
