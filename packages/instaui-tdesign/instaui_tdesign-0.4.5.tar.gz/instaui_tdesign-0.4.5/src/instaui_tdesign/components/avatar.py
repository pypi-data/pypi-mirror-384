from __future__ import annotations
import typing

from instaui_tdesign.components._icon_param_utils import make_icon_for_str
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Avatar(BaseElement):
    def __init__(
        self,
        *,
        icon: typing.Optional[str] = None,
        **kwargs: Unpack[TAvatarProps],
    ):
        super().__init__("t-avatar")
        make_icon_for_str(self, icon)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_error(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "error",
            handler,
            extends=extends,
        )
        return self


class AvatarGroup(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TAvatarGroupProps],
    ):
        super().__init__("t-avatar-group")

        self.props(handle_props(kwargs))  # type: ignore


class TAvatarProps(TypedDict, total=False):
    alt: TMaybeRef[str]
    content: TMaybeRef[str]
    hide_on_load_failed: TMaybeRef[bool]
    image: TMaybeRef[str]
    image_props: TMaybeRef[typing.Dict]
    shape: TMaybeRef[typing.Literal["circle", "round"]]
    size: TMaybeRef[typing.Literal["small", "medium", "large", "24px", "38px"]]
    on_error: EventMixin


class TAvatarGroupProps(TypedDict, total=False):
    cascading: TMaybeRef[typing.Literal["left-up", "right-up"]]
    collapse_avatar: TMaybeRef[str]
    max: TMaybeRef[float]
    popup_props: TMaybeRef[typing.Dict]
    size: TMaybeRef[typing.Literal["small", "medium", "large", "24px", "38px"]]
