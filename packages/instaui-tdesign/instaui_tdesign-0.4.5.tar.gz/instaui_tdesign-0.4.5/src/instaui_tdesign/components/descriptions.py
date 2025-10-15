from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Descriptions(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TDescriptionsProps],
    ):
        super().__init__("t-descriptions")
        self.props(handle_props(kwargs))  # type: ignore


class DescriptionsItem(BaseElement):
    def __init__(
        self,
        content: typing.Optional[TMaybeRef[str]] = None,
        **kwargs: Unpack[TDescriptionsItemProps],
    ):
        super().__init__("t-descriptions-item")
        self.props({"content": content})
        self.props(handle_props(kwargs))  # type: ignore


class TDescriptionsProps(TypedDict, total=False):
    bordered: TMaybeRef[bool]
    colon: TMaybeRef[bool]
    column: TMaybeRef[int]
    content_style: TMaybeRef[typing.Dict]
    item_layout: TMaybeRef[typing.Literal["horizontal", "vertical"]]
    items: TMaybeRef[typing.List]
    label_style: TMaybeRef[typing.Dict]
    layout: TMaybeRef[typing.Literal["horizontal", "vertical"]]
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    table_layout: TMaybeRef[typing.Literal["fixed", "auto"]]
    title: TMaybeRef[str]


class TDescriptionsItemProps(TypedDict, total=False):
    label: TMaybeRef[str]
    span: TMaybeRef[int]
