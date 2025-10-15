from typing import Union
from instaui import custom

from instaui_tdesign.components.icon import Icon


def make_icon_for_bool_or_str(
    element: custom.element, slot_name: str, value: Union[bool, str, None]
):
    if value is not None:
        if isinstance(value, bool):
            element.props({slot_name: value})
        else:
            with element.add_slot(slot_name):
                Icon(value)


def make_icon_for_str(
    element: custom.element, value: Union[str, None], *, slot_name: str = "icon"
):
    if value is not None:
        with element.add_slot(slot_name):
            Icon(value)


def make_prefix_icon(element: custom.element, value: Union[str, None]):
    if value is not None:
        with element.add_slot("prefixIcon"):
            Icon(value)


def make_suffix_icon(element: custom.element, value: Union[str, None]):
    if value is not None:
        with element.add_slot("suffixIcon"):
            Icon(value)
