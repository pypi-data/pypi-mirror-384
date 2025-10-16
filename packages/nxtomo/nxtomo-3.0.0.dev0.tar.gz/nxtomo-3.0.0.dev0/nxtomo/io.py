"""
Some I/O utilities to handle `NeXus <https://manual.nexusformat.org/index.html>`_ and
`HDF5 <https://www.hdfgroup.org/solutions/hdf5/>`_ with `h5py <https://www.h5py.org/>`_.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager

import h5py
import h5py._hl.selections as selection
from h5py import File as HDF5File  # noqa F401
from silx.io.url import DataUrl
from silx.io.utils import open as hdf5_open

_logger = logging.getLogger(__name__)

__all__ = [
    "get_swmr_mode",
    "check_virtual_sources_exist",
    "from_data_url_to_virtual_source",
    "from_virtual_source_to_data_url",
    "cwd_context",
    "to_target_rel_path",
]

_DEFAULT_SWMR_MODE = None


def get_swmr_mode() -> bool | None:
    """
    Return True if SWMR should be used in the tomotools scope.
    """
    swmr_mode = os.environ.get("TOMOTOOLS_SWMR", _DEFAULT_SWMR_MODE)
    if swmr_mode in (None, "None", "NONE"):
        return None
    else:
        return swmr_mode in (
            True,
            "True",
            "true",
            "TRUE",
            "1",
            1,
        )


def check_virtual_sources_exist(fname, data_path):
    """
    Check that a virtual dataset points to actual data.

    :param fname: HDF5 file path
    :param data_path: Path within the HDF5 file

    :return res: Whether the virtual dataset points to actual data.
    """
    with hdf5_open(fname) as f:
        if data_path not in f:
            _logger.error(f"No dataset {data_path} in file {fname}")
            return False
        dptr = f[data_path]
        if not dptr.is_virtual:
            return True
        for vsource in dptr.virtual_sources():
            vsource_fname = os.path.join(
                os.path.dirname(dptr.file.filename), vsource.file_name
            )
            if not os.path.isfile(vsource_fname):
                _logger.error(f"No such file: {vsource_fname}")
                return False
            elif not check_virtual_sources_exist(vsource_fname, vsource.dset_name):
                _logger.error(f"Error with virtual source {vsource_fname}")
                return False
    return True


def from_data_url_to_virtual_source(url: DataUrl, target_path: str | None) -> tuple:
    """
    Convert a DataUrl to a set (as tuple) of h5py.VirtualSource.

    :param url: URL to be converted to a virtual source. It must target a 2D detector.
    :return: (h5py.VirtualSource, tuple(shape of the virtual source), numpy.dtype: type of the dataset associated with the virtual source)
    """
    if not isinstance(url, DataUrl):
        raise TypeError(
            f"url is expected to be an instance of DataUrl and not {type(url)}"
        )

    with hdf5_open(url.file_path()) as o_h5s:
        original_data_shape = o_h5s[url.data_path()].shape
        data_type = o_h5s[url.data_path()].dtype
        if len(original_data_shape) == 2:
            original_data_shape = (
                1,
                original_data_shape[0],
                original_data_shape[1],
            )

        vs_shape = original_data_shape
        if url.data_slice() is not None:
            vs_shape = (
                url.data_slice().stop - url.data_slice().start,
                original_data_shape[-2],
                original_data_shape[-1],
            )

    if target_path is not None and (
        target_path == url.file_path()
        or os.path.abspath(target_path) == url.file_path()
    ):
        file_path = "."
    else:
        file_path = url.file_path()
    vs = h5py.VirtualSource(file_path, url.data_path(), shape=vs_shape, dtype=data_type)

    if url.data_slice() is not None:
        vs.sel = selection.select(original_data_shape, url.data_slice())
    return vs, vs_shape, data_type


def from_virtual_source_to_data_url(vs: h5py.VirtualSource) -> DataUrl:
    """
    Convert a h5py.VirtualSource to a DataUrl.

    :param vs: virtual source to be converted to a DataUrl.
    :return: resulting URL.
    """
    if not isinstance(vs, h5py.VirtualSource):
        raise TypeError(
            f"vs is expected to be an instance of h5py.VirtualSorce and not {type(vs)}"
        )
    url = DataUrl(file_path=vs.path, data_path=vs.name, scheme="silx")
    return url


@contextmanager
def cwd_context(new_cwd=None):
    """
    Create a context with `new_cwd`.

    On entry update the current working directory to `new_cwd` and reset the previous working directory at exit.

    :param new_cwd: working directory to use in the context.
    """
    try:
        curdir = os.getcwd()
    except Exception as e:
        _logger.error(e)
        curdir = None
    try:
        if new_cwd is not None and os.path.isfile(new_cwd):
            new_cwd = os.path.dirname(new_cwd)
        if new_cwd not in (None, ""):
            os.chdir(new_cwd)
        yield
    finally:
        if curdir is not None:
            os.chdir(curdir)


def to_target_rel_path(file_path: str, target_path: str) -> str:
    """
    Cast `file_path` to a relative path according to `target_path`.
    This is used to deduce the path of an h5py.VirtualSource.

    :param file_path: file path to convert to a relative path.
    :param target_path: reference path used to compute the relative path.
    :return: relative path of `file_path` compared to `target_path`.
    """
    if file_path == target_path or os.path.abspath(file_path) == os.path.abspath(
        target_path
    ):
        return "."
    file_path = os.path.abspath(file_path)
    target_path = os.path.abspath(target_path)
    path = os.path.relpath(file_path, os.path.dirname(target_path))
    if not path.startswith("./"):
        path = "./" + path
    return path
