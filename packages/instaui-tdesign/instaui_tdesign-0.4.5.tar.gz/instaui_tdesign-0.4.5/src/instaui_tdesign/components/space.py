from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack

from ._utils import handle_props, handle_event_from_props


class Space(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TSpaceProps],
    ):
        super().__init__("t-space")

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TSpaceProps(TypedDict, total=False):
    align: typing.Literal["start", "end", "center", "baseline"]
    break_line: bool
    direction: typing.Literal["vertical", "horizontal"]
    separator: str
    size: typing.Literal["SpaceSize"]
