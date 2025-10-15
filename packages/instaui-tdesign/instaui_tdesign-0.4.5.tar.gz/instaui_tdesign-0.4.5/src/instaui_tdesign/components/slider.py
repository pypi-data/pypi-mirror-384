from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Slider(BaseElement):
    def __init__(
        self,
        value: typing.Optional[TMaybeRef[typing.Union[float, typing.List]]] = None,
        *,
        model_value: typing.Optional[
            TMaybeRef[typing.Union[float, typing.List]]
        ] = None,
        min: typing.Optional[TMaybeRef[float]] = None,
        max: typing.Optional[TMaybeRef[float]] = None,
        range: typing.Optional[TMaybeRef[bool]] = None,
        **kwargs: Unpack[TSliderProps],
    ):
        super().__init__("t-select")

        self.props(
            {
                "max": max,
                "min": min,
                "range": range,
            }
        )
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

    def on_change_end(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "change_end",
            handler,
            extends=extends,
        )
        return self


class TSliderProps(TypedDict, total=False):
    disabled: TMaybeRef[bool]
    input_number_props: TMaybeRef[typing.Union[TMaybeRef[bool], TMaybeRef[typing.Dict]]]
    label: TMaybeRef[typing.Literal["boolean"]]
    layout: TMaybeRef[typing.Literal["vertical", "horizontal"]]
    marks: TMaybeRef[typing.Union[TMaybeRef[typing.Dict], TMaybeRef[typing.List]]]
    show_step: TMaybeRef[bool]
    step: TMaybeRef[float]
    tooltip_props: TMaybeRef[typing.Dict]
    default_value: TMaybeRef[typing.Union[float, typing.List]]
    on_change: EventMixin
    on_change_end: EventMixin
