from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Comment(BaseElement):
    def __init__(
        self,
        content: typing.Optional[TMaybeRef[str]] = None,
        **kwargs: Unpack[TCommentProps],
    ):
        super().__init__("t-comment")

        self.props({"content": content})
        self.props(handle_props(kwargs))  # type: ignore


class TCommentProps(TypedDict, total=False):
    actions: TMaybeRef[typing.List]
    author: TMaybeRef[str]
    avatar: TMaybeRef[typing.Dict]
    datetime: TMaybeRef[str]
    quote: TMaybeRef[str]
    reply: TMaybeRef[str]
