from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Loadding(BaseElement):
    def __init__(
        self,
        *,
        text: typing.Optional[TMaybeRef[str]] = None,
        **kwargs: Unpack[TLoadingProps],
    ):
        super().__init__("t-loadding")
        self.props({"text": text})
        self.props(handle_props(kwargs))  # type: ignore


class TLoadingProps(TypedDict, total=False):
    attach: TMaybeRef[str]
    content: TMaybeRef[str]
    default: TMaybeRef[str]
    delay: TMaybeRef[float]
    fullscreen: TMaybeRef[bool]
    indicator: TMaybeRef[typing.Union[TMaybeRef[bool], TMaybeRef[str]]]
    inherit_color: TMaybeRef[bool]
    loading: TMaybeRef[bool]
    prevent_scroll_through: TMaybeRef[bool]
    show_overlay: TMaybeRef[bool]
    size: TMaybeRef[str]
    z_index: TMaybeRef[float]
