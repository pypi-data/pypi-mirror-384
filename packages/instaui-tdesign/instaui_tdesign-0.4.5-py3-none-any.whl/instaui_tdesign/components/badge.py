from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Badge(BaseElement):
    def __init__(
        self,
        content: typing.Optional[TMaybeRef[str]] = None,
        **kwargs: Unpack[TBadgeProps],
    ):
        super().__init__("t-badge")
        self.props({"content": content})

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TBadgeProps(TypedDict, total=False):
    color: TMaybeRef[str]
    count: TMaybeRef[typing.Union[int, str]]
    dot: TMaybeRef[bool]
    max_count: float
    offset: TMaybeRef[typing.List]
    shape: TMaybeRef[typing.Literal["circle", "round"]]
    show_zero: TMaybeRef[bool]
    size: TMaybeRef[typing.Literal["small", "medium"]]
