"""
Module for handling an `NXtransformations <https://manual.nexusformat.org/classes/base_classes/nxtransformations.html#nxtransformations>`_ group.
"""

from __future__ import annotations

import logging
from copy import deepcopy

import h5py

# For unit conversion using pint
import pint
from silx.io.dictdump import nxtodict
from silx.io.utils import open as hdf5_open
from silx.utils.proxy import docstring

from nxtomo.nxobject.nxobject import NXobject
from nxtomo.paths.nxtomo import get_paths as get_nexus_paths
from nxtomo.utils.transformation import GravityTransformation, Transformation
from nxtomo.utils.transformation import get_lr_flip as _get_lr_flip
from nxtomo.utils.transformation import get_ud_flip as _get_ud_flip

_ureg = pint.UnitRegistry()

_logger = logging.getLogger(__name__)

__all__ = ["NXtransformations", "get_lr_flip", "get_ud_flip"]


class NXtransformations(NXobject):
    def __init__(self, node_name: str = "transformations", parent=None) -> None:
        """
        Collection of axis-based translations and rotations to describe a geometry.

        For tomotools the first usage would be to allow users to provide more metadata to tag acquisitions (like "detector has been rotated" by 90 degrees).

        :param node_name: name of the transformations group in the hierarchy.
        :param parent: parent in the NeXus hierarchy.
        """
        super().__init__(node_name, parent)
        self._set_freeze(False)
        self._transformations = dict()
        # dict with axis_name as key and Transformation as value.
        self._set_freeze(True)

    @property
    def transformations(self) -> tuple:
        """
        Return the registered transformations as a tuple.
        """
        return tuple(self._transformations.values())

    @transformations.setter
    def transformations(self, transformations: tuple):
        """
        :param transformations: iterable of Transformation instances
        """
        # check type
        if not isinstance(transformations, (tuple, list)):
            raise TypeError(
                f"transformations is expected to be a dict. {type(transformations)} provided instead"
            )
        for transformation in transformations:
            if not isinstance(transformation, Transformation):
                raise TypeError(
                    f"elements are expected to be instances of {Transformation}. {type(transformation)} provided instead"
                )
        # convert it to a dict for convenience
        self._transformations = {
            transformation.axis_name: transformation
            for transformation in transformations
        }

    def addTransformation(self, *args, **kwargs):
        _logger.warning(
            "addTransformation is deprecated. Please use add_transformation"
        )
        self.add_transformation(*args, **kwargs)

    def add_transformation(
        self, transformation: Transformation, overwrite=False, skip_if_exists=False
    ):
        """
        Add a transformation to the existing ones.

        :param transformation: transformation to be added
        :param overwrite: if a transformation with the same axis_name already exists then overwrite it
        :param skip_if_exists: if a transformation with the same axis_name already exists then keep the existing one
        :raises: KeyError, if a transformation with the same axis_name is already registered
        """
        if skip_if_exists is overwrite is True:
            raise ValueError(
                "both 'skip_if_exists' and 'overwrite' set to True. Undefined behavior"
            )
        if transformation.axis_name in self._transformations:
            if overwrite:
                _logger.info(
                    "A transformation over {transformation.axis_name} is already registered. Will overwrite it"
                )
            elif skip_if_exists:
                _logger.info(
                    "A transformation over {transformation.axis_name} is already registered. Skip add"
                )
                return
            else:
                raise KeyError(
                    f"A transformation over {transformation.axis_name} is already registered. axis_name must be unique"
                )

        self._transformations[transformation.axis_name] = transformation

    def rmTransformation(self, *args, **kwargs):
        _logger.warning("rmTransformation is deprecated. Please use rm_transformation")
        self.rm_transformation(*args, **kwargs)

    def rm_transformation(self, transformation: Transformation):
        """
        Remove the provided transformation from the list of existing transformations.

        :param transformation: transformation to be removed
        """
        self._transformations.pop(transformation.axis_name, None)

    @docstring(NXobject)
    def to_nx_dict(
        self,
        nexus_path_version: float | None = None,
        data_path: str | None = None,
        solve_empty_dependency: bool = False,
    ) -> dict:
        """
        Dump the NXtransformations to a dictionary.

        :param nexus_path_version: Nexus version number.
        :param data_path: Data path where transformations are stored.
        :param solve_empty_dependency: If True, transformations without dependency will be set to depend on gravity.
        """
        if len(self._transformations) == 0:
            # if no transformation, avoid creating the group
            return {}
        nexus_paths = get_nexus_paths(nexus_path_version)
        transformations_nexus_paths = nexus_paths.nx_transformations_paths
        if transformations_nexus_paths is None:
            _logger.info(
                f"no TRANSFORMATIONS provided for version {nexus_path_version}"
            )
            return {}

        transformations = deepcopy(self._transformations)
        # Preprocessing for gravity: set transformations with no dependency to depend on gravity.
        if solve_empty_dependency:
            transformations_needing_gravity = dict(
                filter(
                    lambda pair: pair[1].depends_on in (None, ""),
                    transformations.items(),
                )
            )
            if len(transformations_needing_gravity) > 0:
                gravity = GravityTransformation()
                gravity_name = gravity.axis_name
                if gravity_name in transformations.keys():
                    _logger.warning(
                        f"transformations already contains a transformation named '{gravity.axis_name}'. Unable to expand transformation chain (cannot append gravity twice)"
                    )
                else:
                    transformations[gravity_name] = gravity
                # Update transformations needing gravity
                for transformation in transformations_needing_gravity.values():
                    transformation.depends_on = gravity_name

        # Dump each Transformation to a dictionary and adjust the units mapping.
        nx_dict = {}
        for transformation in transformations.values():
            if not isinstance(transformation, Transformation):
                raise TypeError(
                    f"transformations are expected to be instances of {Transformation}. {type(transformation)} provided instead."
                )
            trans_dict = transformation.to_nx_dict(
                transformations_nexus_paths=transformations_nexus_paths,
                data_path=self.path,
            )
            # Adjust unit strings and values according to Nexus conventions:
            # - For rotations, convert to radians and use unit "rad"
            # - For translations, use "m" for meter.
            for key in list(trans_dict.keys()):
                if key.endswith("@units"):
                    unit = trans_dict[key]
                    if unit in ("degree", "degrees") or unit in (
                        "radian",
                        "radians",
                        "rad",
                    ):
                        # Convert the transformation value to degrees regardless of the input unit.
                        q_deg = transformation.transformation_values.to(_ureg.degree)
                        if self.path:
                            value_key = f"{self.path}/{transformation.axis_name}"
                        else:
                            value_key = transformation.axis_name
                        trans_dict[value_key] = q_deg.magnitude
                        trans_dict[key] = "degree"
                    elif unit in ("meter", "meters"):
                        trans_dict[key] = "m"
                    elif unit in ("m/s2", "m/s^2", "m/s**2", "meter / second ** 2"):
                        trans_dict[key] = "m/s^2"
            nx_dict.update(trans_dict)
        nx_dict[f"{self.path}@NX_class"] = "NX_transformations"
        nx_dict[f"{self.path}@units"] = "NX_TRANSFORMATION"
        return nx_dict

    @staticmethod
    def load_from_file(file_path: str, data_path: str, nexus_version: float | None):
        """
        Create an instance of :class:`NXtransformations` and load its value from
        the given file and data path.
        """
        result = NXtransformations()
        return result._load(
            file_path=file_path, data_path=data_path, nexus_version=nexus_version
        )

    def _load(
        self, file_path: str, data_path: str, nexus_version: float | None
    ) -> NXobject:
        """
        Create and load an NXtransformations group from data on disk.
        """
        nexus_paths = get_nexus_paths(nexus_version)
        transformations_nexus_paths = nexus_paths.nx_transformations_paths

        with hdf5_open(file_path) as h5f:
            if data_path == "":
                pass
            elif data_path not in h5f:
                _logger.error(
                    f"No NXtransformations found in {file_path} under {data_path} location."
                )
                return

        transformations_as_nx_dict = nxtodict(file_path, path=data_path)
        # Filter attributes from the dict (as a convention dict contains '@' char)
        transformations_keys = dict(
            filter(lambda a: "@" not in a[0], transformations_as_nx_dict.items())
        )
        for key in transformations_keys:
            transformation = Transformation.from_nx_dict(
                axis_name=key,
                dict_=transformations_as_nx_dict,
                transformations_nexus_paths=transformations_nexus_paths,
            )
            if transformation is None:
                # if failed to load transformation (old version of Nexus?)
                continue
            else:
                self.add_transformation(transformation=transformation)
        return self

    @staticmethod
    @docstring(NXobject)
    def concatenate(nx_objects: tuple, node_name="transformations"):
        res = NXtransformations(node_name=node_name)
        for nx_transformations in nx_objects:
            if not isinstance(nx_transformations, NXtransformations):
                raise TypeError(
                    f"can only concatenate {NXtransformations}. Not {type(nx_transformations)}"
                )
            for transformation in nx_transformations.transformations:
                res.add_transformation(transformation, skip_if_exists=True)
        return res

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, NXtransformations):
            return False
        else:
            # To check equality we filter gravity as it can be provided at the end and as the reference.
            def is_not_gravity(transformation):
                return transformation != GravityTransformation()

            return list(filter(is_not_gravity, self.transformations)) == list(
                filter(is_not_gravity, __value.transformations)
            )

    @staticmethod
    def is_a_valid_group(group: h5py.Group) -> bool:
        """
        Check if the group represents an NXtransformations.
        For now the only condition is to be a group and have NXtransformations as an attribute.
        """
        if not isinstance(group, h5py.Group):
            return False
        return group.attrs.get("NX_class", None) in (
            "NX_transformations",
            "NX_TRANSFORMATIONS",
        )

    def __len__(self):
        return len(self.transformations)


def get_lr_flip(transformations: tuple | NXtransformations) -> tuple:
    """
    Check along all transformations for those matching a left-right flip.

    Return a tuple with all matching transformations.
    """
    if isinstance(transformations, NXtransformations):
        transformations = transformations.transformations
    return _get_lr_flip(transformations)


def get_ud_flip(transformations: tuple | NXtransformations) -> tuple:
    """
    Check along all transformations for those matching an up-down flip.

    Return a tuple with all matching transformations.
    """
    if isinstance(transformations, NXtransformations):
        transformations = transformations.transformations
    return _get_ud_flip(transformations)
