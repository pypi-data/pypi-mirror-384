from typing import Any, Dict, Optional
from ._base_element import BaseElement


class ConfigProvider(BaseElement):
    def __init__(
        self,
        *,
        globalConfig: Optional[Dict[str, Any]] = None,
    ):
        super().__init__("t-config-provider")
        self.props({"globalConfig": globalConfig})
