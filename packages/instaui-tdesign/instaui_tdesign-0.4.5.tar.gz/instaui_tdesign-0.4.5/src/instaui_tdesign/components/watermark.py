from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Watermark(BaseElement):
    def __init__(
        self,
        content: TMaybeRef[str],
        **kwargs: Unpack[TWatermarkProps],
    ):
        super().__init__("t-watermark")
        self.props({"content": content})
        self.props(handle_props(kwargs))  # type: ignore


class TWatermarkProps(TypedDict, total=False):
    alpha: TMaybeRef[float]
    height: TMaybeRef[float]
    is_repeat: TMaybeRef[bool]
    line_space: TMaybeRef[float]
    movable: TMaybeRef[bool]
    move_interval: TMaybeRef[float]
    offset: TMaybeRef[typing.List]
    removable: TMaybeRef[bool]
    rotate: TMaybeRef[float]
    watermark_content: TMaybeRef[
        typing.Union[TMaybeRef[typing.Dict], TMaybeRef[typing.List]]
    ]
    width: TMaybeRef[float]
    x: TMaybeRef[float]
    y: TMaybeRef[float]
    z_index: TMaybeRef[int]
