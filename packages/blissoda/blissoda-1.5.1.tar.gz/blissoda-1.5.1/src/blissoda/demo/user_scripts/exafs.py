from esrf_pathlib import ESRFPath

from blissoda.bliss_globals import setup_globals
from blissoda.demo import testing
from blissoda.demo.processors.exafs import DemoExafsProcessor
from blissoda.import_utils import unavailable_module

try:
    from bliss.physics import units
except ImportError as ex:
    units = unavailable_module(ex)


exafs_processor = DemoExafsProcessor()
# exafs_processor.refresh_period = 0.5


def exafs_demo(nrepeats: int = None, fast: bool = True):
    if nrepeats is None:
        nrepeats = exafs_processor.max_scans + 1
    for _ in range(nrepeats):
        test_exafs_scan(fast=fast)


@testing.integration_test
def test_exafs_scan(fast: bool = True):
    # Prepare scan
    if fast:
        e0 = 8950  # eV
        e1 = 9200  # eV
        step_size = 3.0  # eV
    else:
        e0 = 8800  # eV
        e1 = 9600  # eV
        step_size = 0.5  # eV

    npoints = int((e1 - e0) / step_size)
    intervals = npoints - 1

    from_unit = "eV"
    to_unit = exafs_processor.counters["energy_unit"]

    e0 = (e0 * units.ur(from_unit)).to(to_unit).magnitude
    e1 = (e1 * units.ur(from_unit)).to(to_unit).magnitude
    scan = setup_globals.ascan(
        setup_globals.energy, e0, e1, intervals, 0.01, setup_globals.mu, run=False
    )

    # Processor is in charge of the scan lifecycle
    exafs_processor.run(scan)

    # Validate results
    scan_number = scan.scan_info["scan_nb"]
    raw_dataset_file = ESRFPath(scan.scan_info["filename"])

    testing.wait_workflows()
    _assert_flint_plots_exist(
        exafs_processor, f"{raw_dataset_file.stem}: {scan_number}.1"
    )
    _assert_files_exist(raw_dataset_file.processed_dataset_file, scan_number, npoints)


@testing.demo_assert("Check EXAFS Flint plot {scan_label}")
def _assert_flint_plots_exist(exafs_processor, scan_label):
    exafs_plot = exafs_processor._plotter._get_plot()
    scan_labels = exafs_plot.get_scans()

    if len(scan_labels) > exafs_processor.max_scans:
        raise AssertionError(
            f"{len(scan_labels)} scans plotted exceeds the maximum of {exafs_processor.max_scans}"
        )

    if scan_label not in scan_labels:
        raise AssertionError(f"{scan_label!r} not in {scan_labels}")


@testing.demo_assert("Check EXAFS workflow results for scan #{scan_number}")
def _assert_files_exist(filename, scan_number, npoints):
    if not filename.exists():
        raise FileNotFoundError(str(filename))

    testing.assert_hdf5_dataset_exists(
        filename, f"/{scan_number}.1/measurement/mu", (npoints,)
    )
    testing.assert_hdf5_dataset_exists(
        filename, f"/{scan_number}.1/measurement/energy", (npoints,)
    )
