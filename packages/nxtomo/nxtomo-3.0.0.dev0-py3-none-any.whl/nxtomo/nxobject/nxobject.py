"""
Module for handling an `NXobject <https://manual.nexusformat.org/classes/base_classes/NXobject.html>`_.
"""

from __future__ import annotations

import logging
import os

import h5py
from silx.io.dictdump import dicttonx
from silx.io.url import DataUrl

from nxtomo.io import (
    HDF5File,
    cwd_context,
    from_data_url_to_virtual_source,
    to_target_rel_path,
)
from nxtomo.paths.nxtomo import LATEST_VERSION as LATEST_NXTOMO_VERSION

_logger = logging.getLogger(__name__)


class NXobject:
    __isfrozen = False
    # to ease API and avoid setting wrong attributes we 'freeze' the attributes
    # see https://stackoverflow.com/questions/3603502/prevent-creating-new-attributes-outside-init

    def __init__(self, node_name: str, parent=None) -> None:
        """
        Representation of `NeXus NXobject <https://manual.nexusformat.org/classes/base_classes/NXobject.html>`_.
        Base class for NXtomo objects.

        :param node_name: name of the object in the hierarchy.
        :param parent: parent in the NeXus hierarchy.
        """
        if not isinstance(node_name, str):
            raise TypeError(
                f"name is expected to be an instance of str. Not {type(node_name)}"
            )
        if "/" in node_name:
            # make sure there is no '/' character. This is reserved to define the NXobject hierarchy
            raise ValueError(
                "'/' found in 'node_name' parameter. This is a reserved character. Please change the name"
            )
        self.node_name = node_name
        self.parent = parent
        self._set_freeze()

    def _set_freeze(self, freeze=True):
        self.__isfrozen = freeze

    @property
    def parent(self):  # -> NXobject | None:
        """
        :class:`~nxtomo.nxobject.nxobject.NXobject` parent in the hierarchy.
        """
        return self._parent

    @parent.setter
    def parent(self, parent) -> None:
        if not isinstance(parent, (type(None), NXobject)):
            raise TypeError(
                f"parent is expected to be None or an instance of {NXobject}. Got {type(parent)}"
            )
        self._parent = parent

    @property
    def is_root(self) -> bool:
        """Return True if this :class:`~nxtomo.nxobject.nxobject.NXobject` is the top-level object."""
        return self.parent is None

    @property
    def root_path(self) -> str:
        """Return the path of the root :class:`~nxtomo.nxobject.nxobject.NXobject`."""
        if self.is_root:
            return self.path
        else:
            return self.parent.root_path

    @property
    def path(self):
        """
        Path of the object in the NeXus hierarchy.
        """

        if self.parent is not None:
            path = "/".join([self.parent.path, self.node_name])
        else:
            path = ""
        # clean some possible issues with "//"
        path = path.replace("//", "/")
        return path

    @property
    def node_name(self) -> str:
        """Name of the :class:`~nxtomo.nxobject.nxobject.NXobject` in the NeXus hierarchy."""
        return self._node_name

    @node_name.setter
    def node_name(self, node_name: str):
        if not isinstance(node_name, str):
            raise TypeError(
                f"nexus_name should be an instance of str and not {type(node_name)}"
            )
        self._node_name = node_name

    def save(
        self,
        file_path: str,
        data_path: str | None = None,
        nexus_path_version: float | None = None,
        overwrite: bool = False,
    ) -> None:
        """
        Save the NXobject to disk.

        :param file_path: HDF5 file path.
        :param data_path: location of the NXobject. If not provided the node name is used (when valid).
        :param nexus_path_version: optional NeXus version as float, when saving must use a non-latest version.
        :param overwrite: if the data path already exists, overwrite it; otherwise, raise an error.
        """
        if data_path == "/":
            _logger.warning(
                "'data_path' set to '/' is now an invalid value. Please set 'data_path' to None if you want to store it under the NXobject name at root level, else provide data_path. Will ignore it."
            )
            data_path = None
        entry_path = data_path or self.path or self.node_name
        # entry path is the 'root path'. If not provided use self.path. If None (if at the root level) then use the node name
        for key, value in dict(
            [("file_path", file_path), ("entry", data_path)]
        ).items():
            if not isinstance(value, (type(None), str)):
                raise TypeError(
                    f"{key} is expected to be None or an instance of str not {type(value)}"
                )
        if not isinstance(overwrite, bool):
            raise TypeError(f"overwrite should be a bool. Got {type(overwrite)}")

        if entry_path.lstrip("/").rstrip("/") == "":
            raise ValueError(
                f"root NXobject need to have a data_path to be saved. '{entry_path}' is invalid. Interpreted as '{entry_path.lstrip('/').rstrip('/')}'"
            )
        # not fully sure about the dicttoh5 "add" behavior
        if os.path.exists(file_path):
            with h5py.File(file_path, mode="a") as h5f:
                if entry_path != "/" and entry_path in h5f:
                    if overwrite:
                        del h5f[entry_path]
                    else:
                        raise KeyError(f"{entry_path} already exists")
        if nexus_path_version is None:
            nexus_path_version = LATEST_NXTOMO_VERSION

        nx_dict = self.to_nx_dict(
            nexus_path_version=nexus_path_version, data_path=data_path
        )
        # retrieve virtual sources and DataUrl
        datasets_to_handle_in_postprocessing = {}
        for key in self._get_virtual_sources(nx_dict):
            datasets_to_handle_in_postprocessing[key] = nx_dict.pop(key)
        for key in self._get_data_urls(nx_dict):
            datasets_to_handle_in_postprocessing[key] = nx_dict.pop(key)
        master_vds_file = self._get_vds_master_file_folder(nx_dict)

        # retrieve attributes
        attributes = {}

        dataset_to_postpone = tuple(datasets_to_handle_in_postprocessing.keys())
        for key, value in nx_dict.items():
            if key.startswith(dataset_to_postpone):
                attributes[key] = value
        # clean attributes
        for key in attributes:
            del nx_dict[key]

        dicttonx(
            nx_dict,
            h5file=file_path,
            h5path=data_path,
            update_mode="replace",
            mode="a",
        )

        assert os.path.exists(file_path)

        # in order to solve relative path we need to be on the (source) master file working directory
        with cwd_context(master_vds_file):
            # now handle nx_dict containing h5py.virtualSource or DataUrl
            # this cannot be handled from the nxdetector class because not aware about
            # the output file.
            for (
                dataset_path,
                v_sources_or_data_urls,
            ) in datasets_to_handle_in_postprocessing.items():
                data_type = None
                vs_shape = None
                n_frames = 0

                v_sources_to_handle_in_postprocessing = []
                # convert DataUrl to VirtualSource
                dataset_keys = v_sources_or_data_urls
                for v_source_or_data_url in dataset_keys:
                    if isinstance(v_source_or_data_url, DataUrl):
                        vs = from_data_url_to_virtual_source(
                            v_source_or_data_url, target_path=master_vds_file
                        )[0]
                    else:
                        assert isinstance(
                            v_source_or_data_url, h5py.VirtualSource
                        ), "v_source_or_data_url is not a DataUrl or a VirtualSource"
                        vs = v_source_or_data_url

                    if data_type is None:
                        data_type = vs.dtype
                    elif vs.dtype != data_type:
                        raise TypeError(
                            f"Virtual sources have incoherent data types (found {data_type} and {vs.dtype})"
                        )

                    if not len(vs.maxshape) == 3:
                        raise ValueError(
                            f"Virtual sources are expected to be 3D. {len(vs.maxshape)} found"
                        )
                    if vs_shape is None:
                        vs_shape = vs.maxshape[1:]
                    elif vs_shape != vs.maxshape[1:]:
                        raise ValueError(
                            f"Virtual sources are expected to have same frame dimensions. found {vs_shape} and {vs.maxshape[1:]}"
                        )
                    n_frames += vs.maxshape[0]
                    vs.path = to_target_rel_path(vs.path, file_path)
                    v_sources_to_handle_in_postprocessing.append(vs)

                if n_frames == 0:
                    # in the case there is no frame to be saved
                    return

                vs_shape = [
                    n_frames,
                ] + list(vs_shape)
                layout = h5py.VirtualLayout(shape=tuple(vs_shape), dtype=data_type)
                # fill virtual dataset
                loc_pointer = 0
                for v_source in v_sources_to_handle_in_postprocessing:
                    layout[loc_pointer : (loc_pointer + v_source.maxshape[0])] = (
                        v_source
                    )
                    loc_pointer += v_source.maxshape[0]

                with HDF5File(file_path, mode="a") as h5s:
                    h5s.create_virtual_dataset(
                        "/".join([entry_path, dataset_path]), layout
                    )

        # write attributes of dataset defined from a list of DataUrl or VirtualSource
        assert os.path.exists(file_path)
        dicttonx(
            attributes,
            h5file=file_path,
            h5path=entry_path,
            update_mode="add",
            mode="a",
        )

    def to_nx_dict(
        self,
        nexus_path_version: float | None = None,
        data_path: str | None = None,
    ) -> dict:
        """
        Convert the NXobject to an NX dictionary suitable for dumping to an HDF5 file.

        :param nexus_path_version: NeXus path version to use.
        :param data_path: optional data path used to build links in the file.
        """
        raise NotImplementedError("Base class")

    def __str__(self) -> str:
        return f"{type(self)}: {self.path}"

    @staticmethod
    def _get_virtual_sources(ddict) -> tuple:
        """Return keys/paths containing a list or tuple of h5py.VirtualSource objects."""

        def has_virtual_sources(value):
            if isinstance(value, h5py.VirtualSource):
                return True
            elif isinstance(value, (list, tuple)):
                for v in value:
                    if has_virtual_sources(v):
                        return True
            return False

        keys = []
        for key, value in ddict.items():
            if has_virtual_sources(value):
                keys.append(key)
        return tuple(keys)

    @staticmethod
    def _get_vds_master_file_folder(nx_dict: dict):
        path = nx_dict.pop("__vds_master_file__", None)
        if path is not None:
            return os.path.dirname(path)
        else:
            return None

    @staticmethod
    def _get_data_urls(ddict) -> tuple:
        """Return keys/paths containing a list or tuple of silx.io.url.DataUrl objects."""

        def has_data_url(value):
            if isinstance(value, DataUrl):
                return True
            elif isinstance(value, (list, tuple)):
                for v in value:
                    if has_data_url(v):
                        return True
            return False

        keys = []
        for key, value in ddict.items():
            if has_data_url(value):
                keys.append(key)
        return tuple(keys)

    def __setattr__(self, __name, __value):
        if self.__isfrozen and not hasattr(self, __name):
            raise AttributeError("can't set attribute", __name)
        else:
            super().__setattr__(__name, __value)

    @staticmethod
    def concatenate(nx_objects: tuple, node_name: str):
        """
        Concatenate a tuple of NXobjects into a single NXobject.

        :param nx_objects: NXobjects to concatenate.
        :param node_name: name of the node to create. Parent must be handled manually for now.
        """
        raise NotImplementedError("Base class")
