from typing import Any
from typing import Dict
from typing import Optional

from ...bliss_globals import setup_globals
from ...exafs.processor import ExafsProcessor
from ...resources import resource_filename


class DemoExafsProcessor(ExafsProcessor):
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        **deprecated_defaults: Dict[str, Any],
    ) -> None:
        defaults = self._merge_defaults(deprecated_defaults, defaults)

        defaults.setdefault("workflow", resource_filename("exafs", "exafs.ows"))
        defaults.setdefault("_scan_type", "any")
        counters = defaults.setdefault("_counters", dict())

        if self._HAS_BLISS:
            energy_unit = setup_globals.energy.unit or "eV"
            counters.setdefault(
                "any",
                {
                    "mu_name": "mu",
                    "energy_name": "energy",
                    "energy_unit": energy_unit,
                },
            )

        super().__init__(config=config, defaults=defaults)

    def _scan_type_from_scan(self, scan) -> Optional[str]:
        return "any"

    def _multi_xas_scan(self, scan) -> bool:
        # Single scan are also considered "multi-scan" so the
        # data is split (eventhough there is nothing to split,
        # we will only have one scan) and saved in PROCESSED_DATA.
        return True

    def _multi_xas_subscan_size(self, scan) -> int:
        # The workflow will look an monotonicity of the energy
        # counter to figure this out.
        return 0
