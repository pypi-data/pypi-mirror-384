from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Statistic(BaseElement):
    def __init__(
        self,
        *,
        title: typing.Optional[TMaybeRef[str]] = None,
        value: typing.Optional[TMaybeRef[float]] = None,
        unit: typing.Optional[TMaybeRef[str]] = None,
        trend: typing.Optional[
            TMaybeRef[typing.Literal["increase", "decrease"]]
        ] = None,
        **kwargs: Unpack[TStatisticProps],
    ):
        super().__init__("t-statistic")
        self.props({"title": title, "value": value, "unit": unit, "trend": trend})
        self.props(handle_props(kwargs))  # type: ignore


class TStatisticProps(TypedDict, total=False):
    animation: TMaybeRef[typing.Dict]
    animation_start: TMaybeRef[bool]
    color: TMaybeRef[typing.Literal["black", "blue", "red", "orange", "green"]]
    decimal_places: TMaybeRef[float]
    extra: TMaybeRef[str]
    format: TMaybeRef[str]
    loading: TMaybeRef[bool]
    prefix: TMaybeRef[str]
    separator: TMaybeRef[str]
    suffix: TMaybeRef[str]
    trend_placement: TMaybeRef[typing.Literal["left", "right"]]
