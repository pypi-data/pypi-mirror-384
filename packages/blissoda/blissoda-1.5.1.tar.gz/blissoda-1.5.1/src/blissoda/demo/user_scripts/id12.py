import pathlib

from blissoda.bliss_globals import setup_globals
from blissoda.demo import testing
from blissoda.demo.processors.id12 import DemoId12Hdf5ToSpecConverter

id12_converter = DemoId12Hdf5ToSpecConverter()


def id12_demo(expo=0.2, npoints=10):
    for _ in range(2):
        test_id12_loopscan(expo=expo, npoints=npoints)


@testing.integration_fixture
def _id12():
    id12_converter.enable()
    yield id12_converter
    id12_converter.disable()


@testing.integration_test
def test_id12_loopscan(_id12: DemoId12Hdf5ToSpecConverter, expo=0.2, npoints=10):
    scan = setup_globals.loopscan(
        npoints,
        expo,
        setup_globals.diode1,
        setup_globals.diode2,
        setup_globals.mca1,
    )
    scan_number = scan.scan_info["scan_nb"]
    output_dir = pathlib.Path(_id12.output_dir(scan))
    _assert_spec_counter_file(_id12, output_dir, scan_number)


@testing.demo_assert("Check id12 SPEC file for scan #{scan_number}")
def _assert_spec_counter_file(
    _id12: DemoId12Hdf5ToSpecConverter, output_dir: pathlib.Path, scan_number: int
):
    result = _id12._future.result(timeout=10)
    base_names = result["output_filenames"]
    assert len(base_names) == 1
    subscan = 1
    for base_name in base_names:
        with open(output_dir / base_name, "r") as f:
            assert f"scan{scan_number:03d}_{subscan}" in base_name, base_name
            counters = f.readline().split("  ")
            for name in [
                "epoch",
                "elapsed_time",
                "diode1",
                "diode2",
                "mca1_det0_events",
            ]:
                assert name in counters, name
