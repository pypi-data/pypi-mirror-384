from __future__ import annotations
import typing

from instaui_tdesign.components._icon_param_utils import make_icon_for_str
from ._base_element import BaseElement
from typing_extensions import TypedDict, Unpack
from instaui.event.event_mixin import EventMixin
from ._utils import handle_props, handle_event_from_props, try_setup_vmodel


class Menu(BaseElement):
    def __init__(
        self,
        *,
        value: typing.Union[float, str, None] = None,
        model_value: typing.Union[float, str, None] = None,
        **kwargs: Unpack[TMenuProps],
    ):
        super().__init__("t-menu")

        try_setup_vmodel(self, value)
        self.props(handle_props(kwargs, model_value=model_value))  # type: ignore
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

    def on_expand(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "expand",
            handler,
            extends=extends,
        )
        return self


class HeadMenu(BaseElement):
    def __init__(
        self,
        *,
        value: typing.Union[float, str, None] = None,
        model_value: typing.Union[float, str, None] = None,
        **kwargs: Unpack[THeadMenuProps],
    ):
        super().__init__("t-head-menu")

        try_setup_vmodel(self, value)
        self.props(handle_props(kwargs, model_value=model_value))  # type: ignore
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

    def on_expand(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "expand",
            handler,
            extends=extends,
        )
        return self


class SubMenu(BaseElement):
    def __init__(
        self,
        content: typing.Optional[str] = None,
        *,
        icon: typing.Optional[str] = None,
        **kwargs: Unpack[TSubMenuProps],
    ):
        super().__init__("t-sub-menu")

        self.props({"content": content})
        make_icon_for_str(self, icon)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class MenuItem(BaseElement):
    def __init__(
        self,
        content: typing.Optional[str] = None,
        *,
        icon: typing.Optional[str] = None,
        **kwargs: Unpack[TMenuItemProps],
    ):
        super().__init__("t-menu-item")

        self.props({"content": content})
        make_icon_for_str(self, icon)
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

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


class MenuGroup(BaseElement):
    def __init__(self, title: typing.Optional[str] = None):
        super().__init__("t-menu-group")

        self.props({"title": title})


class TMenuProps(TypedDict, total=False):
    collapsed: bool
    expand_mutex: bool
    expand_type: typing.Literal["normal", "popup"]
    expanded: typing.List
    default_expanded: typing.List
    logo: str
    operations: str
    theme: typing.Literal["light", "dark", "global", "system"]
    default_value: typing.Union[float, str]
    width: typing.Union[float, str, typing.List[typing.Union[float, str]]]
    on_change: EventMixin
    on_expand: EventMixin


class THeadMenuProps(TypedDict, total=False):
    expand_type: typing.Literal["normal", "popup"]
    expanded: typing.List
    default_expanded: typing.List
    logo: str
    operations: str
    theme: typing.Literal["light", "dark"]
    on_change: EventMixin
    on_expand: EventMixin


class TSubMenuProps(TypedDict, total=False):
    disabled: bool
    popup_props: typing.Dict
    title: str
    value: typing.Union[int, str]


class TMenuItemProps(TypedDict, total=False):
    disabled: bool
    href: str
    replace: bool
    router: typing.Dict
    router_link: bool
    target: typing.Literal["_blank", "_self", "_parent", "_top"]
    to: str
    value: typing.Union[int, str]
    on_click: EventMixin
