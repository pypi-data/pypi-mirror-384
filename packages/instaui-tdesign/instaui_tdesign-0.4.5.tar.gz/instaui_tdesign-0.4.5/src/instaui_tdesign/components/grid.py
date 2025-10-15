from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack

from ._utils import handle_props, handle_event_from_props


class Row(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TRowProps],
    ):
        super().__init__("t-row")

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class Col(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TColProps],
    ):
        super().__init__("t-col")

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TRowProps(TypedDict, total=False):
    align: typing.Literal[
        "start", "end", "center", "stretch", "baseline", "top", "middle", "bottom"
    ]
    gutter: typing.Union[float, typing.Dict, typing.List]
    justify: typing.Literal["start", "end", "center", "space-around", "space-between"]
    tag: str


class TColProps(TypedDict, total=False):
    flex: typing.Union[float, str]
    lg: typing.Union[float, typing.Dict]
    md: typing.Union[float, typing.Dict]
    offset: float
    order: float
    pull: float
    push: float
    sm: typing.Union[float, typing.Dict]
    span: float
    tag: str
    xl: typing.Union[float, typing.Dict]
    xs: typing.Union[float, typing.Dict]
    xxl: typing.Union[float, typing.Dict]
