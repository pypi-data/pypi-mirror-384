from typing import List

from ...id14.converter import Id14Hdf5ToSpecConverter
from ...import_utils import unavailable_type

try:
    from bliss.scanning.scan import Scan as BlissScanType
except ImportError as ex:
    BlissScanType = unavailable_type(ex)


class DemoId14Hdf5ToSpecConverter(Id14Hdf5ToSpecConverter):
    def _get_inputs_for_mca(self, scan: BlissScanType) -> List[dict]:
        inputs = super()._get_inputs_for_mca(scan)
        task_identifier = "Hdf5ToSpec"
        inputs.append(
            {
                "task_identifier": task_identifier,
                "name": "mca_counter",
                "value": "mca1_det0",
            }
        )
        return inputs

    def _scan_requires_mca_conversion(self, scan: BlissScanType) -> bool:
        return True

    def _scan_requires_asc_conversion(self, scan: BlissScanType) -> bool:
        return True
