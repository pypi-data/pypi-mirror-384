import pathlib

from ._assert import demo_assert


@demo_assert("Scan #{scan_number} in SPEC file {filename}")
def assert_spec_scan_exists(filename: pathlib.Path, scan_number: int) -> None:
    find_string = f"#S {scan_number}"
    with open(filename, "r") as f:
        for line in f:
            if find_string in line:
                break
        else:
            raise AssertionError(f"{find_string!r} not found in {str(filename)!r}")
