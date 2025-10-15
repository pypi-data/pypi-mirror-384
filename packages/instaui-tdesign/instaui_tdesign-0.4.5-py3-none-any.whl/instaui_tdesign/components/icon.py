from __future__ import annotations
from typing import List, Optional
from instaui import custom
from instaui.event.event_mixin import EventMixin

_prefix: Optional[str] = None


class Icon(custom.element):
    def __init__(
        self,
        name: str,
        *,
        size: Optional[str] = None,
        color: Optional[str] = None,
    ):
        super().__init__("t-icon")
        self.props(
            {
                "name": name,
                "size": size,
                "color": color,
                "prefix": _prefix,
            }
        )

    def on_click(
        self,
        handler: EventMixin,
        *,
        extends: Optional[List] = None,
    ):
        self.on(
            "click",
            handler,
            extends=extends,
        )
        return self


def _reset_prefix(value: str):
    global _prefix
    _prefix = value
