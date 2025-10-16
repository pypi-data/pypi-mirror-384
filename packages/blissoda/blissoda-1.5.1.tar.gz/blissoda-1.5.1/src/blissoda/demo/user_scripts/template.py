"""Template for new integration tests."""

from blissoda.demo import testing


def template_demo(expo=0.2, npoints=10):
    for _ in range(2):
        template_test(expo=expo, npoints=npoints)


@testing.integration_fixture
def _template_fixture1():
    print("setup '_template_fixture1'")
    yield "value1"
    print("teardown '_template_fixture1' always called, also when test fails")


@testing.integration_fixture
def _template_fixture2(_template_fixture1):
    print("execute '_template_fixture2'")
    assert _template_fixture1 == "value1"
    return "value2"


@testing.integration_test
def template_test(_template_fixture1, _template_fixture2, expo=0.2, npoints=10):
    assert _template_fixture1 == "value1"
    assert _template_fixture2 == "value2"
