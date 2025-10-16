"""This module provides pytest-like features for integration tests while
preserving the capability to run the tests manualy from the Bliss shell.

The difference with pytest:

- Fixture functions cannot have the same name, even when defined in a different module.
- Fixtures always have the 'function' scope.
- Tests are not auto-discovered but need the ``@integration_fixture`` decorator
  to ensure the fixture arguments get evaluated.

A minimal example:

.. code-block: python

    from blissoda.demo import testing

    @testing.integration_fixture(autouse=True)
    def _example_auto_fixture():
        print("'_example_auto_fixture' is always called when imported")

    @testing.integration_fixture
    def _example_fixture1():
        print("setup '_example_fixture1'")
        yield "value1"
        print("teardown '_example_fixture1' always called, also when test fails")

    @testing.integration_fixture
    def _example_fixture2(_example_fixture1):
        print("execute '_example_fixture2'")
        assert _example_fixture1 == "value1"
        return "value2"

    @testing.integration_test
    def example_test(_example_fixture1, _example_fixture2, expo=0.2, npoints=10):
        assert _example_fixture1 == "value1"
        assert _example_fixture2 == "value2"

The fixtures are private to hide them from the Bliss shell.
"""

from . import _auto  # noqa F401: ensure that autouse fixtures are imported
from ._assert import demo_assert  # noqa F401
from ._celery import wait_workflows  # noqa F401
from ._fixtures import integration_fixture  # noqa F401
from ._hdf5 import assert_hdf5_dataset_exists  # noqa F401
from ._spec import assert_spec_scan_exists  # noqa F401
from ._test import integration_test  # noqa F401
