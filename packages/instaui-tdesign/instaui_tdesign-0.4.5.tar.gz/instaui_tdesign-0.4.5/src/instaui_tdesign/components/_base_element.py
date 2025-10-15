from instaui import custom
from instaui_tdesign import consts
from instaui.dependencies.plugin_dependency import register_plugin


class BaseElement(custom.element):
    def __init__(self, tag: str):
        super().__init__(tag)
        _register_tdesign()


def _register_tdesign():
    register_plugin(
        "InstauiTDesign",
        esm=consts.instaui_tdesign_esm_js,
        externals={
            "tdesign-vue-next": consts.tdesign_esm_js,
        },
        css=[consts.tdesign_css, consts.instaui_tdesign_css],
    )
