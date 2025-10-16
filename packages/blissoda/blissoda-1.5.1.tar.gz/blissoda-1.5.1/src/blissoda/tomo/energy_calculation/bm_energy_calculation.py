from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from ewoksjob.client import submit

from ...flint import WithFlintAccess
from ...import_utils import unavailable_function
from ...persistent.parameters import ParameterInfo
from ...processor import BaseProcessor

try:
    from bliss.shell.getval import getval_yes_no
except ImportError as ex:
    getval_yes_no = unavailable_function(ex)

from .grid_plotter import GridPlot

try:
    from bliss import current_session
except ImportError:
    current_session = None


MATERIAL_TABLE = {
    # Aluminum
    "al": ("Al", 2.70),
    "aluminum": ("Al", 2.70),
    "aluminium": ("Al", 2.70),
    # Carbon family (choose the right one by key)
    "c": ("C", 2.26),
    "carbon": ("C", 2.26),
    "graphite": ("C", 2.26),
    # Glassy carbon (rods/blocks)
    "glassy carbon": ("C", 1.52),
    "glassy_carbon": ("C", 1.52),
    "glassy_carbon_bloc": ("C", 1.52),
    "glassy carbon bloc": ("C", 1.52),
    "glassy_carbon_block": ("C", 1.52),
    "glassy carbon block": ("C", 1.52),
    # Ambiguous “carbon block/bloc” — keep as graphite unless explicitly “glassy”
    "carbon bloc": ("C", 2.26),
    "carbon block": ("C", 2.26),
    # Carbon fibers (PAN-based typical bulk density)
    "carbon_fibers_5um": ("C", 1.80),
    "carbon ni fibers": ("C", 1.80),
    "carbon_ni_fibers": ("C", 1.80),
    # Beryllium
    "be": ("Be", 1.85),
    "beryllium": ("Be", 1.85),
    # Silicon
    "si": ("Si", 2.3296),
    "silicon": ("Si", 2.3296),
    # Silica / quartz
    "sio2": ("SiO2", 2.20),
    "silica": ("SiO2", 2.20),
    "silica b": ("SiO2", 2.20),
    "silica c": ("SiO2", 2.20),
    "sio2 b": ("SiO2", 2.20),
    "sio2 block": ("SiO2", 2.20),
    "sio2_block": ("SiO2", 2.20),
    "quartz": ("SiO2", 2.65),
    # Alumina / sapphire
    "al2o3": ("Al2O3", 3.98),
    "sapphire": ("Al2O3", 3.98),
    # Copper
    "cu": ("Cu", 8.96),
    "copper": ("Cu", 8.96),
    # Silver
    "ag": ("Ag", 10.49),
    "silver": ("Ag", 10.49),
    # Nickel
    "ni": ("Ni", 8.90),
    "nickel": ("Ni", 8.90),
    # Molybdenum
    "mo": ("Mo", 10.28),
    "molybdenum": ("Mo", 10.28),
    # Titanium
    "ti": ("Ti", 4.506),
    "titanium": ("Ti", 4.506),
    # Zirconium
    "zr": ("Zr", 6.52),
    "zirconium": ("Zr", 6.52),
    # Chromium
    "cr": ("Cr", 7.19),
    "chromium": ("Cr", 7.19),
    # Iron
    "fe": ("Fe", 7.874),
    "iron": ("Fe", 7.874),
    # Tungsten
    "w": ("W", 19.25),
    "tungsten": ("W", 19.25),
    # Gold
    "au": ("Au", 19.32),
    "gold": ("Au", 19.32),
    # Alloys / mixtures
    "brass": ("CuZn", 8.50),
    "lead_brass": ("Cu57Zn40.5Pb2.5", 8.70),
    "lead brass": ("Cu57Zn40.5Pb2.5", 8.70),
    # Polymers / resin (generic)
    "resin": ("C", 1.20),
    "resin lenses": ("C", 1.20),
    "resin_block": ("C", 1.20),
    "resin block": ("C", 1.20),
    # Air (dry, ~15°C, sea level)
    "air": ("Air", 0.001225),
    "free pass": ("Air", 0.001225),
}
_POS = re.compile(r"^\s*([A-Za-z]+)\s*([0-9]+(?:\.[0-9]+)?)\s*$")
_EMPTY = re.compile(
    r"^\s*(empty|out|open|none|0|free\s*pass(?:\s*\d+)?)\s*$", re.IGNORECASE
)
_ORDER_KEY_RE = re.compile(r"^(fix|att)\d+$")

_SYNONYMS = {
    "glassy carbon bloc": "glassy_carbon_bloc",
    "glassy_carbon_bloc": "glassy_carbon_bloc",
    "glassy carbon block": "glassy_carbon_block",
    "glassy_carbon_block": "glassy_carbon_block",
    "glassy carbon": "glassy carbon",
    "glassy_carbon": "glassy carbon",
    "carbon bloc": "carbon bloc",
    "carbon block": "carbon block",
    "carbon fibers 5um": "carbon_fibers_5um",
    "carbon_fibers_5um": "carbon_fibers_5um",
    "carbon ni fibers": "carbon_ni_fibers",
    "carbon_ni_fibers": "carbon_ni_fibers",
    "graphite": "graphite",
    "carbon": "carbon",
    "c": "c",
    "aluminum": "al",
    "aluminium": "al",
    "al": "al",
    "copper": "cu",
    "cu": "cu",
    "silica": "sio2",
    "silica b": "sio2",
    "silica c": "sio2",
    "quartz": "sio2",
    "sio2": "sio2",
    "sio": "sio2",
    "sio2 b": "sio2",
    "sio2 block": "sio2",
    "sio2_block": "sio2",
    "beryllium": "be",
    "be": "be",
    "silicon": "si",
    "si": "si",
    "sapphire": "al2o3",
    "al2o3": "al2o3",
    "silver": "ag",
    "ag": "ag",
    "gold": "au",
    "au": "au",
    "tungsten": "w",
    "w": "w",
    "nickel": "ni",
    "ni": "ni",
    "molybdenum": "mo",
    "mo": "mo",
    "titanium": "ti",
    "ti": "ti",
    "zirconium": "zr",
    "zr": "zr",
    "chromium": "cr",
    "cr": "cr",
    "iron": "fe",
    "fe": "fe",
    "brass": "brass",
    "lead_brass": "lead_brass",
    "lead brass": "lead_brass",
    "resin": "resin",
    "resin lenses": "resin",
    "resin_block": "resin",
    "resin block": "resin",
    "empty": "air",
    "air": "air",
    "free pass": "air",
}
_DESC_NUM = re.compile(r"([0-9]+(?:[.,][0-9]+)?)\s*(mm|um|µm|μm|cm|m)\b", re.IGNORECASE)
_UNIT_MM = {"mm": 1.0, "um": 1e-3, "µm": 1e-3, "μm": 1e-3, "cm": 10.0, "m": 1000.0}


def _to_mm(value: str, unit: Optional[str]) -> float:
    v = float(value.replace(",", "."))
    u = (unit or "").strip().lower()
    return v * _UNIT_MM[u] if u in _UNIT_MM else v


def _material_from_description(desc: str) -> Optional[str]:
    s = desc.lower()
    for k in sorted(_SYNONYMS.keys(), key=len, reverse=True):
        if re.search(rf"(?<![0-9A-Za-z]){re.escape(k)}(?![0-9A-Za-z])", s):
            return _SYNONYMS[k]
    return None


def _parse_description(desc: str) -> Optional[Tuple[str, float]]:
    if not desc:
        return None
    s = re.sub(r"\([^)]*\)", " ", desc)
    s = re.sub(r"\s+", " ", s).strip()
    num = _DESC_NUM.search(s)
    if not num:
        return None
    val, unit = num.groups()
    t_mm = _to_mm(val, unit)
    mat = _material_from_description(s)
    if mat in ("air", None):
        return None
    return mat, float(t_mm)


def _parse_from_positions_list(dev: Any) -> Optional[Tuple[str, float]]:
    plist = getattr(dev, "positions_list", None)
    label = str(getattr(dev, "position", "")).strip().lower()
    if not plist or not label:
        return None
    entry = next(
        (it for it in plist if str(it.get("label", "")).strip().lower() == label), None
    )
    if not entry:
        return None
    got = _parse_description(entry.get("description") or "")
    if not got:
        return None
    mat_key, t_mm = got
    if mat_key not in MATERIAL_TABLE:
        return None
    return mat_key, t_mm


def parse_position_string(position: Any) -> Tuple[Optional[str], float]:
    s = str(position)
    if _EMPTY.match(s):
        return None, 0.0
    m = _POS.match(s)
    if not m:
        raise ValueError(f"Unrecognized attenuator position format: {position!r}")
    code = m.group(1).lower()
    mm = m.group(2)
    thickness_mm = float(mm) if "." in mm else float(int(mm)) / 1000.0
    return code, thickness_mm


class BMEnergyPlotter(WithFlintAccess):
    """Reusable base for plotters that draw in Flint."""

    def __init__(self, *, unique_name: Optional[str] = None) -> None:
        super().__init__()
        self.unique_name = unique_name or self.__class__.__name__
        self._grid: Optional[GridPlot] = None

    @property
    def grid(self) -> GridPlot:
        if self._grid is None:
            self._grid = GridPlot(unique_name=self.unique_name)
        return self._grid

    def clear(self) -> None:
        if self._grid is not None:
            self._grid.clear()

    def _plot_in_flint(self, result: Dict[str, Any]) -> None:
        energy_eV = result.get("energy_eV")
        sp_src = result.get("spectral_power")
        sp_att = result.get("attenuated_spectral_power")
        flux_src = result.get("flux")
        flux_att = result.get("attenuated_flux")
        transmission = result.get("transmission")
        cumulated_power = result.get("cumulated_power")

        x_keV = energy_eV / 1e3
        g = self.grid
        g.set_layout(2, 2)

        # 1) Spectral power
        series_sp = [{"y": sp_src, "label": "Source", "color": "red"}]
        series_sp.append({"y": sp_att, "label": "Attenuated", "color": "green"})
        g.set_cell(
            0,
            0,
            x=x_keV,
            series=series_sp,
            title="Spectral Power (source (red) vs attenuated (green))",
            xlabel="Energy [keV]",
            ylabel="Spectral Power [W/eV]",
        )

        # 2) Flux
        series_flux = []
        series_flux.append(
            {"y": flux_src, "label": "Flux (source)", "color": "darkRed"}
        )
        series_flux.append(
            {"y": flux_att, "label": "Flux (attenuated)", "color": "darkGreen"}
        )
        g.set_cell(
            0,
            1,
            x=x_keV,
            series=series_flux,
            title="Flux (source (red) vs attenuated (green))",
            xlabel="Energy [keV]",
            ylabel="Flux [Phot/s/0.1%bw]",
        )

        # 3) Transmission
        g.set_cell(
            1,
            0,
            x=x_keV,
            series=[{"y": transmission, "label": "T", "color": "blue"}],
            title="Transmission vs Energy",
            xlabel="Energy [keV]",
            ylabel="Transmission",
        )

        # 4) Cumulated power
        g.set_cell(
            1,
            1,
            x=x_keV,
            series=[{"y": cumulated_power, "label": "Cumulated", "color": "black"}],
            title="Cumulated Power vs Energy",
            xlabel="Energy [keV]",
            ylabel="Cumulated Power [W]",
        )

    def plot(self, result: Dict[str, Any]) -> None:
        self._plot_in_flint(result)


class BMEnergyCalculation(
    BaseProcessor,
    parameters=[
        ParameterInfo("attenuators_names", category="attenuators"),
        ParameterInfo("fixed_elements", category="attenuators"),
        ParameterInfo("order", category="attenuators"),
        ParameterInfo("queue", category="workflows"),
        ParameterInfo("prompt_set_energy", category="handle_result"),
        ParameterInfo("plot", category="plot"),
        ParameterInfo("beam_energy_gev", category="source_configuration"),
        ParameterInfo("bfield_t", category="source_configuration"),
        ParameterInfo("current_a", category="source_configuration"),
        ParameterInfo("hor_div_mrad", category="source_configuration"),
        ParameterInfo("phot_energy_min", category="source_configuration"),
        ParameterInfo("phot_energy_max", category="source_configuration"),
        ParameterInfo("npoints", category="source_configuration"),
        ParameterInfo("log_choice", category="source_configuration"),
    ],
):
    """Submit the **BM** workflow and (optionally) plot in Flint via a plotter."""

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
                "beam_energy_gev": 6.0,
                "bfield_t": 0.8,
                "current_a": 0.2,
                "hor_div_mrad": 1.0,
                "phot_energy_min": 100.0,
                "phot_energy_max": 200000.0,
                "npoints": 2000,
                "log_choice": 1,
            }
        )
        BaseProcessor.__init__(self, config=config, defaults=defaults)
        self._plotter = BMEnergyPlotter(unique_name="Energy Calculation")

    def _info_categories(self) -> dict:
        cats = super()._info_categories()
        cats.pop("status", None)
        cats.pop("enabled", None)
        return cats

    def submit(self, save_workflow_to: Optional[str] = None):
        wf = self.get_workflow()
        submit_kwargs = self.get_submit_arguments()
        if save_workflow_to:
            p = Path(save_workflow_to)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(wf, indent=2))
            submit_kwargs["convert_destination"] = save_workflow_to
        future = submit(args=(wf,), kwargs=submit_kwargs, queue=self.queue)
        result = future.get()

        if self.plot and self._plotter is not None:
            self._plotter._plot_in_flint(result)

        mean_eV = self._extract_mean_energy_eV(result)
        if self.prompt_set_energy:
            if mean_eV is None:
                print("Calculated energy is: N/A.")
            else:
                mean_keV = mean_eV / 1e3
                if getval_yes_no(
                    f"Calculated energy is: {mean_keV:.3f} keV. Run ENERGY({mean_keV:.3f})? ",
                    default="no",
                ):
                    self._set_energy_eV(mean_eV)
        else:
            if mean_eV is not None:
                print(f"Calculated energy is: {mean_eV / 1e3:.3f} keV.")
        return

    def get_submit_arguments(self) -> dict:
        return {"inputs": self._build_submit_inputs(), "outputs": [{"all": True}]}

    def get_workflow(self) -> dict:
        return {
            "graph": {"id": "bm_attenuation_bm", "schema_version": "1.1"},
            "nodes": [
                {
                    "id": "compute",
                    "label": "compute_bm_spectrum",
                    "task_type": "class",
                    "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
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
                            "source_output": "attenuated_flux",
                            "target_input": "attenuated_flux",
                        },
                    ],
                },
            ],
        }

    def _resolve_devices(self) -> List[Any]:
        if current_session is None:
            raise RuntimeError("BLISS current_session is not available.")
        names = [n.strip() for n in str(self.attenuators_names).split(",") if n.strip()]
        sg = getattr(current_session, "setup_globals", current_session)
        return [getattr(sg, name) for name in names]

    def _build_attenuators_from_devices(
        self, devices: Iterable[Any]
    ) -> Tuple[Dict[str, Dict[str, float]], List[str]]:
        attenuators, order_keys = OrderedDict(), []
        for idx, dev in enumerate(devices, 1):
            parsed = _parse_from_positions_list(dev)
            code, t_mm = parsed if parsed else (None, 0.0)
            if (not code) or t_mm <= 0.0:
                element, density, t_mm = "Air", MATERIAL_TABLE["air"][1], 0.0
            else:
                element, density = MATERIAL_TABLE.get(code, (code.capitalize(), 1.0))
            key = f"att{idx}"
            order_keys.append(key)
            attenuators[key] = {
                "material": element,
                "thickness_mm": float(t_mm),
                "density_g_cm3": float(density),
            }
        return attenuators, order_keys

    def _build_submit_inputs(self) -> List[dict]:
        devices = self._resolve_devices()
        att_layers, _ = self._build_attenuators_from_devices(devices)
        fixed_layers = self._build_fixed_elements()

        merged = OrderedDict()
        merged.update(fixed_layers)
        merged.update(att_layers)

        order_value = list(merged.keys()) if self.order is None else self.order

        inputs: List[dict] = [
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "TYPE_CALC",
                "value": 0,
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "VER_DIV",
                "value": 0,
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "MACHINE_NAME",
                "value": "ESRF bending magnet",
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "RB_CHOICE",
                "value": 0,
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "MACHINE_R_M",
                "value": 25.0,
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "BFIELD_T",
                "value": float(self.bfield_t),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "BEAM_ENERGY_GEV",
                "value": float(self.beam_energy_gev),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "CURRENT_A",
                "value": float(self.current_a),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "HOR_DIV_MRAD",
                "value": float(self.hor_div_mrad),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "PHOT_ENERGY_MIN",
                "value": float(self.phot_energy_min),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "PHOT_ENERGY_MAX",
                "value": float(self.phot_energy_max),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "NPOINTS",
                "value": int(self.npoints),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "LOG_CHOICE",
                "value": int(self.log_choice),
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "PSI_MRAD_PLOT",
                "value": 1.0,
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "PSI_MIN",
                "value": -1.0,
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "PSI_MAX",
                "value": 1.0,
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "PSI_NPOINTS",
                "value": 500,
            },
            {
                "task_identifier": "ewokstomo.tasks.energycalculation.ComputeBMSpectrum",
                "name": "FILE_DUMP",
                "value": False,
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

    @staticmethod
    def _coerce_layer(entry: Dict[str, Any]) -> Dict[str, float]:
        material = str(entry.get("material", "")).strip()
        if not material:
            raise ValueError("fixed_elements entry missing 'material'")
        thickness_mm = float(entry.get("thickness_mm", 0.0))
        if "density_g_cm3" in entry:
            density = float(entry["density_g_cm3"])
        else:
            mkey = material.lower()
            density = MATERIAL_TABLE.get(mkey, (material, 1.0))[1]

        # Treat empty/air with <=0 mm as neutral layer
        if material.lower() in ("empty", "none", "air") and thickness_mm <= 0.0:
            material = "Air"
            thickness_mm = 0.0
            density = MATERIAL_TABLE["air"][1]

        return {
            "material": material,
            "thickness_mm": thickness_mm,
            "density_g_cm3": density,
        }

    def _build_fixed_elements(self) -> OrderedDict[str, Dict[str, float]]:
        fixed_src = dict(self.fixed_elements or {})
        fixed: "OrderedDict[str, Dict[str, float]]" = OrderedDict()
        gen_idx = 1
        for user_key, entry in fixed_src.items():
            layer = self._coerce_layer(entry)
            key = (
                user_key
                if isinstance(user_key, str) and _ORDER_KEY_RE.match(user_key)
                else f"fix{gen_idx}"
            )
            gen_idx += 1 if not (_ORDER_KEY_RE.match(str(user_key) or "")) else 0
            fixed[key] = layer
        return fixed

    @staticmethod
    def _extract_mean_energy_eV(result: dict) -> Optional[float]:
        v = (result.get("stats") or {}).get(
            "mean_energy_eV", result.get("mean_energy_eV")
        )
        return float(v) if v is not None else None

    def _set_energy_eV(self, energy_eV: float) -> None:
        if current_session is None:
            return
        sg = getattr(current_session, "setup_globals", current_session)
        ENERGY = getattr(sg, "ENERGY", None)
        if callable(ENERGY):
            ENERGY(float(energy_eV) / 1e3)
