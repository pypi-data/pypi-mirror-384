from typing import get_args
from instaui import ui
from instaui_tdesign.types import TLocale
from instaui_tdesign.locales import get_locale


class Locale:
    def __init__(self, locale: TLocale):
        self._names = get_args(TLocale)
        self._current_name = ui.state(locale)

        @ui.computed(inputs=[self._current_name])
        def locale_data(name: TLocale):
            return get_locale(name)

        self._current_data = locale_data

    @property
    def all_names(self):
        return self._names

    @property
    def current_name(self):
        return self._current_name

    @property
    def current(self):
        return self._current_data


def use_locale(locale_name: TLocale):
    """Reactive language settings.

    Args:
        locale_name (TLocale):  The language name of the locale.

    Example:
    .. code-block:: python
        @ui.page("/")
        def index():
            locale = td.use_locale("zh-CN")
            td.select(locale.all_names, locale.current_name)

            with td.config_provider(locale=locale.current):
                td.pagination(
                    total=50, show_total=True, show_jumper=True, show_page_size=True
                )

    """
    return Locale(locale_name)
