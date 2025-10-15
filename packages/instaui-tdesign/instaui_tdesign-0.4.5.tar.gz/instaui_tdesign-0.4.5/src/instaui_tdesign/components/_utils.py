from typing import Dict
from instaui.components.element import Element
from instaui.vars.mixin_types.element_binding import ElementBindingMixin
from instaui.event.event_mixin import EventMixin


def handle_props(props: Dict, *, model_value=None):
    props = {k.replace("_", "-"): v for k, v in props.items()}
    if model_value is not None:
        props["modelValue"] = model_value
    return props


def handle_event_from_props(element: Element, props: Dict):
    for k, v in props.items():
        if isinstance(v, EventMixin):
            # 'on_click' -> 'click'
            element.on(k.replace("on_", ""), v)


def try_setup_vmodel(
    element: Element,
    value,
    *,
    prop_name: str = "value",
):
    if value is None:
        return
    if isinstance(value, ElementBindingMixin):
        element.vmodel(value, prop_name=prop_name)
        return

    element.props({prop_name: value})
