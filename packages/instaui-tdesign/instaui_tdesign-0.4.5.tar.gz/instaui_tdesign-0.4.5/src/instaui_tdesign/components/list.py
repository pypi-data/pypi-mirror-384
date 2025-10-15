from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class List(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TListProps],
    ):
        super().__init__("t-list")
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_load_more(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "load_more",
            handler,
            extends=extends,
        )
        return self

    def on_scroll(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "scroll",
            handler,
            extends=extends,
        )
        return self


class ListItem(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TListItemProps],
    ):
        super().__init__("t-list-item")
        self.props(handle_props(kwargs))  # type: ignore


class ListItemMeta(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TListItemMetaProps],
    ):
        super().__init__("t-list-item-meta")
        self.props(handle_props(kwargs))  # type: ignore


class TListProps(TypedDict, total=False):
    async_loading: TMaybeRef[str]
    footer: TMaybeRef[str]
    header: TMaybeRef[str]
    layout: TMaybeRef[typing.Literal["horizontal", "vertical"]]
    scroll: TMaybeRef[typing.Dict]
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    split: TMaybeRef[bool]
    stripe: TMaybeRef[bool]
    on_load_more: EventMixin
    on_scroll: EventMixin


class TListItemProps(TypedDict, total=False):
    action: TMaybeRef[str]
    content: TMaybeRef[str]
    default: TMaybeRef[str]


class TListItemMetaProps(TypedDict, total=False):
    avatar: TMaybeRef[str]
    description: TMaybeRef[str]
    image: TMaybeRef[str]
    title: TMaybeRef[str]
