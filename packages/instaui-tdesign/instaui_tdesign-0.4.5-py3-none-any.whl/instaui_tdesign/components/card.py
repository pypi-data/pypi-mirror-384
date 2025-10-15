from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Card(BaseElement):
    def __init__(
        self,
        content: typing.Optional[TMaybeRef[str]] = None,
        **kwargs: Unpack[TCardProps],
    ):
        super().__init__("t-card")

        self.props({"content": content})
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TCardProps(TypedDict, total=False):
    actions: TMaybeRef[str]
    avatar: TMaybeRef[str]
    bordered: bool
    body_style: TMaybeRef[typing.Dict]
    cover: TMaybeRef[str]
    description: TMaybeRef[str]
    footer: TMaybeRef[str]
    header: TMaybeRef[str]
    header_bordered: TMaybeRef[bool]
    hover_shadow: TMaybeRef[bool]
    loading: TMaybeRef[typing.Union[bool, str]]
    loading_props: typing.Dict
    shadow: TMaybeRef[bool]
    size: TMaybeRef[typing.Literal["medium", "small"]]
    status: TMaybeRef[str]
    subtitle: TMaybeRef[str]
    theme: TMaybeRef[typing.Literal["normal", "poster1", "poster2"]]
    title: TMaybeRef[str]
