"""
Module for handling an `NXmonitor <https://manual.nexusformat.org/classes/base_classes/NXmonitor.html>`_.
"""

from __future__ import annotations

from functools import partial
from operator import is_not

import numpy
import pint
from silx.utils.proxy import docstring

from nxtomo.nxobject.nxobject import NXobject
from nxtomo.paths.nxtomo import get_paths as get_nexus_paths
from nxtomo.utils import get_quantity

__all__ = [
    "NXmonitor",
]

_ureg = pint.UnitRegistry()
_ampere = _ureg.ampere


class NXmonitor(NXobject):
    def __init__(self, node_name="control", parent: NXobject | None = None) -> None:
        """
        Representation of `NeXus NXmonitor <https://manual.nexusformat.org/classes/base_classes/NXmonitor.html>`_.
        A monitor of incident beam data.

        :param node_name: name of the monitor in the hierarchy.
        :param parent: parent in the NeXus hierarchy.
        """
        super().__init__(node_name=node_name, parent=parent)
        self._set_freeze(False)
        self._data = None
        self._set_freeze(True)

    @property
    def data(self) -> pint.Quantity | None:
        """
        Monitor data.
        In the case of NXtomo, it is expected to contain the machine electric current for each frame.
        """
        return self._data

    @data.setter
    def data(self, data: pint.Quantity | numpy.ndarray | list | tuple | None):
        if isinstance(data, pint.Quantity):
            self._data = data.to(_ampere)
        elif isinstance(data, (tuple, list)):
            if len(data) == 0:
                self._data = None
            else:
                self._data = numpy.asarray(data) * _ampere
        elif isinstance(data, numpy.ndarray):
            if data.ndim != 1:
                raise ValueError(f"data is expected to be 1D and not {data.ndim}D")
            self._data = data * _ampere
        elif data is None:
            self._data = None
        else:
            raise TypeError(
                f"data is expected to be a pint.Quantity, None, a list, or a 1D numpy array. Not {type(data)}"
            )

    @docstring(NXobject)
    def to_nx_dict(
        self,
        nexus_path_version: float | None = None,
        data_path: str | None = None,
    ) -> dict:
        nexus_paths = get_nexus_paths(nexus_path_version)
        monitor_nexus_paths = nexus_paths.nx_monitor_paths

        nx_dict = {}
        if self.data is not None:
            if monitor_nexus_paths.DATA_PATH is not None:
                data_path = f"{self.path}/{monitor_nexus_paths.DATA_PATH}"
                nx_dict[data_path] = self.data.magnitude
                nx_dict["@".join([data_path, "units"])] = f"{self.data.units:~}"

        if nx_dict != {}:
            nx_dict[f"{self.path}@NX_class"] = "NXmonitor"
        return nx_dict

    def _load(self, file_path: str, data_path: str, nexus_version: float) -> NXobject:
        """
        Create and load an NXmonitor from data on disk.
        """
        nexus_paths = get_nexus_paths(nexus_version)
        monitor_nexus_paths = nexus_paths.nx_monitor_paths
        if monitor_nexus_paths.DATA_PATH is not None:
            self.data = get_quantity(
                file_path=file_path,
                data_path="/".join([data_path, monitor_nexus_paths.DATA_PATH]),
                default_unit=_ampere,
            )

    @staticmethod
    @docstring(NXobject)
    def concatenate(nx_objects: tuple, node_name: str = "control"):
        # filter None obj
        nx_objects = tuple(filter(partial(is_not, None), nx_objects))
        if len(nx_objects) == 0:
            return None
        nx_monitor = NXmonitor(node_name=node_name)
        data = [nx_obj.data for nx_obj in nx_objects if nx_obj.data is not None]
        if len(data) > 0:
            nx_monitor.data = numpy.concatenate(data)
        return nx_monitor
