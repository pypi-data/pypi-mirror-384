from __future__ import annotations
import typing
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack

from ._utils import handle_props, handle_event_from_props


class Layout(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TLayoutProps],
    ):
        super().__init__("t-layout")

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class Header(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[THeaderProps],
    ):
        super().__init__("t-header")

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class Aside(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TAsideProps],
    ):
        super().__init__("t-aside")

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class Content(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TContentProps],
    ):
        super().__init__("t-content")

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class Footer(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TFooterProps],
    ):
        super().__init__("t-footer")

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TLayoutProps(TypedDict, total=False):
    direction: typing.Literal["vertical", "horizontal"]


class THeaderProps(TypedDict, total=False):
    height: str


class TAsideProps(TypedDict, total=False):
    width: str


class TContentProps(TypedDict, total=False):
    content: typing.Literal["TNode"]
    default: typing.Literal["TNode"]


class TFooterProps(TypedDict, total=False):
    height: str
