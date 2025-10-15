from __future__ import annotations

import datetime
import functools
import gc
import os
import warnings

import numpy as np
import numpy.typing as npt
import psutil
from omfiles import OmFileWriter


def create_test_om_file(
    filename: str = "test_file.om", shape=(5, 5), dtype: npt.DTypeLike = np.float32
) -> tuple[str, np.ndarray]:
    test_data = np.arange(np.prod(shape), dtype=dtype).reshape(shape)

    writer = OmFileWriter(filename)
    variable = writer.write_array(test_data, chunks=[5, 5])
    writer.close(variable)

    return filename, test_data


def find_chunk_for_timestamp(
    target_time: datetime.datetime, domain_file_length: int, domain_temporal_resolution_seconds: int
) -> int:
    """
    Find the chunk number that contains a specific timestamp.
    """

    # Calculate seconds since epoch for the target time
    epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    target_seconds = int((target_time - epoch).total_seconds())
    chunk = target_seconds // (domain_file_length * domain_temporal_resolution_seconds)

    # # Calculate the timerange for the chunk as np.ndarray of datetime.datetime
    # chunk_start = np.datetime64(
    #     epoch + datetime.timedelta(0, chunk * domain_file_length * domain_temporal_resolution_seconds)
    # )
    # chunk_end = np.datetime64(
    #     epoch + datetime.timedelta(0, (chunk + 1) * domain_file_length * domain_temporal_resolution_seconds)
    # )

    return chunk


def filter_numpy_size_warning(func):
    """
    Decorator to filter out numpy size changed warnings.

    for some reason xr.open_dataset triggers a warning:
    "RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility. Expected 16 from C header, got 96 from Py<PyAny>"
    We will just filter it out for now...
    https://github.com/pydata/xarray/issues/7259
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="numpy.ndarray size changed", category=RuntimeWarning)
            return func(*args, **kwargs)

    return wrapper


class FileDescriptorCounter:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.fd_count_before = 0

    def count_before(self):
        self.fd_count_before = len(self.process.open_files())
        return self.fd_count_before

    def count_after(self):
        # Clean up potentially lingering objects
        gc.collect()
        return len(self.process.open_files())

    def assert_no_leaks(self):
        fd_count_after = self.count_after()
        assert fd_count_after <= self.fd_count_before, (
            f"File descriptor leak: {self.fd_count_before} before, {fd_count_after} after"
        )
