from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Guide(BaseElement):
    def __init__(
        self,
        *,
        current: TMaybeRef[int],
        steps: TMaybeRef[typing.List[TGuideStepValue]],
        **kwargs: Unpack[TGuideProps],
    ):
        super().__init__("t-guide")
        self.props({"steps": steps})
        try_setup_vmodel(self, current, prop_name="current")
        self.props(handle_props(kwargs))  # type: ignore
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

    def on_finish(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "finish",
            handler,
            extends=extends,
        )
        return self

    def on_next_step_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "next_step_click",
            handler,
            extends=extends,
        )
        return self

    def on_prev_step_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "prev_step_click",
            handler,
            extends=extends,
        )
        return self

    def on_skip(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "skip",
            handler,
            extends=extends,
        )
        return self


class TGuideProps(TypedDict, total=False):
    counter: TMaybeRef[str]
    default_current: TMaybeRef[int]
    finish_button_props: TMaybeRef[typing.Dict]
    hide_counter: TMaybeRef[bool]
    hide_prev: TMaybeRef[bool]
    hide_skip: TMaybeRef[bool]
    highlight_padding: TMaybeRef[float]
    mode: TMaybeRef[typing.Literal["popup", "dialog"]]
    next_button_props: TMaybeRef[typing.Dict]
    prev_button_props: TMaybeRef[typing.Dict]
    show_overlay: TMaybeRef[bool]
    skip_button_props: TMaybeRef[typing.Dict]
    z_index: TMaybeRef[float]
    on_change: EventMixin
    on_finish: EventMixin
    on_next_step_click: EventMixin
    on_prev_step_click: EventMixin
    on_skip: EventMixin


class TGuideStepValue(TypedDict, total=False):
    body: TMaybeRef[str]
    content: TMaybeRef[str]
    element: TMaybeRef[str]
    highlight_content: TMaybeRef[str]
    highlight_padding: TMaybeRef[float]
    mode: TMaybeRef[typing.Literal["popup", "dialog"]]
    next_button_props: TMaybeRef[typing.Dict]
    offset: TMaybeRef[typing.List]
    placement: TMaybeRef[typing.Union[TStepPopupPlacement, TStepDialogPlacement]]
    popup_props: TMaybeRef[typing.Dict]
    prev_button_props: TMaybeRef[typing.Dict]
    show_overlay: TMaybeRef[bool]
    skip_button_props: TMaybeRef[typing.Dict]
    step_overlay_class: TMaybeRef[str]
    title: TMaybeRef[str]


TStepPopupPlacement = typing.Literal[
    "top",
    "left",
    "right",
    "bottom",
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
    "left-top",
    "left-bottom",
    "right-top",
    "right-bottom",
]
TStepDialogPlacement = typing.Literal["top", "center"]
