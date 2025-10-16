from __future__ import annotations

from collections import OrderedDict
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ...persistent.parameters import ParameterInfo
from .bm_energy_calculation import BMEnergyCalculation


class WigglerEnergyCalculation(
    BMEnergyCalculation,
    parameters=[
        ParameterInfo("attenuators_names", category="attenuators"),
        ParameterInfo("fixed_elements", category="attenuators"),
        ParameterInfo("order", category="attenuators"),
        ParameterInfo("queue", category="workflows"),
        ParameterInfo("prompt_set_energy", category="handle_result"),
        ParameterInfo("plot", category="plot"),
        ParameterInfo("beam_energy_gev", category="source_configuration"),
        ParameterInfo("current_a", category="source_configuration"),
        ParameterInfo("phot_energy_min", category="source_configuration"),
        ParameterInfo("phot_energy_max", category="source_configuration"),
        ParameterInfo("npoints", category="source_configuration"),
        ParameterInfo("log_choice", category="source_configuration"),
        ParameterInfo("wig_field", category="source_configuration"),  # FIELD
        ParameterInfo("wig_nperiods", category="source_configuration"),  # NPERIODS
        ParameterInfo("wig_ulambda_m", category="source_configuration"),  # ULAMBDA (m)
        ParameterInfo("wig_k", category="source_configuration"),  # K
        ParameterInfo(
            "wig_ntrajpoints", category="source_configuration"
        ),  # NTRAJPOINTS
        ParameterInfo("wig_file", category="source_configuration"),  # FILE (dump) or ""
        ParameterInfo("wig_slit_flag", category="source_configuration"),  # SLIT_FLAG
        ParameterInfo("wig_slit_d_m", category="source_configuration"),  # SLIT_D (m)
        ParameterInfo("wig_slit_ny", category="source_configuration"),  # SLIT_NY
        ParameterInfo(
            "wig_slit_width_h_mm", category="source_configuration"
        ),  # SLIT_WIDTH_H_MM
        ParameterInfo(
            "wig_slit_height_v_mm", category="source_configuration"
        ),  # SLIT_HEIGHT_V_MM
        ParameterInfo(
            "wig_slit_center_h_mm", category="source_configuration"
        ),  # SLIT_CENTER_H_MM
        ParameterInfo(
            "wig_slit_center_v_mm", category="source_configuration"
        ),  # SLIT_CENTER_V_MM
        ParameterInfo(
            "wig_shift_x_flag", category="source_configuration"
        ),  # SHIFT_X_FLAG
        ParameterInfo(
            "wig_shift_x_value_m", category="source_configuration"
        ),  # SHIFT_X_VALUE (m)
        ParameterInfo(
            "wig_shift_betax_flag", category="source_configuration"
        ),  # SHIFT_BETAX_FLAG
        ParameterInfo(
            "wig_shift_betax_value", category="source_configuration"
        ),  # SHIFT_BETAX_VALUE (rad)
        ParameterInfo(
            "wig_traj_resampling_factor", category="source_configuration"
        ),  # TRAJ_RESAMPLING_FACTOR
        ParameterInfo(
            "wig_slit_points_factor", category="source_configuration"
        ),  # SLIT_POINTS_FACTOR
    ],
):
    """Submit the **Wiggler** workflow and (optionally) plot in Flint.
    Inherits common logic from BMEnergyCalculation (devices, fixed elements, plotting).
    """

    _HIDE_PARAMS = {"trigger_at", "Enabled"}

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        **deprecated_defaults: Dict[str, Any],
    ):
        defaults = self._merge_defaults(deprecated_defaults, defaults)
        defaults.update(
            {
                "attenuators_names": "att1,att2,att3,att4,att5",
                "queue": "online",
                "order": None,
                "beam_energy_gev": 6.0,  # GeV
                "current_a": 0.2,  # A (converted to mA for the task)
                "phot_energy_min": 100.0,  # eV
                "phot_energy_max": 800000.0,  # eV
                "npoints": 4000,
                "log_choice": 1,
                "wig_field": 1,
                "wig_nperiods": 1,
                "wig_ulambda_m": 0.15,
                "wig_k": 22.591,
                "wig_ntrajpoints": 101,
                "wig_file": "",
                "wig_slit_flag": 1,
                "wig_slit_d_m": 56.5,
                "wig_slit_ny": 101,
                "wig_slit_width_h_mm": 10.0,
                "wig_slit_height_v_mm": 5.0,
                "wig_slit_center_h_mm": 0.0,
                "wig_slit_center_v_mm": 0.0,
                "wig_shift_x_flag": 1,
                "wig_shift_x_value_m": -0.002385,
                "wig_shift_betax_flag": 5,
                "wig_shift_betax_value": 0.005,
                "wig_traj_resampling_factor": 10000.0,
                "wig_slit_points_factor": 3.0,
            }
        )
        super().__init__(config=config, defaults=defaults)

    def get_workflow(self) -> dict:
        """Wire ComputeWigglerSpectrum -> ApplyAttenuators -> SpectrumStats."""
        return {
            "graph": {"id": "bm_attenuation_wiggler", "schema_version": "1.1"},
            "nodes": [
                {
                    "id": "compute",
                    "label": "compute_wiggler_spectrum",
                    "task_type": "class",
                    "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                },
                {
                    "id": "attenuate",
                    "label": "apply_attenuators",
                    "task_type": "class",
                    "task_identifier": "ewokstomo.tasks.energycalculation.ApplyAttenuators",
                },
                {
                    "id": "stats",
                    "label": "spectrum_stats",
                    "task_type": "class",
                    "task_identifier": "ewokstomo.tasks.energycalculation.SpectrumStats",
                },
            ],
            "links": [
                {
                    "source": "compute",
                    "target": "attenuate",
                    "data_mapping": [
                        {"source_output": "energy_eV", "target_input": "energy_eV"},
                        {
                            "source_output": "spectral_power",
                            "target_input": "spectral_power",
                        },
                        {"source_output": "flux", "target_input": "flux"},
                    ],
                },
                {
                    "source": "attenuate",
                    "target": "stats",
                    "data_mapping": [
                        {"source_output": "energy_eV", "target_input": "energy_eV"},
                        {
                            "source_output": "attenuated_spectral_power",
                            "target_input": "attenuated_spectral_power",
                        },
                        {
                            "source_output": "attenuated_flux",
                            "target_input": "attenuated_flux",
                        },
                    ],
                },
            ],
        }

    def _build_submit_inputs(self) -> List[dict]:
        devices = self._resolve_devices()
        att_layers, _ = self._build_attenuators_from_devices(devices)
        fixed_layers = self._build_fixed_elements()

        merged = OrderedDict()
        merged.update(fixed_layers)
        merged.update(att_layers)

        order_value = (
            list(merged.keys()) if getattr(self, "order", None) is None else self.order
        )

        inputs: List[dict] = [
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "PHOT_ENERGY_MIN",
                "value": float(self.phot_energy_min),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "PHOT_ENERGY_MAX",
                "value": float(self.phot_energy_max),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "NPOINTS",
                "value": int(self.npoints),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "ENERGY",
                "value": float(self.beam_energy_gev),
            },  # GeV
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "CURRENT",
                "value": float(self.current_a) * 1000.0,
            },  # mA
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "FIELD",
                "value": int(self.wig_field),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "NPERIODS",
                "value": int(self.wig_nperiods),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "ULAMBDA",
                "value": float(self.wig_ulambda_m),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "K",
                "value": float(self.wig_k),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "NTRAJPOINTS",
                "value": int(self.wig_ntrajpoints),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "FILE",
                "value": str(self.wig_file),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SLIT_FLAG",
                "value": int(self.wig_slit_flag),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SLIT_D",
                "value": float(self.wig_slit_d_m),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SLIT_NY",
                "value": int(self.wig_slit_ny),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SLIT_WIDTH_H_MM",
                "value": float(self.wig_slit_width_h_mm),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SLIT_HEIGHT_V_MM",
                "value": float(self.wig_slit_height_v_mm),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SLIT_CENTER_H_MM",
                "value": float(self.wig_slit_center_h_mm),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SLIT_CENTER_V_MM",
                "value": float(self.wig_slit_center_v_mm),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SHIFT_X_FLAG",
                "value": int(self.wig_shift_x_flag),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SHIFT_X_VALUE",
                "value": float(self.wig_shift_x_value_m),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SHIFT_BETAX_FLAG",
                "value": int(self.wig_shift_betax_flag),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SHIFT_BETAX_VALUE",
                "value": float(self.wig_shift_betax_value),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "TRAJ_RESAMPLING_FACTOR",
                "value": float(self.wig_traj_resampling_factor),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "SLIT_POINTS_FACTOR",
                "value": float(self.wig_slit_points_factor),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeWigglerSpectrum",
                "name": "LOG_CHOICE",
                "value": int(self.log_choice),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ApplyAttenuators",
                "name": "attenuators",
                "value": merged,
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ApplyAttenuators",
                "name": "order",
                "value": order_value,
            },
        ]
        return inputs
