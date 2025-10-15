from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Progress(BaseElement):
    def __init__(
        self,
        percentage: typing.Optional[TMaybeRef[float]] = None,
        *,
        label: typing.Optional[TMaybeRef[typing.Union[str, bool]]] = None,
        size: typing.Optional[TMaybeRef[typing.Union[float, str]]] = None,
        status: typing.Optional[
            TMaybeRef[typing.Literal["success", "error", "warning", "active"]]
        ] = None,
        **kwargs: Unpack[TProgressProps],
    ):
        super().__init__("t-progress")
        self.props(
            {"percentage": percentage, "label": label, "size": size, "status": status}
        )
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TProgressProps(TypedDict, total=False):
    color: TMaybeRef[typing.Union[str, typing.List[str]]]
    stroke_width: TMaybeRef[typing.Union[float, str]]
    theme: TMaybeRef[typing.Literal["line", "plump", "circle"]]
    track_color: TMaybeRef[str]
