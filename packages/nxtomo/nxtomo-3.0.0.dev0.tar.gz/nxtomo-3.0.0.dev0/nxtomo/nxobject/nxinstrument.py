"""
Module for handling an `NXinstrument <https://manual.nexusformat.org/classes/base_classes/NXinstrument.html>`_.
"""

from __future__ import annotations

import logging
from functools import partial
from operator import is_not

import pint
from silx.io.utils import open as open_hdf5
from silx.utils.proxy import docstring

from nxtomo.nxobject.nxdetector import NXdetector, NXdetectorWithUnit
from nxtomo.nxobject.nxobject import NXobject
from nxtomo.nxobject.nxsource import DefaultESRFSource, NXsource
from nxtomo.paths.nxtomo import get_paths as get_nexus_paths
from nxtomo.utils import get_data

_logger = logging.getLogger(__name__)

__all__ = [
    "NXinstrument",
]

_ureg = pint.UnitRegistry()
_volt = _ureg.volt


class NXinstrument(NXobject):
    def __init__(
        self, node_name: str = "instrument", parent: NXobject | None = None
    ) -> None:
        """
        Representation of `NeXus NXinstrument <https://manual.nexusformat.org/classes/base_classes/NXinstrument.html>`_.

        Collection of the components of the instrument or beamline.

        :param node_name: name of the instrument in the hierarchy.
        :param parent: parent in the NeXus hierarchy.
        """
        super().__init__(node_name=node_name, parent=parent)
        self._set_freeze(False)
        self._detector = NXdetector(
            node_name="detector",
            parent=self,
            field_of_view="Full",
            expected_dim=(2, 3),
        )
        self._diode = NXdetectorWithUnit(
            node_name="diode",
            parent=self,
            expected_dim=(1,),
            default_unit=_volt,
        )
        self._source = DefaultESRFSource(node_name="source", parent=self)
        self._name = None
        self._set_freeze(True)

    @property
    def detector(self) -> NXdetector | None:
        """
        :class:`~nxtomo.nxobject.nxdetector.NXdetector`
        """
        return self._detector

    @detector.setter
    def detector(self, detector: NXdetector | None):
        if not isinstance(detector, (NXdetector, type(None))):
            raise TypeError(
                f"detector is expected to be None or an instance of NXdetector. Not {type(detector)}"
            )
        self._detector = detector

    @property
    def diode(self) -> NXdetector | None:
        """
        :class:`~nxtomo.nxobject.nxdetector.NXdetector`
        """
        return self._diode

    @diode.setter
    def diode(self, diode: NXdetector | None):
        if not isinstance(diode, (NXdetector, type(None))):
            raise TypeError(
                f"diode is expected to be None or an instance of NXdetector. Not {type(diode)}"
            )
        self._diode = diode

    @property
    def source(self) -> NXsource | None:
        """
        :class:`~nxtomo.nxobject.nxsource.NXsource`
        """
        return self._source

    @source.setter
    def source(self, source: NXsource | None) -> None:
        if not isinstance(source, (NXsource, type(None))):
            raise TypeError(
                f"source is expected to be None or an instance of NXsource. Not {type(source)}"
            )
        self._source = source

    @property
    def name(self) -> str | None:
        """Instrument name (for example, BM00)."""
        return self._name

    @name.setter
    def name(self, name: str | None) -> None:
        if not isinstance(name, (str, type(None))):
            raise TypeError(
                f"name is expected to be None or an instance of str. Not {type(name)}"
            )
        self._name = name

    @docstring(NXobject)
    def to_nx_dict(
        self,
        nexus_path_version: float | None = None,
        data_path: str | None = None,
    ) -> dict:
        nexus_paths = get_nexus_paths(nexus_path_version)
        nexus_instrument_paths = nexus_paths.nx_instrument_paths
        nx_dict = {}

        if self._detector is not None:
            nx_dict.update(
                self._detector.to_nx_dict(nexus_path_version=nexus_path_version)
            )

        if self._diode is not None:
            nx_dict.update(
                self._diode.to_nx_dict(nexus_path_version=nexus_path_version)
            )

        if self._source is not None:
            nx_dict.update(
                self.source.to_nx_dict(nexus_path_version=nexus_path_version)
            )

        if self.name is not None:
            nx_dict[f"{self.path}/{nexus_instrument_paths.NAME}"] = self.name
        if nx_dict != {}:
            nx_dict[f"{self.path}@NX_class"] = "NXinstrument"

        return nx_dict

    def _load(
        self,
        file_path: str,
        data_path: str,
        nexus_version: float,
        detector_data_as: str,
    ) -> NXobject:
        """
        Create and load an NXinstrument from data on disk.
        """
        nexus_paths = get_nexus_paths(nexus_version)
        nexus_instrument_paths = nexus_paths.nx_instrument_paths

        with open_hdf5(file_path) as h5f:
            if data_path in h5f:
                has_detector = "detector" in h5f[data_path]
                has_diode = "diode" in h5f[data_path]
                has_source = "source" in h5f[data_path]
            else:
                has_detector = False
                has_diode = False
                has_source = False
        # TODO: loading detector might be done using the NXclass instead of some hard coded names
        if has_detector:
            self.detector._load(
                file_path=file_path,
                data_path="/".join(
                    [data_path, "detector"],
                ),
                nexus_version=nexus_version,
                load_data_as=detector_data_as,
            )
        if has_diode:
            self.diode._load(
                file_path=file_path,
                data_path="/".join(
                    [data_path, "diode"],
                ),
                nexus_version=nexus_version,
                load_data_as="as_numpy_array",
            )
        if has_source:
            self.source._load(
                file_path=file_path,
                data_path="/".join([data_path, "source"]),
                nexus_version=nexus_version,
            )
        if nexus_instrument_paths.NAME is not None:
            self.name = get_data(
                file_path=file_path,
                data_path="/".join([data_path, nexus_instrument_paths.NAME]),
            )

    @staticmethod
    @docstring(NXobject)
    def concatenate(nx_objects: tuple, node_name="instrument"):
        # filter None obj
        nx_objects = tuple(filter(partial(is_not, None), nx_objects))
        if len(nx_objects) == 0:
            return None
        # warning: later we make the assumption that nx_objects contains at least one element
        for nx_obj in nx_objects:
            if not isinstance(nx_obj, NXinstrument):
                raise TypeError("Cannot concatenate non NXinstrument object")

        nx_instrument = NXinstrument(node_name=node_name)

        nx_instrument.name = nx_objects[0].name
        _logger.info(f"instrument name {nx_objects[0].name} will be picked")

        nx_instrument.source = NXsource.concatenate(
            [nx_obj.source for nx_obj in nx_objects],
            node_name="source",
        )
        nx_instrument.source.parent = nx_instrument

        nx_instrument.diode = NXdetectorWithUnit.concatenate(
            [nx_obj.diode for nx_obj in nx_objects],
            node_name="diode",
            expected_dim=(1,),
            default_unit=_volt,
        )
        nx_instrument.diode.parent = nx_instrument

        nx_instrument.detector = NXdetector.concatenate(
            [nx_obj.detector for nx_obj in nx_objects],
            node_name="detector",
        )
        nx_instrument.detector.parent = nx_instrument

        return nx_instrument
