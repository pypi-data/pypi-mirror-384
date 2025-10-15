from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Pagination(BaseElement):
    def __init__(
        self,
        current: typing.Optional[TMaybeRef[int]] = None,
        *,
        current_value: typing.Optional[TMaybeRef[bool]] = None,
        page_size: typing.Optional[TMaybeRef[int]] = None,
        page_size_value: typing.Optional[TMaybeRef[int]] = None,
        **kwargs: Unpack[TPaginationProps],
    ):
        super().__init__("t-pagination")

        try_setup_vmodel(self, current, prop_name="current")
        try_setup_vmodel(self, page_size, prop_name="page-size")

        if page_size_value is not None:
            self.props({"page-size": page_size_value})

        if current_value is not None:
            self.props({"current": current_value})

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

    def on_current_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "current_change",
            handler,
            extends=extends,
        )
        return self

    def on_page_size_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "page_size_change",
            handler,
            extends=extends,
        )
        return self


class PaginationMini(BaseElement):
    def __init__(
        self,
        current: typing.Optional[int] = None,
        *,
        current_value: typing.Optional[bool] = None,
        **kwargs: Unpack[TPaginationMiniProps],
    ):
        super().__init__("t-pagination-mini")

        try_setup_vmodel(self, current)

        self.props(handle_props(kwargs, model_value=current_value))  # type: ignore
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


class TPaginationProps(TypedDict, total=False):
    default_current: TMaybeRef[int]
    disabled: TMaybeRef[bool]
    folded_max_page_btn: TMaybeRef[int]
    max_page_btn: TMaybeRef[int]
    page_ellipsis_mode: typing.Literal["mid", "both-ends"]
    default_page_size: TMaybeRef[int]
    page_size_options: typing.List
    select_props: typing.Dict
    show_first_and_last_page_btn: TMaybeRef[bool]
    show_jumper: TMaybeRef[bool]
    show_page_number: TMaybeRef[bool]
    show_page_size: TMaybeRef[bool]
    show_previous_and_next_btn: TMaybeRef[bool]
    size: TMaybeRef[typing.Literal["small", "medium"]]
    theme: TMaybeRef[typing.Literal["default", "simple"]]
    total: TMaybeRef[int]
    total_content: typing.Union[TMaybeRef[bool], TMaybeRef[str]]
    on_change: EventMixin
    on_current_change: EventMixin
    on_page_size_change: EventMixin


class TPaginationMiniProps(TypedDict, total=False):
    disabled: typing.Union[bool, typing.Dict]
    layout: TMaybeRef[typing.Literal["horizontal", "vertical"]]
    show_current: bool
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    tips: typing.Dict
    variant: TMaybeRef[typing.Literal["text", "outline"]]
    on_change: EventMixin
