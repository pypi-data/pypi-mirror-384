"""I/O utilities."""

import contextlib
import functools
import logging
import traceback
from contextlib import contextmanager

import h5py

try:
    import hdf5plugin  # noqa F401
except ImportError:
    pass
from silx.io.url import DataUrl
from silx.io.utils import open as hdf5_open

__all__ = ["EntryReader", "DatasetReader", "deprecated_warning", "deprecated"]


class _BaseReader(contextlib.AbstractContextManager):
    def __init__(self, url: DataUrl):
        if not isinstance(url, DataUrl):
            raise TypeError(f"url should be an instance of DataUrl. Not {type(url)}")
        if url.scheme() not in ("silx", "h5py"):
            raise ValueError("Valid scheme are silx and h5py")
        if url.data_slice() is not None:
            raise ValueError(
                "Data slices are not managed. Data path should "
                "point to a bliss node (h5py.Group)"
            )
        self._url = url
        self._file_handler = None

    def __exit__(self, *exc):
        return self._file_handler.close()


class EntryReader(_BaseReader):
    """Context manager used to read a BLISS node."""

    def __enter__(self):
        self._file_handler = hdf5_open(filename=self._url.file_path())
        if self._url.data_path() == "":
            entry = self._file_handler
        elif self._url.data_path() not in self._file_handler:
            raise KeyError(
                f"data path '{self._url.data_path()}' doesn't exists from '{self._url.file_path()}'"
            )
        else:
            entry = self._file_handler[self._url.data_path()]
        if not isinstance(entry, h5py.Group):
            raise ValueError("Data path should point to a bliss node (h5py.Group)")
        return entry


class DatasetReader(_BaseReader):
    """Context manager used to read a BLISS node."""

    def __enter__(self):
        self._file_handler = hdf5_open(filename=self._url.file_path())
        entry = self._file_handler[self._url.data_path()]
        if not isinstance(entry, h5py.Dataset):
            raise ValueError(
                f"Data path ({self._url.path()}) should point to a dataset (h5py.Dataset)"
            )
        return entry


depreclog = logging.getLogger("nxtomo.DEPRECATION")

deprecache = set([])


def deprecated_warning(
    type_,
    name,
    reason=None,
    replacement=None,
    since_version=None,
    only_once=True,
    skip_backtrace_count=0,
):
    """
    Log a deprecation warning.

    :param type_: Nature of the object to be deprecated,
        e.g. "Module", "Function", "Class".
    :param name: Object name.
    :param reason: Reason for deprecating this object (e.g. "feature no longer provided").
    :param replacement: Name of the replacement function (when the deprecation renames the function).
    :param since_version: First *silx* version for which the function was deprecated (e.g. "0.5.0").
    :param only_once: If True, the deprecation warning is generated only once for each call site. Default is True.
    :param skip_backtrace_count: Number of trailing stack frames to ignore when logging the backtrace.
    """
    if not depreclog.isEnabledFor(logging.WARNING):
        # Avoid computation when it is not logged
        return

    msg = "%s %s is deprecated"
    if since_version is not None:
        msg += " since silx version %s" % since_version
    msg += "."
    if reason is not None:
        msg += " Reason: %s." % reason
    if replacement is not None:
        msg += " Use '%s' instead." % replacement
    msg += "\n%s"
    limit = 2 + skip_backtrace_count
    backtrace = "".join(traceback.format_stack(limit=limit)[0])
    backtrace = backtrace.rstrip()
    if only_once:
        data = (msg, type_, name, backtrace)
        if data in deprecache:
            return
        else:
            deprecache.add(data)
    depreclog.warning(msg, type_, name, backtrace)


def deprecated(
    func=None,
    reason=None,
    replacement=None,
    since_version=None,
    only_once=True,
    skip_backtrace_count=1,
):
    """
    Decorator that deprecates the use of a function.

    :param str reason: Reason for deprecating this function (e.g. "feature no longer provided").
    :param str replacement: Name of the replacement function (when the deprecation renames the function).
    :param str since_version: First *silx* version for which the function was deprecated (e.g. "0.5.0").
    :param bool only_once: If True, the deprecation warning is generated only once. Default is True.
    :param int skip_backtrace_count: Number of trailing stack frames to ignore when logging the backtrace.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            deprecated_warning(
                type_="Function",
                name=func.__name__,
                reason=reason,
                replacement=replacement,
                since_version=since_version,
                only_once=only_once,
                skip_backtrace_count=skip_backtrace_count,
            )
            return func(*args, **kwargs)

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


@contextmanager
def ignore_deprecation_warning():
    """Filter logs from 'nxtomo.DEPRECATION'."""

    def filter(record):
        return record.name != depreclog.name

    depreclog.addFilter(filter)
    yield
    depreclog.removeFilter(filter)
