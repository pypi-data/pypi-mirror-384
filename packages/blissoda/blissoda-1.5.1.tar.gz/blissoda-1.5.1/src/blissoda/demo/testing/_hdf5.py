import pathlib
from typing import Tuple

import h5py
from silx.io.h5py_utils import retry
from silx.utils.retry import RetryError

from ._assert import demo_assert


@demo_assert("HDF5 dataset {data_path} in {filename} with shape {expected_shape}")
@retry(retry_timeout=10, retry_period=0.2)
def assert_hdf5_dataset_exists(
    filename: pathlib.Path,
    data_path: str,
    expected_shape: Tuple[int, ...],
) -> None:
    if not filename.exists():
        raise RetryError(f"{str(filename)!r} does not exist")
    filename = str(filename)
    with h5py.File(filename, mode="r") as root:
        if data_path not in root:
            raise RetryError(f"{data_path!r} not in {filename!r}")

        dset = root[data_path]
        if dset.shape != expected_shape:
            url = f"{filename!r}::{data_path}"
            raise RetryError(
                f"Shape of {url!r} is {dset.shape} instead of {expected_shape}"
            )
