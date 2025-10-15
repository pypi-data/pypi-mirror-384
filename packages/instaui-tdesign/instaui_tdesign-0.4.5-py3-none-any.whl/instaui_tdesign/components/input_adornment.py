from __future__ import annotations
import typing
from ._base_element import BaseElement


class InputAdornment(BaseElement):
    def __init__(
        self,
        *,
        append: typing.Optional[str] = None,
        prepend: typing.Optional[str] = None,
    ):
        super().__init__("t-input-adornment")
        self.props({"append": append, "prepend": prepend})
