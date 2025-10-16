"""General utility helpers."""

from __future__ import annotations

import os
from typing import Iterable

import h5py
import numpy
import pint
from silx.io.utils import h5py_read_dataset
from silx.io.utils import open as hdf5_open

from nxtomo.io import to_target_rel_path

_ureg = pint.UnitRegistry()

try:
    import tifffile  # noqa F401
except ImportError:
    has_tifffile = False
else:
    from tifffile import TiffFile

    has_tifffile = True

__all__ = [
    "cast_and_check_array_1D",
    "get_data",
    "get_quantity",
]


def cast_and_check_array_1D(array, array_name: str):
    """
    Cast the provided array to 1D and handle pint quantities.

    :param array: array to be cast to 1D. Can be a pint.Quantity.
    :param array_name: name of the array (used for logging only).
    :return: 1D NumPy array (with magnitude if a pint.Quantity).
    :raises TypeError: if the input type is invalid.
    :raises ValueError: if the input has more than one dimension.
    """
    if not isinstance(array, (type(None), numpy.ndarray, Iterable, pint.Quantity)):
        raise TypeError(
            f"{array_name} is expected to be None, an Iterable, or a pint.Quantity. "
            f"Not {type(array)}"
        )
    if isinstance(array, pint.Quantity):
        unit = array.units
        array = array.magnitude
    else:
        unit = None

    if array is not None and not isinstance(array, numpy.ndarray):
        array = numpy.asarray(array)

    if array is not None and array.ndim > 1:
        raise ValueError(f"{array_name} is expected to be 0 or 1D, not {array.ndim}D")
    return array * unit if unit else array


def get_quantity(
    file_path: str, data_path: str, default_unit: pint.Unit
) -> pint.Quantity:
    """
    Return the value and unit of an HDF5 dataset. If the unit is not found, fall back on `default_unit`.

    :param file_path: file path location of the HDF5 dataset to read.
    :param data_path: data path location of the HDF5 dataset to read.
    :param default_unit: default unit to use if the dataset has no ``unit`` or ``units`` attribute, as a pint.Unit object.
    :return: pint.Quantity with the data and associated unit.
    """
    with hdf5_open(file_path) as h5f:
        if data_path in h5f and isinstance(h5f[data_path], h5py.Dataset):
            dataset = h5f[data_path]
            unit = None
            if "unit" in dataset.attrs:
                unit = dataset.attrs["unit"]
            elif "units" in dataset.attrs:
                unit = dataset.attrs["units"]
            else:
                unit = str(default_unit)  # Use default unit if none found
            if hasattr(unit, "decode"):
                unit = unit.decode()

            if unit == "kev":
                unit = "keV"
            try:
                unit = _ureg(unit)  # Convert to a pint unit
            except pint.UndefinedUnitError:
                raise ValueError(f"Invalid or undefined unit: {unit}")
            data = h5py_read_dataset(dataset)  # Read dataset values
            return data * unit
        else:
            return None


def get_data(file_path: str, data_path: str):
    """
    Proxy to `h5py_read_dataset`, handling the case where `data_path` is not present in the file.
    In this situation, return None.

    :param file_path: file path location of the HDF5 dataset to read.
    :param data_path: data path location of the HDF5 dataset to read.
    """
    with hdf5_open(file_path) as h5f:
        if data_path in h5f:
            return h5py_read_dataset(h5f[data_path])
        else:
            return None


def create_detector_dataset_from_tiff(
    tiff_files: tuple,
    external_dataset_group: h5py.Group,
    external_dataset_prefix="frame_",
    dtype=None,
    relative_link: bool = True,
) -> tuple[h5py.VirtualSource]:
    """
    Create a series of external datasets to TIFF files (one per file) inside ``external_dataset_group``.

    :param tiff_files: files used to create virtual sources.
    :param external_dataset_group: output HDF5 group. The file must be opened with write access (mode 'w' or 'a').
    :param dtype: expected dtype of all the TIFF data. If not provided it is deduced from the first dataset.
    :param relative_link: if True create the link using a relative path; otherwise use an absolute path.

    .. warning::

        The most robust way to create an NXtomo is to use relative links (in order to share it with the ``.tif`` files).
        Nevertheless there is currently a limitation on how relative links are resolved for external datasets
        (resolution is done according to the current working directory instead of the file).
        Tomotools handles this, but other software might not (such as silx, as this is a workaround that should be handled at the HDF5 level).
        Links might therefore appear broken when using relative paths, which will not happen when using absolute paths.
    """
    if not has_tifffile:
        raise RuntimeError("tiff file not installed")
    external_datasets = []

    # convert from local to ...

    for i_file, tiff_file in enumerate(tiff_files):
        with TiffFile(tiff_file, mode="r") as tif:
            fh = tif.filehandle
            for page in tif.pages:
                if dtype is not None:
                    assert dtype == page.dtype, "incoherent data type"
                dtype = page.dtype
                for index, (offset, bytecount) in enumerate(
                    zip(page.dataoffsets, page.databytecounts)
                ):
                    _ = fh.seek(offset)
                    data = fh.read(bytecount)
                    _, _, shape = page.decode(data, index, jpegtables=page.jpegtables)
                    if len(shape) == 4:
                        # don't know why but return it as 4D when 2D expected...
                        shape = shape[0:-1]
                    elif len(shape) == 2:
                        shape = 1, *shape

                    # move tiff file path to relative path
                    if relative_link:
                        external_file_path = to_target_rel_path(
                            file_path=tiff_file,
                            target_path=external_dataset_group.file.filename,
                        )
                    else:
                        external_file_path = os.path.abspath(tiff_file)

                    external_dataset = external_dataset_group.create_dataset(
                        name=f"{external_dataset_prefix}{str(i_file).zfill(6)}",
                        shape=shape,
                        dtype=dtype,
                        external=[(external_file_path, offset, bytecount)],
                    )
                    external_datasets.append(external_dataset)

    virtual_sources = []
    for i, ed in enumerate(external_datasets):
        vsource = h5py.VirtualSource(ed)
        virtual_sources.append(vsource)
    return tuple(virtual_sources)
