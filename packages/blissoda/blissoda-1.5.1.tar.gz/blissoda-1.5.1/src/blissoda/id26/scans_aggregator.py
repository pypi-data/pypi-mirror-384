from __future__ import annotations

import json
import logging
import os
from typing import Any

from ..import_utils import unavailable_module

try:
    import gevent
except ImportError as ex:
    gevent = unavailable_module(ex)
import numpy as np
from ewoksjob.client import get_future
from ewoksjob.client import submit

from blissoda.resources import resource_filename

from ..bliss_globals import current_session  # type: ignore
from ..flint import WithFlintAccess
from ..persistent.parameters import ParameterInfo
from ..processor import BaseProcessor
from ..processor import BlissScanType  # type: ignore
from .plots import AggregatedScansPlot

logger = logging.getLogger(__name__)


class ScansAggregator(
    BaseProcessor,
    parameters=[
        ParameterInfo("workflow", category="workflows"),
        ParameterInfo("data_mappings", category="workflows"),
        ParameterInfo("filename", category="workflows"),
        ParameterInfo("start_scan_id", category="workflows"),
        ParameterInfo("stop_scan_id", category="workflows"),
        ParameterInfo("aggregation_mode", category="workflows"),
        ParameterInfo("use_daxs", category="workflows"),
    ],
):
    DEFAULT_PARAMETERS = {
        "workflow": resource_filename("id26", "scans_aggregator.json"),
        "data_mappings": {
            "x": ".1/measurement/elapsed_time",
            "signal": ".1/measurement/sim_gaussian_1",
        },
        "filename": None,
        "start_scan_id": None,
        "stop_scan_id": None,
        "aggregation_mode": "fraction of sums",
        "use_daxs": True,
        "trigger_at": "END",
        "_enabled": False,
        "_clear_plot": True,
    }

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        defaults: dict[str, Any] | None = None,
        **deprecated_defaults: dict[str, Any],
    ) -> None:
        defaults = self._merge_defaults(deprecated_defaults, defaults)

        for parameter, value in self.DEFAULT_PARAMETERS.items():
            defaults.setdefault(parameter, value)

        super().__init__(config=config, defaults=defaults)

        self.handler = AggregatedScansHandler()

    def reset(self):
        for parameter, value in self.DEFAULT_PARAMETERS.items():
            if parameter == "_enabled" and self._enabled:
                self.disable()  # Only disable if currently enabled.
            elif parameter == "data_mappings":
                continue  # Do not reset data mappings
            else:
                setattr(self, parameter, value)
        self.handler.clear()

    def _get_current_scan_id(self) -> None | int:
        if current_session is None:
            raise ValueError("No current session available to get the scan from.")
        try:
            scan = current_session.scans[-1]
        except (AttributeError, IndexError):
            raise ValueError("No scans found in the current session.")

        scan_id = scan.scan_info["scan_nb"]
        if not isinstance(scan_id, int):
            raise ValueError("The id of the current scan is not a valid integer.")
        return scan_id

    def _get_start_scan_id(self) -> None | int:
        return self._get_parameter("start_scan_id")  # type: ignore

    def _set_start_scan_id(self, value: None | int) -> None:
        if value is None:
            self._set_parameter("start_scan_id", None)
            return
        if value < 0:
            current_scan_id = self._get_current_scan_id()
            if not isinstance(current_scan_id, int):
                raise ValueError(
                    "The id of the current scan must be be a valid integer before"
                    " using negative start_scan_id."
                )
            value = value + current_scan_id + 1
        if value == 0:
            raise ValueError("The start_scan_id cannot be zero.")
        self._set_parameter("start_scan_id", value)

    def _get_stop_scan_id(self) -> None | int:
        return self._get_parameter("stop_scan_id")  # type: ignore

    def _set_stop_scan_id(self, value: None | int) -> None:
        if value is None:
            self._set_parameter("stop_scan_id", None)
            return
        if value < 0:
            current_scan_id = self._get_current_scan_id()
            if not isinstance(current_scan_id, int):
                raise ValueError(
                    "The id of the current scan must be be a valid integer before"
                    " using negative stop_scan_id."
                )
            value = value + current_scan_id + 1
        if value == 0:
            raise ValueError("The stop_scan_id cannot be zero.")
        self._set_parameter("stop_scan_id", value)

    def _get_workflow(self) -> dict:
        with open(self.workflow) as wf:
            return json.load(wf)

    def _get_workflow_inputs(self, scan) -> list:
        if scan is not None:
            current_scan_id = self._get_current_scan_id()
            if self._get_start_scan_id() is None:
                self._set_start_scan_id(current_scan_id)
            self._set_stop_scan_id(current_scan_id)

        return [
            {
                "name": "data_mappings",
                "value": dict(self.data_mappings),
            },
            {
                "name": "filename",
                "value": self._get_filename(scan),
            },
            {
                "name": "start_scan_id",
                "value": self._get_parameter("start_scan_id"),
            },
            {
                "name": "stop_scan_id",
                "value": self._get_parameter("stop_scan_id"),
            },
            {
                "name": "aggregation_mode",
                "value": self._get_parameter("aggregation_mode"),
            },
            {
                "name": "use_daxs",
                "value": self._get_parameter("use_daxs"),
            },
        ]

    def _get_filename(self, scan=None) -> str:
        if self.filename is not None:
            return self.filename

        if scan is not None:
            filename = scan.scan_info.get("filename")
            if filename is not None:
                self.filename = filename
                return filename
            else:
                raise ValueError("Scan has no filename.")

        if current_session is None:
            raise ValueError("No current session available to get the filename from.")

        return current_session.scan_saving.filename

    def _get_processed_data_path(self) -> str:
        if self.filename is None:
            raise ValueError("Failed to get processed data path.")

        stem = os.path.splitext(os.path.basename(self.filename))[0]

        if current_session is not None:
            scan_saving = current_session.scan_saving
            root = os.path.join(
                scan_saving.base_path,
                scan_saving.proposal_dirname,
                scan_saving.beamline,
                scan_saving.proposal_session_name,
                "PROCESSED_DATA",
            )
        else:
            root = ""

        start_scan_id = self._get_start_scan_id()
        stop_scan_id = self._get_stop_scan_id()

        return os.path.join(
            root, f"{stem}_aggregated_scans_{start_scan_id}_to_{stop_scan_id}.dat"
        )

    def _trigger_workflow_on_new_scan(self, scan: BlissScanType | None) -> dict | None:
        workflow = self._get_workflow()
        workflow_inputs = self._get_workflow_inputs(scan)

        future = submit(
            args=(workflow,),
            kwargs={"inputs": workflow_inputs, "outputs": [{"all": False}]},
        )

        clear_plot = self._get_parameter("_clear_plot")
        # Consolidate the workflow inputs into a single dictionary.
        workflow_inputs = {
            workflow_input["name"]: workflow_input["value"]
            for workflow_input in workflow_inputs
        }
        self.handler.handle_workflow_result(
            future.task_id, clear_plot=clear_plot, workflow_inputs=workflow_inputs
        )

    def __call__(
        self,
        start_scan_id: int,
        stop_scan_id: int,
        clear_plot: bool = True,
        save_txt: bool = False,
    ) -> None:
        if start_scan_id > stop_scan_id:
            logger.warning(
                f"Invalid scan indices; the start_scan_id ({start_scan_id}) "
                f"should be smaller than the stop_scan_id ({stop_scan_id})."
            )
            return

        # Temporarily set the scan ids for the workflow trigger.
        prev_start_scan_id = self._get_start_scan_id()
        prev_stop_scan_id = self._get_stop_scan_id()

        self._set_start_scan_id(start_scan_id)
        self._set_stop_scan_id(stop_scan_id)

        if clear_plot:
            self._set_parameter("_clear_plot", True)
        else:
            self._set_parameter("_clear_plot", False)

        try:
            self._trigger_workflow_on_new_scan(None)
        except Exception as e:
            logger.warning(e, exc_info=True)

        if save_txt:
            result = self.handler.get_result()
            if result is None:
                logger.warning("No aggregated data available to save.")
                return
            x = result["measurement"]["x"]
            signal = result["measurement"]["signal"]
            filename = self._get_processed_data_path()
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            np.savetxt(filename, np.column_stack((x, signal)), header="x\tsignal")
            print(f"Data saved to {filename}.")

        # Restore the previous scan ids.
        self._set_start_scan_id(prev_start_scan_id)
        self._set_stop_scan_id(prev_stop_scan_id)


class AggregatedScansHandler(WithFlintAccess):
    def __init__(self) -> None:
        super().__init__()
        self._workflow_inputs = None
        self._result = None

    def clear(self):
        plot = self._get_plot()
        plot.submit("clear")
        plot.xlabel = "X"
        plot.ylabel = "Y"
        plot.title = ""

    def handle_workflow_result(self, *args, **kwargs) -> None:
        """Handle workflow result in a background task to recover data."""
        gevent.spawn(self._handle_workflow_result, *args, **kwargs)

    def _handle_workflow_result(
        self, task_id, timeout: int = 60, clear_plot: bool = True, workflow_inputs=None
    ) -> None:
        logger.info(f"Recovering processed data for task {task_id}")
        try:
            result = get_future(task_id).get(timeout=timeout)
            if result:
                self._result = result
                # Merge workflow inputs back into the result for reference.
                self._workflow_inputs = workflow_inputs
                self.plot_data(clear_plot=clear_plot)
            else:
                self._result = None
        except Exception as e:
            logger.exception(e)
            self._result = None

    def _get_plot(self, plot_id="Aggregated Scans", plot_cls=AggregatedScansPlot):
        return super()._get_plot(plot_id, plot_cls)

    def _get_filename(self):
        if self._workflow_inputs is None:
            return ""
        filename = self._workflow_inputs.get("filename", "")
        return filename

    def _get_axes_labels(self) -> dict[str, str]:
        axes_labels = {"x": "X", "y": "Y"}

        if not self._workflow_inputs:
            return axes_labels

        data = self._workflow_inputs.get("data_mappings", {})
        if not data:
            return axes_labels

        if "x" in data:
            axes_labels["x"] = data["x"].split("/")[-1]

        if "signal" in data:
            axes_labels["y"] = data["signal"].split("/")[-1]
            if "monitor" in data:
                axes_labels["y"] += " / " + data["monitor"].split("/")[-1]

        return axes_labels

    def get_result(self) -> dict[str, Any] | None:
        return self._result

    def plot_data(self, clear_plot: bool = True):
        if not self._result or self._workflow_inputs is None:
            return

        plot = self._get_plot()
        if clear_plot:
            plot.submit("clear")

        scans = self._result["scans"]
        for scan_id in scans:
            color = "gray"
            legend = f"Scan {scan_id}"

            if scan_id == max(scans):
                color = "black"
                legend = legend + " (last)"

            plot.add_curve(
                scans[scan_id]["x"],
                scans[scan_id]["signal"],
                legend=legend,
                linestyle="-",
                color=color,
            )

        measurement = self._result["measurement"]
        plot.add_curve(
            measurement["x"],
            measurement["signal"],
            legend=self._workflow_inputs["aggregation_mode"].capitalize(),
            linestyle="-",
            color="red",
            linewidth=2,
        )

        filename = self._get_filename()
        plot.title = f"{filename}"

        axes_labels = self._get_axes_labels()
        plot.xlabel = axes_labels["x"]
        plot.ylabel = axes_labels["y"]
