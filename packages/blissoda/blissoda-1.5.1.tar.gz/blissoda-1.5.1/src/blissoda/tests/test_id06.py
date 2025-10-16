import numpy
import pytest

from ..id06.utils import get_positions
from ..id06.xrpd_processor import Id06XrpdProcessor

PI = numpy.pi


def test_get_positions():
    deg_step = 1
    rad_step = numpy.deg2rad(deg_step)

    pyfai_pos = get_positions(start=0, step=1, npts=360)
    theoretical_pos = numpy.concatenate(
        (
            numpy.arange(-PI + rad_step / 2, 0, rad_step),
            numpy.arange(0, PI, rad_step),
        ),
        axis=0,
    )

    assert numpy.all(pyfai_pos - theoretical_pos < 1e-13)


class MockScan:
    def __init__(self, scan_info):
        self.scan_info = scan_info


@pytest.mark.parametrize(
    "scan_info",
    [
        ({"type": "fscan", "save": True}),
        ({"type": "oscan", "save": True}),
    ],
)
def test_get_integration_options_parametrized(mock_bliss, scan_info):
    mock_scan = MockScan(scan_info=scan_info)
    id06_xrpd_processor = Id06XrpdProcessor()
    id06_xrpd_processor.integration_options = {"param": 22}

    result = id06_xrpd_processor.get_integration_options(mock_scan, "lima_name")

    assert result["param"] == 22
