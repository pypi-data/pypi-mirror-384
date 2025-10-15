from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props
from .popup import TPopupProps, TPopupPlacementValue

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Tooltip(BaseElement):
    def __init__(
        self,
        content: TMaybeRef[str],
        **kwargs: Unpack[TTooltipProps],
    ):
        super().__init__("t-tooltip")
        self.props({"content": content})
        self.props(handle_props(kwargs))  # type: ignore


class TooltipLite(BaseElement):
    def __init__(
        self,
        content: TMaybeRef[str],
        **kwargs: Unpack[TTooltipLiteProps],
    ):
        super().__init__("t-tooltip-lite")
        self.props({"content": content})
        self.props(handle_props(kwargs))  # type: ignore


class TTooltipProps(TPopupProps):
    delay: TMaybeRef[float]
    destroy_on_close: TMaybeRef[bool]
    duration: TMaybeRef[float]
    placement: TMaybeRef[TPopupPlacementValue]
    show_arrow: TMaybeRef[bool]
    theme: TMaybeRef[
        typing.Literal["default", "primary", "success", "danger", "warning", "light"]
    ]


class TTooltipLiteProps(TypedDict, total=False):
    placement: TMaybeRef[typing.Literal["top", "bottom"]]
    show_arrow: TMaybeRef[bool]
    show_shadow: TMaybeRef[bool]
    theme: TMaybeRef[typing.Literal["light", "default"]]
    trigger_element: TMaybeRef[typing.Literal["TNode"]]
