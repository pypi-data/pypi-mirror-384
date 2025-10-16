from typing import Any
from typing import Dict
from typing import Optional

from ...wrappers.ewoks_macro import EwoksMacroHandler


class DemoEwoksMacroHandler(EwoksMacroHandler):
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        if defaults is None:
            defaults = {}
        defaults.setdefault("queue", "celery")
        super().__init__(config, defaults)
