from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class ImageViewer(BaseElement):
    def __init__(
        self,
        images: typing.Optional[TMaybeRef[typing.List[str]]] = None,
        **kwargs: Unpack[TImageViewerProps],
    ):
        super().__init__("t-image-viewer")
        self.props({"images": images})
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_close(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "close",
            handler,
            extends=extends,
        )
        return self

    def on_download(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "download",
            handler,
            extends=extends,
        )
        return self

    def on_index_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "index_change",
            handler,
            extends=extends,
        )
        return self


class TImageViewerProps(TypedDict, total=False):
    attach: TMaybeRef[str]
    close_btn: TMaybeRef[typing.Union[bool, str]]
    close_on_esc_keydown: TMaybeRef[bool]
    close_on_overlay: TMaybeRef[bool]
    draggable: TMaybeRef[bool]
    image_referrerpolicy: TMaybeRef[
        typing.Literal[
            "no-referrer",
            "no-referrer-when-downgrade",
            "origin",
            "origin-when-cross-origin",
            "same-origin",
            "strict-origin",
            "strict-origin-when-cross-origin",
            "unsafe-url",
        ]
    ]
    image_scale: TMaybeRef[typing.Dict]
    index: TMaybeRef[float]
    default_index: TMaybeRef[float]
    mode: TMaybeRef[typing.Literal["modal", "modeless"]]
    navigation_arrow: TMaybeRef[typing.Union[bool, str]]
    show_overlay: TMaybeRef[bool]
    title: TMaybeRef[str]
    trigger: TMaybeRef[str]
    viewer_scale: TMaybeRef[typing.Dict]
    visible: TMaybeRef[bool]
    default_visible: TMaybeRef[bool]
    z_index: TMaybeRef[float]
    on_close: EventMixin
    on_download: EventMixin
    on_index_change: EventMixin
