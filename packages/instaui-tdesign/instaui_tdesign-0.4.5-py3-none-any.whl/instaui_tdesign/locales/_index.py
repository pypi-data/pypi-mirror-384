import importlib
from typing import Dict
from instaui_tdesign.types import TLocale


class LazyLocaleDict:
    def __init__(self):
        self._locale_map = {}

    def get(self, key: str):
        key = key.lower().replace("-", "_")

        if key not in self._locale_map:
            self._locale_map[key] = self._load_locale(key)
        return self._locale_map[key]

    def _load_locale(self, key: str):
        module_name = key
        try:
            module = importlib.import_module(f"instaui_tdesign.locales.{module_name}")
            return module.locale

        except ImportError:
            raise ImportError(f"Cannot import module {module_name}")


_locale_dict = LazyLocaleDict()


def get_locale(locale: TLocale) -> Dict:
    return _locale_dict.get(locale)
