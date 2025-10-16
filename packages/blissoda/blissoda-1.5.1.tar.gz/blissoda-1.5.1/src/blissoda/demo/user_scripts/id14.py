import pathlib

from blissoda.bliss_globals import setup_globals
from blissoda.demo import testing
from blissoda.demo.processors.id14 import DemoId14Hdf5ToSpecConverter

id14_converter = DemoId14Hdf5ToSpecConverter()


def id14_demo(expo=0.2, npoints=10):
    for _ in range(2):
        test_id14_loopscan(expo=expo, npoints=npoints)


@testing.integration_fixture
def _id14():
    id14_converter.enable()
    yield id14_converter
    id14_converter.disable()


@testing.integration_test
def test_id14_loopscan(_id14, expo=0.2, npoints=10):
    scan = setup_globals.loopscan(
        npoints, expo, setup_globals.diode1, setup_globals.mca1
    )
    scan_number = scan.scan_info["scan_nb"]
    _assert_spec_counter_file(_id14, scan_number)
    _assert_spec_mca_file(_id14, scan_number)


@testing.demo_assert("Check ID14 SPEC file for scan #{scan_number}")
def _assert_spec_counter_file(_id14, scan_number):
    result = _id14._future_for_counters.result(timeout=10)
    output_filename = pathlib.Path(result["output_filename"])
    testing.assert_spec_scan_exists(output_filename, scan_number)


@testing.demo_assert("Check ID14 MCA file for scan #{scan_number}")
def _assert_spec_mca_file(_id14, scan_number):
    result = _id14._future_for_mca.result(timeout=10)
    output_filenames = result["output_filenames"]
    if not output_filenames:
        raise AssertionError("No filenames returned from ID14 MCA conversion workflow")
    for output_filename in output_filenames:
        testing.assert_spec_scan_exists(output_filename, scan_number)
