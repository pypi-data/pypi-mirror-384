from pathlib import Path
from typing import Final
from instaui_tdesign import __version__


static_folder: Final = Path(__file__).parent / "static"

instaui_tdesign_css: Final = static_folder / "instaui-tdesign.css"
instaui_tdesign_esm_js: Final = static_folder / "instaui-tdesign.js"

tdesign_css: Final = static_folder / "tdesign.min.css"
tdesign_esm_js: Final = static_folder / "tdesign.min.js"

THEME_CSS_DIR: Final = Path(__file__).parent / "theme/css"


TDESIGN_VUE_ESM_JS_CDN: Final = f"https://cdn.jsdelivr.net/gh/instaui-python/instaui-tdesign@v{__version__}/tdesign-dist/tdesign.min.js"
TDESIGN_VUE_CSS_CDN: Final = f"https://cdn.jsdelivr.net/gh/instaui-python/instaui-tdesign@v{__version__}/tdesign-dist/tdesign.min.css"
