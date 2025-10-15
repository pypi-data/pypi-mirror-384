from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Calendar(BaseElement):
    def __init__(
        self,
        value: typing.Optional[TMaybeRef[typing.Union[str, typing.List[str]]]] = None,
        **kwargs: Unpack[TCalendarProps],
    ):
        super().__init__("t-calendar")

        self.props({"value": value})
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_cell_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "cell_click",
            handler,
            extends=extends,
        )
        return self

    def on_cell_double_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "cell_double_click",
            handler,
            extends=extends,
        )
        return self

    def on_cell_right_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "cell_right_click",
            handler,
            extends=extends,
        )
        return self

    def on_controller_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "controller_change",
            handler,
            extends=extends,
        )
        return self

    def on_month_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "month_change",
            handler,
            extends=extends,
        )
        return self


class TCalendarProps(TypedDict, total=False):
    cell: TMaybeRef[str]
    cell_append: TMaybeRef[str]
    controller_config: TMaybeRef[typing.Union[bool, typing.Dict]]
    fill_with_zero: TMaybeRef[bool]
    first_day_of_week: TMaybeRef[float]
    format: TMaybeRef[str]
    head: TMaybeRef[str]
    is_show_weekend_default: TMaybeRef[bool]
    mode: TMaybeRef[typing.Literal["month", "year"]]
    month: TMaybeRef[typing.Union[float, str]]
    multiple: TMaybeRef[bool]
    prevent_cell_contextmenu: TMaybeRef[bool]
    range: TMaybeRef[typing.List]
    theme: TMaybeRef[typing.Literal["full", "card"]]
    week: TMaybeRef[typing.Union[str, typing.List]]
    year: TMaybeRef[typing.Union[float, str]]
    on_cell_click: EventMixin
    on_cell_double_click: EventMixin
    on_cell_right_click: EventMixin
    on_controller_change: EventMixin
    on_month_change: EventMixin
