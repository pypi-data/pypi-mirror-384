"""
Module for handling an `NXsample <https://manual.nexusformat.org/classes/base_classes/NXsample.html>`_.
"""

from __future__ import annotations

import logging
from functools import partial
from operator import is_not

import numpy
import pint
from silx.utils.proxy import docstring

from nxtomo.nxobject.nxobject import NXobject
from nxtomo.nxobject.nxtransformations import NXtransformations
from nxtomo.nxobject.utils.concatenate import concatenate_pint_quantities
from nxtomo.nxobject.utils.decorator import check_dimensionality
from nxtomo.nxobject.utils.ObjectWithPixelSizeMixIn import _ObjectWithPixelSizeMixIn
from nxtomo.paths.nxtomo import get_paths as get_nexus_paths
from nxtomo.utils import get_data, get_quantity

_logger = logging.getLogger(__name__)

__all__ = [
    "NXsample",
]

_ureg = pint.UnitRegistry()
_meter = _ureg.meter
_degree = _ureg.degree


class NXsample(NXobject, _ObjectWithPixelSizeMixIn):
    def __init__(self, node_name="sample", parent: NXobject | None = None) -> None:
        """
        Representation of `NeXus NXsample <https://manual.nexusformat.org/classes/base_classes/NXsample.html>`_.
        Metadata describing the sample.

        :param node_name: name of the sample in the hierarchy.
        :param parent: parent in the NeXus hierarchy.
        """
        NXobject.__init__(self, node_name=node_name, parent=parent)
        self._set_freeze(False)
        _ObjectWithPixelSizeMixIn.__init__(self)

        self._name = None
        self._rotation_angle = None
        self._x_translation: pint.Quantity | None = None
        self._y_translation: pint.Quantity | None = None
        self._z_translation: pint.Quantity | None = None
        self._propagation_distance: pint.Quantity | None = None
        self._transformations = tuple()
        self._set_freeze(True)

    @property
    def name(self) -> str | None:
        """Sample name."""
        return self._name

    @name.setter
    def name(self, name: str | None) -> None:
        if not isinstance(name, (type(None), str)):
            raise TypeError(f"name is expected to be None or str not {type(name)}")
        self._name = name

    @property
    def rotation_angle(self) -> pint.Quantity | None:
        """Sample rotation angle (one value per frame)."""
        return self._rotation_angle

    @rotation_angle.setter
    @check_dimensionality("[]")
    def rotation_angle(self, rotation_angle: None | pint.Quantity):
        self._rotation_angle = rotation_angle

    @property
    def x_translation(self) -> pint.Quantity | None:
        """Sample translation along X. See `modelling at ESRF <https://tomo.gitlab-pages.esrf.fr/ebs-tomo/master/modelization.html>`_ for more information."""
        return self._x_translation

    @x_translation.setter
    @check_dimensionality("[length]")
    def x_translation(self, x_translation: None | pint.Quantity):
        self._x_translation = x_translation

    @property
    def y_translation(self) -> pint.Quantity | None:
        """Sample translation along Y. See `modelling at ESRF <https://tomo.gitlab-pages.esrf.fr/ebs-tomo/master/modelization.html>`_ for more information."""
        return self._y_translation

    @y_translation.setter
    @check_dimensionality("[length]")
    def y_translation(self, y_translation: None | pint.Quantity):
        self._y_translation = y_translation

    @property
    def z_translation(self) -> pint.Quantity | None:
        """Sample translation along Z. See `modelling at ESRF <https://tomo.gitlab-pages.esrf.fr/ebs-tomo/master/modelization.html>`_ for more information."""
        return self._z_translation

    @z_translation.setter
    @check_dimensionality("[length]")
    def z_translation(self, z_translation: None | pint.Quantity):
        self._z_translation = z_translation

    @property
    def propagation_distance(self) -> pint.Quantity | None:
        return self._propagation_distance

    @propagation_distance.setter
    @check_dimensionality("[length]")
    def propagation_distance(self, value: pint.Quantity | None):
        self._propagation_distance = value

    @property
    def transformations(self) -> tuple[NXtransformations]:
        """Sample transformations as `NXtransformations <https://manual.nexusformat.org/classes/base_classes/NXtransformations.html>`_."""
        return self._transformations

    @transformations.setter
    def transformations(self, transformations: tuple[NXtransformations]):
        if not isinstance(transformations, tuple):
            raise TypeError(
                f"transformations expects a tuple. Got {type(transformations)}"
            )
        for transformation in transformations:
            if not isinstance(transformation, NXtransformations):
                raise TypeError(
                    f"transformations should be a tuple of {NXtransformations}. Contains {type(transformation)}"
                )

    @docstring(NXobject)
    def to_nx_dict(
        self,
        nexus_path_version: float | None = None,
        data_path: str | None = None,
    ) -> dict:
        nexus_paths = get_nexus_paths(nexus_path_version)
        nexus_sample_paths = nexus_paths.nx_sample_paths
        x_pixel_size_path = (
            "/".join([self.path, nexus_sample_paths.X_PIXEL_SIZE])
            if nexus_sample_paths.X_PIXEL_SIZE is not None
            else None
        )
        y_pixel_size_path = (
            "/".join([self.path, nexus_sample_paths.Y_PIXEL_SIZE])
            if nexus_sample_paths.Y_PIXEL_SIZE is not None
            else None
        )

        nx_dict = _ObjectWithPixelSizeMixIn.to_nx_dict(
            self,
            x_pixel_size_path=x_pixel_size_path,
            y_pixel_size_path=y_pixel_size_path,
        )

        if self.name is not None:
            path_name = f"{self.path}/{nexus_sample_paths.NAME}"
            nx_dict[path_name] = self.name
        if self.rotation_angle is not None:
            path_rotation_angle = f"{self.path}/{nexus_sample_paths.ROTATION_ANGLE}"
            nx_dict[path_rotation_angle] = self.rotation_angle
            nx_dict["@".join([path_rotation_angle, "units"])] = "degree"
        if self.x_translation is not None:
            path_x_translation = f"{self.path}/{nexus_sample_paths.X_TRANSLATION}"
            nx_dict[path_x_translation] = self.x_translation.magnitude
            nx_dict["@".join([path_x_translation, "units"])] = (
                f"{self.x_translation.units:~}"
            )
        if self.y_translation is not None:
            path_y_translation = f"{self.path}/{nexus_sample_paths.Y_TRANSLATION}"
            nx_dict[path_y_translation] = self.y_translation.magnitude
            nx_dict["@".join([path_y_translation, "units"])] = (
                f"{self.y_translation.units:~}"
            )
        if self.z_translation is not None:
            path_z_translation = f"{self.path}/{nexus_sample_paths.Z_TRANSLATION}"
            nx_dict[path_z_translation] = self.z_translation.magnitude
            nx_dict["@".join([path_z_translation, "units"])] = (
                f"{self.z_translation.units:~}"
            )

        if (
            self.propagation_distance is not None
            and nexus_sample_paths.PROPAGATION_DISTANCE is not None
        ):
            path_propagation_distance = (
                f"{self.path}/{nexus_sample_paths.PROPAGATION_DISTANCE}"
            )
            nx_dict[path_propagation_distance] = self.propagation_distance
            nx_dict["@".join([path_propagation_distance, "units"])] = (
                f"{self.propagation_distance.units:~}"
            )

        if nx_dict != {}:
            nx_dict[f"{self.path}@NX_class"] = "NXsample"
        return nx_dict

    def _load(self, file_path: str, data_path: str, nexus_version: float) -> NXobject:
        """
        Create and load an NXsample from data on disk.
        """
        nexus_paths = get_nexus_paths(nexus_version)
        nexus_sample_paths = nexus_paths.nx_sample_paths

        _ObjectWithPixelSizeMixIn._load(
            self,
            file_path=file_path,
            x_pixel_size_path=(
                "/".join([data_path, nexus_sample_paths.X_PIXEL_SIZE])
                if nexus_sample_paths.X_PIXEL_SIZE
                else None
            ),
            y_pixel_size_path=(
                "/".join([data_path, nexus_sample_paths.Y_PIXEL_SIZE])
                if nexus_sample_paths.Y_PIXEL_SIZE
                else None
            ),
        )

        self.name = get_data(
            file_path=file_path,
            data_path="/".join([data_path, nexus_sample_paths.NAME]),
        )
        self.rotation_angle = get_quantity(
            file_path=file_path,
            data_path="/".join([data_path, nexus_sample_paths.ROTATION_ANGLE]),
            default_unit=_degree,
        )
        self.x_translation = get_quantity(
            file_path=file_path,
            data_path="/".join([data_path, nexus_sample_paths.X_TRANSLATION]),
            default_unit=_meter,
        )
        self.y_translation = get_quantity(
            file_path=file_path,
            data_path="/".join([data_path, nexus_sample_paths.Y_TRANSLATION]),
            default_unit=_meter,
        )
        self.z_translation = get_quantity(
            file_path=file_path,
            data_path="/".join([data_path, nexus_sample_paths.Z_TRANSLATION]),
            default_unit=_meter,
        )
        if nexus_sample_paths.PROPAGATION_DISTANCE is not None:
            self.propagation_distance = get_quantity(
                file_path=file_path,
                data_path="/".join(
                    [data_path, nexus_sample_paths.PROPAGATION_DISTANCE]
                ),
                default_unit=_meter,
            )

    @staticmethod
    @docstring(NXobject)
    def concatenate(nx_objects: tuple, node_name="sample"):
        nx_objects = tuple(filter(partial(is_not, None), nx_objects))
        # filter None obj
        if len(nx_objects) == 0:
            return None
        # warning: later we make the assumption that nx_objects contains at least one element
        for nx_obj in nx_objects:
            if not isinstance(nx_obj, NXsample):
                raise TypeError("Cannot concatenate non-NXsample object")

        nx_sample = NXsample(node_name)
        _logger.info(f"sample name {nx_objects[0].name} will be picked")
        nx_sample.name = nx_objects[0].name
        _ObjectWithPixelSizeMixIn.concatenate(nx_sample, nx_objects=nx_objects)

        propagation_distance = nx_objects[0].propagation_distance
        if propagation_distance is not None:
            _logger.info(
                f"sample propagation distance {propagation_distance} will be picked"
            )
            nx_sample.propagation_distance = nx_objects[0].propagation_distance
            nx_sample.propagation_distance.unit = nx_objects[
                0
            ].propagation_distance.units

        rotation_angles = [
            nx_obj.rotation_angle
            for nx_obj in nx_objects
            if nx_obj.rotation_angle is not None
        ]
        if rotation_angles:
            nx_sample.rotation_angle = numpy.concatenate(rotation_angles)

        def get_quantities(attr_name):
            values = [
                getattr(nx_obj, attr_name)
                for nx_obj in nx_objects
                if getattr(nx_obj, attr_name) is not None
            ]
            return values

        # Translation attributes
        nx_sample.x_translation = concatenate_pint_quantities(
            get_quantities("x_translation")
        )
        nx_sample.y_translation = concatenate_pint_quantities(
            get_quantities("y_translation")
        )
        nx_sample.z_translation = concatenate_pint_quantities(
            get_quantities("z_translation")
        )

        _ObjectWithPixelSizeMixIn.concatenate(
            output_nx_object=nx_sample, nx_objects=nx_objects
        )

        return nx_sample
