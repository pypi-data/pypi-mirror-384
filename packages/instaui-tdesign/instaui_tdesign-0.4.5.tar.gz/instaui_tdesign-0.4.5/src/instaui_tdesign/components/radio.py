from __future__ import annotations
import typing
from instaui import ui
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from instaui.vars.mixin_types.element_binding import ElementBindingMixin
from typing_extensions import TypedDict, Unpack

from ._utils import handle_props, handle_event_from_props, try_setup_vmodel


class Radio(BaseElement):
    def __init__(
        self,
        checked: typing.Optional[bool] = None,
        *,
        checked_value: typing.Optional[bool] = None,
        allow_uncheck: bool = True,
        **kwargs: Unpack[TRadioProps],
    ):
        super().__init__("t-radio")

        self.props({"allow-uncheck": allow_uncheck})
        try_setup_vmodel(self, checked)

        self.props(handle_props(kwargs, model_value=checked_value))  # type: ignore
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


class RadioGroup(BaseElement):
    def __init__(
        self,
        options: typing.List[
            typing.Union[str, int, bool, typing.Dict[str, typing.Union[str, int, bool]]]
        ] = [],
        value: typing.Optional[typing.Union[bool, int, str]] = None,
        *,
        model_value: typing.Optional[typing.Union[bool, int, str]] = None,
        **kwargs: Unpack[TRadioGroupProps],
    ):
        super().__init__("t-radio-group")
        if isinstance(options, ElementBindingMixin):
            options = ui.js_computed(
                inputs=[options],
                code=r"""opts=>{
    if(opts.length===0){return opts}
    const data = opts[0]
    if(typeof data === 'object'){return opts}
    return opts.map(item=>({label:item.toString(),value:item}))                   
}""",
            )  # type: ignore

        elif isinstance(options, list) and options and not isinstance(options[0], dict):
            options = [{"label": str(item), "value": item} for item in options]

        self.props({"options": options})

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


class TRadioProps(TypedDict, total=False):
    default_checked: bool
    disabled: bool
    label: str
    name: str
    readonly: bool
    value: typing.Union[bool, float, str]
    on_change: EventMixin
    on_click: EventMixin


class TRadioGroupProps(TypedDict, total=False):
    allow_uncheck: bool
    disabled: bool
    name: str
    readonly: bool
    size: typing.Literal["small", "medium", "large"]
    theme: typing.Literal["radio", "button"]
    default_value: typing.Union[bool, int, str]
    variant: typing.Literal["outline", "primary-filled", "default-filled"]
    on_change: EventMixin
