from typing import Optional, Union, Literal
from instaui import ui
from instaui_tdesign.types import TLocale, TCustomizeLocale
from instaui_tdesign._settings import configure
from instaui_tdesign import consts
from instaui_tdesign.components.icon import _reset_prefix


def use(
    *,
    locale: Optional[Union[TLocale, TCustomizeLocale]] = None,
    theme: Optional[
        Literal["default", "green", "violet", "orange", "blue", "rose", "amber", "teal"]
    ] = None,
    icon_prefix: Optional[str] = None,
):
    """Use tdesign ui.

    Args:
        locale (ui.TMaybeRef[Union[TLocale, TCustomizeLocale]], optional): The locale of tdesign ui.
        theme (Optional[Literal["default", "green", "violet"]], optional): The theme of tdesign ui. Defaults to `default`.
        icon_prefix (Optional[str], optional): The prefix of icon name. Defaults to `tdesign`.

    Examples:
    .. code-block:: python
        from instaui import ui
        import instaui_tdesign as td

        td.use(theme="violet", locale="en-US")

        @ui.page("/")
        def index_page():
            td.input(placeholder="input")
    """

    if locale:
        configure(locale=locale)
    if theme:
        ui.add_css_link(consts.THEME_CSS_DIR / f"theme-{theme}.css")
    if icon_prefix:
        _reset_prefix(icon_prefix)
