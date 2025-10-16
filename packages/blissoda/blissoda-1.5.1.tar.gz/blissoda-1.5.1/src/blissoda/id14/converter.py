"""User API for HDF5 conversion on the Bliss repl"""

import os
import shutil
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ewoksjob.client import submit

from ..bliss_globals import current_session
from ..persistent.parameters import ParameterInfo
from ..processor import BaseProcessor
from ..processor import BlissScanType
from ..resources import resource_filename
from ..utils import directories


class Id14Hdf5ToSpecConverter(
    BaseProcessor,
    parameters=[
        ParameterInfo(
            "workflow_for_mca", category="workflows", deprecated_names=["workflow"]
        ),
        ParameterInfo("workflow_for_counters", category="workflows"),
        ParameterInfo("retry_timeout", category="parameters"),
        ParameterInfo("counter_names", category="parameters"),
        ParameterInfo("queue", category="workflows", deprecated_names=["worker"]),
    ],
):
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        **deprecated_defaults: Dict[str, Any],
    ) -> None:
        defaults = self._merge_defaults(deprecated_defaults, defaults)

        self._workflow_for_mca = resource_filename("id14", "spec_convert_mca.json")
        self._workflow_for_counters = resource_filename(
            "id14", "spec_convert_counters.json"
        )

        # For integration tests
        self._future_for_mca = None
        self._future_for_counters = None

        defaults.setdefault("trigger_at", "END")
        defaults.setdefault("retry_timeout", 60)
        defaults.setdefault("queue", "celery")
        defaults.setdefault("workflow_for_mca", self._workflow_for_mca)
        defaults.setdefault("workflow_for_counters", self._workflow_for_counters)
        defaults.setdefault("counter_names", [])

        super().__init__(config=config, defaults=defaults)

        # Remove the old default of "PREPARED":
        if self.trigger_at != "END":
            self.trigger_at = "END"

    def enable_slurm(self):
        self.queue = "slurm"

    def disable_slurm(self):
        self.queue = "celery"

    def on_new_scan_metadata(self, scan: BlissScanType) -> None:
        if self._scan_requires_mca_conversion(scan):
            self.workflow_for_mca = self._copy_workflow(
                scan, self.workflow_for_mca, self._workflow_for_mca
            )
            kwargs = self._get_mca_submit_arguments(scan)
            self._future_for_mca = submit(
                args=(self.workflow_for_mca,), kwargs=kwargs, queue=self.queue
            )

        if self._scan_requires_asc_conversion(scan):
            self.workflow_for_counters = self._copy_workflow(
                scan, self.workflow_for_counters, self._workflow_for_counters
            )
            kwargs = self._get_counters_submit_arguments(scan)
            self._future_for_counters = submit(
                args=(self.workflow_for_counters,), kwargs=kwargs, queue=self.queue
            )

    def _scan_requires_mca_conversion(self, scan: BlissScanType) -> bool:
        return scan.scan_info.get("type", "") == "MCA Acq"

    def _scan_requires_asc_conversion(self, scan: BlissScanType) -> bool:
        return scan.scan_info.get("name", "").endswith("_nisscan")

    def _trigger_workflow_on_new_scan(self, scan: BlissScanType) -> None:
        self.on_new_scan_metadata(scan)

    def _get_mca_submit_arguments(self, scan: BlissScanType) -> dict:
        return {"inputs": self._get_inputs_for_mca(scan), "outputs": [{"all": False}]}

    def _get_inputs_for_mca(self, scan: BlissScanType) -> List[dict]:
        task_identifier = "Hdf5ToSpec"

        filename = self._get_filename(scan)
        output_filename = self._workflow_destination(scan, ".mca")
        scan_nb = scan.scan_info.get("scan_nb")

        inputs = [
            {
                "task_identifier": task_identifier,
                "name": "filename",
                "value": filename,
            },
            {
                "task_identifier": task_identifier,
                "name": "output_filename",
                "value": output_filename,
            },
            {
                "task_identifier": task_identifier,
                "name": "scan_numbers",
                "value": [scan_nb],
            },
            {
                "task_identifier": task_identifier,
                "name": "retry_timeout",
                "value": self.retry_timeout,
            },
        ]

        # Scan metadata published in id14.McaAcq.McaAcq.save
        calibration = scan.scan_info.get("instrument", dict()).get("calibration")
        if calibration:
            mca_calibration = calibration["a"], calibration["b"], 0
            inputs.append(
                {
                    "task_identifier": task_identifier,
                    "name": "mca_calibration",
                    "value": mca_calibration,
                }
            )

        return inputs

    def _get_counters_submit_arguments(
        self, scan: BlissScanType, mca: bool = True
    ) -> dict:
        return {
            "inputs": self._get_inputs_for_counters(scan),
            "outputs": [{"all": False}],
        }

    def _get_inputs_for_counters(self, scan: BlissScanType) -> List[dict]:
        task_identifier = "Hdf5ToSpec2"

        filename = self._get_filename(scan)
        output_filename = self._workflow_destination(scan, ".asc")
        scan_nb = scan.scan_info.get("scan_nb")

        inputs = [
            {
                "task_identifier": task_identifier,
                "name": "filename",
                "value": filename,
            },
            {
                "task_identifier": task_identifier,
                "name": "output_filename",
                "value": output_filename,
            },
            {
                "task_identifier": task_identifier,
                "name": "scan_numbers",
                "value": [scan_nb],
            },
            {
                "task_identifier": task_identifier,
                "name": "retry_timeout",
                "value": self.retry_timeout,
            },
            {
                "task_identifier": task_identifier,
                "name": "counter_names",
                "value": self.counter_names,
            },
        ]
        return inputs

    def _get_filename(self, scan: BlissScanType) -> str:
        filename = scan.scan_info.get("filename")
        if filename:
            return filename
        return current_session.scan_saving.filename

    def _workflow_destination(self, scan: BlissScanType, extension: str) -> str:
        filename = self._get_filename(scan)
        root = directories.get_processed_dir(filename)
        stem = os.path.splitext(os.path.basename(filename))[0]
        basename = f"{stem}{extension}"
        return os.path.join(root, basename)

    def _copy_workflow(
        self, scan: BlissScanType, src_file: str, default_src_file: str
    ) -> Optional[str]:
        """Ensure the workflow is located the proposal directory for user reference and worker accessibility."""
        if not os.path.isfile(src_file):
            src_file = default_src_file

        dataset_filename = self._get_filename(scan)
        workflow_directory = directories.get_workflows_dir(dataset_filename)
        dst_file = os.path.join(workflow_directory, os.path.basename(src_file))

        if not os.path.exists(dst_file):
            os.makedirs(workflow_directory, exist_ok=True)
            shutil.copyfile(src_file, dst_file)

        return dst_file
