import os
from typing import Any
from typing import Dict
from typing import Optional

from ...id12.converter import Id12Hdf5ToAsciiConverter
from .. import EWOKS_RESULTS_DIR


class DemoId12Hdf5ToSpecConverter(Id12Hdf5ToAsciiConverter):
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        **deprecated_defaults: Dict[str, Any],
    ) -> None:
        defaults = self._merge_defaults(deprecated_defaults, defaults)

        root_dir = os.path.join(EWOKS_RESULTS_DIR, "id12", "inhouse")
        defaults.setdefault(
            "external_proposal_outdir", os.path.join(root_dir, "EXTERNAL")
        )
        defaults.setdefault(
            "inhouse_proposal_outdir", os.path.join(root_dir, "INHOUSE2")
        )
        defaults.setdefault("test_proposal_outdir", os.path.join(root_dir, "NOBACKUP"))

        super().__init__(config=config, defaults=defaults)
