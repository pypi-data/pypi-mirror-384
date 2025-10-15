from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Anchor(BaseElement):
    def __init__(
        self,
        *,
        affix_props: typing.Optional[typing.Dict] = None,
        **kwargs: Unpack[TAnchorProps],
    ):
        super().__init__("t-anchor")
        self.props(
            {
                "affixProps": affix_props,
            }
        )
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "change",
            handler,
            extends=extends,
        )
        return self

    def on_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "click",
            handler,
            extends=extends,
        )
        return self


class AnchorItem(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TAnchorItemProps],
    ):
        super().__init__("t-anchor-item")

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TAnchorProps(TypedDict, total=False):
    bounds: TMaybeRef[float]
    container: TMaybeRef[str]
    cursor: TMaybeRef[str]
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    target_offset: TMaybeRef[float]
    on_change: EventMixin
    on_click: EventMixin


class TAnchorItemProps(TypedDict, total=False):
    href: TMaybeRef[str]
    target: TMaybeRef[typing.Literal["_self", "_blank", "_parent", "_top"]]
    title: TMaybeRef[str]


class TAnchorTargetProps(TypedDict, total=False):
    id: TMaybeRef[str]
    tag: TMaybeRef[str]
