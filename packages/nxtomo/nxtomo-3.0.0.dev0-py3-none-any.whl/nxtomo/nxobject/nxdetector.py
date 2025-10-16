"""
Module for handling an `NXdetector <https://manual.nexusformat.org/classes/base_classes/NXdetector.html>`_.
"""

from __future__ import annotations

import os
from functools import partial
from operator import is_not
from typing import Iterable

import h5py
import numpy
import pint
from h5py import VirtualSource
from h5py import h5s as h5py_h5s
from silx.io.url import DataUrl
from silx.io.utils import open as hdf5_open
from silx.utils.enum import Enum as _Enum
from silx.utils.proxy import docstring

from nxtomo.io import from_virtual_source_to_data_url
from nxtomo.nxobject.nxobject import NXobject
from nxtomo.nxobject.nxtransformations import (
    NXtransformations,
    get_lr_flip,
    get_ud_flip,
)
from nxtomo.nxobject.utils.decorator import check_dimensionality
from nxtomo.nxobject.utils.ObjectWithPixelSizeMixIn import (
    _ObjectWithPixelSizeMixIn,
    check_quantity_consistency,
)
from nxtomo.paths.nxtomo import get_paths as get_nexus_path
from nxtomo.utils import cast_and_check_array_1D, get_data, get_quantity
from nxtomo.utils.frameappender import FrameAppender
from nxtomo.utils.io import deprecated, ignore_deprecation_warning
from nxtomo.utils.transformation import DetXFlipTransformation, DetYFlipTransformation

try:
    from h5py._hl.vds import VDSmap
except ImportError:
    has_VDSmap = False
else:
    has_VDSmap = True
import logging

import h5py._hl.selections as selection

_logger = logging.getLogger(__name__)


__all__ = ["FOV", "ImageKey", "FieldOfView", "NXdetector", "NXdetectorWithUnit"]

_ureg = pint.UnitRegistry()
_meter = _ureg.meter
_second = _ureg.second


class FOV(_Enum):
    """
    Possible field-of-view values. Use cases are described `here <https://tomotools.gitlab-pages.esrf.fr/tomoscan/language/half_acquisition.html?highlight=half>`_.

    """

    @classmethod
    def from_value(cls, value):
        if isinstance(value, str):
            value = value.lower().title()

        return FOV(value)

    FULL = "Full"
    """We expect to have the full dataset in the field of view."""
    HALF = "Half"
    """We expect to have half of the dataset in the field of view—around 360 degrees. Reconstruction will generate a sinogram of the full dataset."""


FieldOfView = FOV


class ImageKey(_Enum):
    """
    NXdetector `image_key <https://manual.nexusformat.org/classes/base_classes/NXdetector.html#image_key>`_.
    Used to distinguish different frame types.
    """

    ALIGNMENT = -1
    """Used for alignment frames (also known as alignment images)."""
    PROJECTION = 0
    """Projection frames."""
    FLAT_FIELD = 1
    """Flat frames."""
    DARK_FIELD = 2
    """Dark frames."""
    INVALID = 3
    """Invalid frames (ignored during analysis)."""


class NXdetector(NXobject, _ObjectWithPixelSizeMixIn):
    def __init__(
        self,
        node_name="detector",
        parent: NXobject | None = None,
        field_of_view: FOV | None = None,
        expected_dim: tuple | None = None,
    ) -> None:
        """
        Representation of `NeXus NXdetector <https://manual.nexusformat.org/classes/base_classes/NXdetector.html>`_.
        Detector of the acquisition.

        :param node_name: name of the detector in the hierarchy.
        :param parent: parent in the NeXus hierarchy.
        :param field_of_view: field of view of the detector, if known.
        :param expected_dim: expected data dimensions, provided as a tuple of ints to be checked when data is set.
        """
        NXobject.__init__(self, node_name=node_name, parent=parent)
        self._set_freeze(False)
        _ObjectWithPixelSizeMixIn.__init__(self)

        self._expected_dim = expected_dim

        self._data = None
        self.image_key_control = None
        self._transformations = NXtransformations(parent=self)
        self._distance = None  # detector / sample distance
        self.field_of_view = field_of_view
        self._count_time = None
        self.tomo_n = None
        self.group_size = None
        self._roi = None
        self.__master_vds_file = None
        # used to record the virtual dataset set file origin in order to solve relative links
        self._x_rotation_axis_pixel_position: float | None = None
        self._y_rotation_axis_pixel_position: float | None = None
        self._sequence_number: numpy.ndarray[numpy.uint32] | None = None
        """Index of each frame on the acquisition sequence"""

        # as the class is 'freeze' we need to set 'estimated_cor_from_motor' once to make sure the API still exists.
        # the logger filtering avoid to have deprecation logs...
        with ignore_deprecation_warning():
            self.estimated_cor_from_motor = None
        self._set_freeze(True)

    @property
    def data(self) -> numpy.ndarray | tuple | None:
        """
        Detector data (frames).
        Can be None, a NumPy array, or a collection of DataUrl or h5py.VirtualSource objects.
        """
        return self._data

    @data.setter
    def data(self, data: numpy.ndarray | tuple | None):
        if isinstance(data, (tuple, list)) or (
            isinstance(data, numpy.ndarray)
            and data.ndim == 1
            and (self._expected_dim is None or len(self._expected_dim) > 1)
        ):
            for elmt in data:
                if has_VDSmap:
                    if not isinstance(elmt, (DataUrl, VirtualSource, VDSmap)):
                        raise TypeError(
                            f"element of 'data' are expected to be a {len(self._expected_dim)}D numpy array, a list of silx DataUrl or a list of h5py virtualSource. Not {type(elmt)}"
                        )
            data = tuple(data)
        elif isinstance(data, numpy.ndarray):
            if (
                self._expected_dim is not None
                and data is not None
                and data.ndim not in self._expected_dim
            ):
                raise ValueError(
                    f"data is expected to be {len(self._expected_dim)}D not {data.ndim}D"
                )
        elif data is None:
            pass
        else:
            raise TypeError(
                f"data is expected to be an instance of {numpy.ndarray}, None or a list of silx DataUrl or h5py Virtual Source. Not {type(data)}"
            )
        self._data = data

    @property
    def x_rotation_axis_pixel_position(self) -> float:
        """
        Absolute position of the center of rotation in the detector space in X (X being the abscissa).
        Units: pixel.
        """
        return self._x_rotation_axis_pixel_position

    @x_rotation_axis_pixel_position.setter
    def x_rotation_axis_pixel_position(self, value: float | None) -> None:
        if not isinstance(value, (float, type(None))):
            raise TypeError(
                f"x_rotation_axis_pixel_position is expected ot be an instance of {float} or None. Not {type(value)}"
            )
        self._x_rotation_axis_pixel_position = value

    @property
    def y_rotation_axis_pixel_position(self) -> float:
        """
        Absolute position of the center of rotation in the detector space in Y (Y being the ordinate).
        Units: pixel.

        .. warning::

            This field is not handled at the moment by tomotools. Only the X position is handled.
        """
        return self._y_rotation_axis_pixel_position

    @y_rotation_axis_pixel_position.setter
    def y_rotation_axis_pixel_position(self, value: float | None) -> None:
        if not isinstance(value, (float, type(None))):
            raise TypeError(
                f"y_rotation_axis_pixel_position is expected to be an instance of {float} or None. Not {type(value)}"
            )
        self._y_rotation_axis_pixel_position = value

    def set_transformation_from_x_flipped(self, flipped: bool | None):
        """Utility function to set transformations from a simple `x_flipped` boolean ((x in the **detector** coordinate system)).
        Used for backward compatibility and convenience.
        """
        # WARNING: moving from two simple boolean to full NXtransformations make the old API very weak. It should be removed
        # soon (but we want to keep the API for at least one release). This is expected to fail except if you stick to {x,y} flips
        if isinstance(flipped, numpy.bool_):
            flipped = bool(flipped)
        if not isinstance(flipped, (bool, type(None))):
            raise TypeError(
                f"x_flipped should be either a (python) boolean or None and is {flipped}, of type {type(flipped)}."
            )
        current_lr_transfs = get_lr_flip(self.transformations)
        for transf in current_lr_transfs:
            self.transformations.rm_transformation(transformation=transf)

        self.transformations.add_transformation(DetYFlipTransformation(flip=flipped))

    def set_transformation_from_y_flipped(self, flipped: bool | None):
        """
        Util function to set a detector transformation (y in the **detector** coordinate system).
        """
        # WARNING: moving from two simple boolean to full NXtransformations make the old API very weak. It should be removed
        # soon (but we want to keep the API for at least one release). This is expected to fail except if you stick to {x,y} flips
        if isinstance(flipped, numpy.bool_):
            flipped = bool(flipped)
        if not isinstance(flipped, (bool, type(None))):
            raise TypeError(
                f"y_flipped should be either a (python) boolean or None and is {flipped}, of type {type(flipped)}."
            )

        current_ud_transfs = get_ud_flip(self.transformations)
        for transf in current_ud_transfs:
            self.transformations.rm_transformation(transf)

        self.transformations.add_transformation(DetXFlipTransformation(flip=flipped))

    @property
    def distance(self) -> pint.Quantity | None:
        """
        sample / detector distance as a pint Quantity.
        """
        return self._distance

    @distance.setter
    @check_dimensionality(expected_dimension="[length]")
    def distance(self, value: pint.Quantity | None) -> None:
        self._distance = value

    @property
    def field_of_view(self) -> FieldOfView | None:
        """
        Detector :class:`~nxtomo.nxobject.nxdetector.FieldOfView`.
        """
        return self._field_of_view

    @field_of_view.setter
    def field_of_view(self, field_of_view: FieldOfView | str | None) -> None:
        if field_of_view is not None:
            field_of_view = FOV.from_value(field_of_view)
        self._field_of_view = field_of_view

    @property
    def count_time(self) -> pint.Quantity | None:
        return self._count_time

    @count_time.setter
    @check_dimensionality(expected_dimension="[time]")
    def count_time(self, count_time: None | pint.Quantity):
        self._count_time = count_time

    @property
    @deprecated(
        replacement="x_rotation_axis_pixel_position",
        reason="exists in nexus standard",
        since_version="1.3",
    )
    def estimated_cor_from_motor(self) -> float | None:
        """
        Hint of the center of rotation in pixels read from the motor (when possible).
        """
        return self._x_rotation_axis_pixel_position

    @estimated_cor_from_motor.setter
    @deprecated(
        replacement="x_rotation_axis_pixel_position",
        reason="exists in nexus standard",
        since_version="1.3",
    )
    def estimated_cor_from_motor(self, estimated_cor_from_motor: float | None):
        self._x_rotation_axis_pixel_position = estimated_cor_from_motor

    @property
    def image_key_control(self) -> numpy.ndarray | None:
        """
        :class:`~nxtomo.nxobject.nxdetector.ImageKey` for each frame.
        """
        return self._image_key_control

    @image_key_control.setter
    def image_key_control(self, control_image_key: Iterable | None):
        control_image_key = cast_and_check_array_1D(
            control_image_key, "control_image_key"
        )
        if control_image_key is None:
            self._image_key_control = None
        else:
            # cast all value to instances of ImageKey
            self._image_key_control = numpy.asarray(
                [ImageKey(key) for key in control_image_key]
            )

    @property
    def image_key(self) -> numpy.ndarray | None:
        """
        :class:`~nxtomo.nxobject.nxdetector.ImageKey` for each frame. Replace all
        :class:`~nxtomo.nxobject.nxdetector.ImageKey.ALIGNMENT` values with
        :class:`~nxtomo.nxobject.nxdetector.ImageKey.PROJECTION` to fulfill the NeXus standard.
        """
        if self.image_key_control is None:
            return None
        else:
            control_image_key = self.image_key_control.copy()
            control_image_key[control_image_key == ImageKey.ALIGNMENT] = (
                ImageKey.PROJECTION
            )
            return control_image_key

    @property
    def tomo_n(self) -> int | None:
        """
        Expected number of :class:`~nxtomo.nxobject.nxdetector.ImageKey.PROJECTION` frames.
        """
        return self._tomo_n

    @tomo_n.setter
    def tomo_n(self, tomo_n: int | None):
        self._tomo_n = tomo_n

    @property
    def group_size(self) -> int | None:
        """
        Number of acquisitions for the dataset.
        """
        return self._group_size

    @group_size.setter
    def group_size(self, group_size: int | None):
        self._group_size = group_size

    @property
    def roi(self) -> tuple | None:
        """
        Detector region of interest as (x0, y0, x1, y1).
        """
        return self._roi

    @roi.setter
    def roi(self, roi: tuple | None) -> None:
        if roi is None:
            self._roi = None
        elif not isinstance(roi, (tuple, list, numpy.ndarray)):
            raise TypeError("roi is expected to be None or a tuple")
        elif len(roi) != 4:
            raise ValueError(
                f"roi is expected to contains four elements. Get {len(roi)}"
            )
        else:
            self._roi = tuple(roi)

    @property
    def sequence_number(self) -> numpy.ndarray[numpy.uint32] | None:
        return self._sequence_number

    @sequence_number.setter
    def sequence_number(self, values: numpy.ndarray[numpy.uint32] | None):
        if values is None:
            self._sequence_number = None
        elif (
            isinstance(values, numpy.ndarray)
            and values.dtype == numpy.uint32
            and values.ndim == 1
        ):
            self._sequence_number = values
        else:
            raise TypeError(
                f"'values' is expected to be None or a 1D numpy array of uint32. Got {type(values)}"
            )

    @docstring(NXobject)
    def to_nx_dict(
        self,
        nexus_path_version: float | None = None,
        data_path: str | None = None,
    ) -> dict:
        nexus_paths = get_nexus_path(nexus_path_version)
        nexus_detector_paths = nexus_paths.nx_detector_paths
        x_pixel_size_path = (
            "/".join([self.path, nexus_detector_paths.X_PIXEL_SIZE])
            if nexus_detector_paths.X_PIXEL_SIZE is not None
            else None
        )
        y_pixel_size_path = (
            "/".join([self.path, nexus_detector_paths.Y_PIXEL_SIZE])
            if nexus_detector_paths.Y_PIXEL_SIZE is not None
            else None
        )
        nx_dict = _ObjectWithPixelSizeMixIn.to_nx_dict(
            self,
            x_pixel_size_path=x_pixel_size_path,
            y_pixel_size_path=y_pixel_size_path,
        )

        # image key control
        if self.image_key_control is not None:
            path_img_key = f"{self.path}/{nexus_detector_paths.IMAGE_KEY}"
            nx_dict[path_img_key] = [img_key.value for img_key in self.image_key]
            path_img_key_ctrl = f"{self.path}/{nexus_detector_paths.IMAGE_KEY_CONTROL}"
            nx_dict[path_img_key_ctrl] = [
                img_key.value for img_key in self.image_key_control
            ]
        # distance
        if self.distance is not None:
            path_distance = f"{self.path}/{nexus_detector_paths.DISTANCE}"
            nx_dict[path_distance] = self.distance.magnitude
            nx_dict["@".join([path_distance, "units"])] = f"{self.distance.units:~}"
        # FOV
        if self.field_of_view is not None:
            path_fov = f"{self.path}/{nexus_detector_paths.FOV}"
            nx_dict[path_fov] = self.field_of_view.value
        # count time
        if self.count_time is not None:
            path_count_time = f"{self.path}/{nexus_detector_paths.EXPOSURE_TIME}"
            nx_dict[path_count_time] = self.count_time.magnitude
            nx_dict["@".join([path_count_time, "units"])] = f"{self.count_time.units:~}"
        # tomo n
        if self.tomo_n is not None:
            tomo_n_fov_path = f"{nexus_paths.TOMO_N_SCAN}"
            nx_dict[tomo_n_fov_path] = self.tomo_n
        if self.group_size is not None:
            group_size_path = f"{self.path}/{nexus_paths.GRP_SIZE_ATTR}"
            nx_dict[group_size_path] = self.group_size
        # sequence number
        if (
            self.sequence_number is not None
            and nexus_detector_paths.SEQUENCE_NUMBER is not None
        ):
            sequence_number_path = f"{self.path}/{nexus_detector_paths.SEQUENCE_NUMBER}"
            nx_dict[sequence_number_path] = self.sequence_number

        # x rotation axis position
        if self.x_rotation_axis_pixel_position is not None:
            x_rotation_axis_pixel_position_path = (
                nexus_detector_paths.X_ROTATION_AXIS_PIXEL_POSITION
                or nexus_detector_paths.ESTIMATED_COR_FRM_MOTOR
            )
            if x_rotation_axis_pixel_position_path is not None:
                x_rot_axis_pos_path = (
                    f"{self.path}/{x_rotation_axis_pixel_position_path}"
                )
                nx_dict[x_rot_axis_pos_path] = self.x_rotation_axis_pixel_position
                nx_dict[f"{x_rot_axis_pos_path}@units"] = "pixel"

        # y rotation axis position
        if (
            self.y_rotation_axis_pixel_position is not None
            and nexus_detector_paths.Y_ROTATION_AXIS_PIXEL_POSITION is not None
        ):
            y_rot_axis_pos_path = (
                f"{self.path}/{nexus_detector_paths.Y_ROTATION_AXIS_PIXEL_POSITION}"
            )
            nx_dict[y_rot_axis_pos_path] = self.y_rotation_axis_pixel_position
            nx_dict[f"{y_rot_axis_pos_path}@units"] = "pixel"

        if self.roi is not None:
            path_roi = f"{self.path}/{nexus_detector_paths.ROI}"
            nx_dict[path_roi] = self.roi
            nx_dict["@".join([path_roi, "units"])] = "pixel"

        # export TRANSFORMATIONS
        nx_dict.update(
            self.transformations.to_nx_dict(
                nexus_path_version=nexus_path_version,
                data_path=data_path,
                solve_empty_dependency=True,
            )
        )

        # export detector data
        nx_dict.update(
            self._data_to_nx_dict(
                nexus_path_version=nexus_path_version,
                data_path=data_path,
            )
        )
        return nx_dict

    def _data_to_nx_dict(
        self,
        nexus_path_version: float | None = None,
        data_path: str | None = None,
    ) -> dict:
        nexus_paths = get_nexus_path(nexus_path_version)
        nexus_detector_paths = nexus_paths.nx_detector_paths

        nx_dict = {}
        if self.data is not None:
            # add data
            path_data = f"{self.path}/{nexus_detector_paths.DATA}"
            nx_dict[path_data] = self.data
            nx_dict["@".join([path_data, "interpretation"])] = "image"
            nx_dict["__vds_master_file__"] = self.__master_vds_file
            # add attributes to data
            nx_dict[f"{self.path}@NX_class"] = "NXdetector"
            nx_dict[f"{self.path}@signal"] = nexus_detector_paths.DATA
            nx_dict[f"{self.path}@SILX_style/axis_scale_types"] = [
                "linear",
                "linear",
            ]
        return nx_dict

    def _load(
        self, file_path: str, data_path: str, nexus_version: float, load_data_as: str
    ) -> None:
        possible_as_values = ("as_virtual_source", "as_data_url", "as_numpy_array")
        if load_data_as not in possible_as_values:
            raise ValueError(
                f"load_data_as is expected to be in {possible_as_values} and not {load_data_as}"
            )

        self.__master_vds_file = file_path
        # record the input file if we need to solve virtual dataset path from it

        nexus_paths = get_nexus_path(nexus_version)
        nexus_detector_paths = nexus_paths.nx_detector_paths

        data_dataset_path = f"{data_path}/{nexus_detector_paths.DATA}"

        def vs_file_path_to_real_path(file_path, vs_file_path):
            # get file path as absolute for the NXtomo. Simplify management of the
            # directories
            if os.path.isabs(vs_file_path):
                return vs_file_path
            else:
                return os.path.join(os.path.dirname(file_path), vs_file_path)

        # step 1: load frames
        with hdf5_open(file_path) as h5f:
            if data_dataset_path in h5f:
                dataset = h5f[data_dataset_path]
            else:
                _logger.error(f"unable to find {data_dataset_path} from {file_path}")
                return
            if load_data_as == "as_numpy_array":
                self.data = dataset[()]
            elif load_data_as == "as_data_url":
                if dataset.is_virtual:
                    urls = []
                    for vs_info in dataset.virtual_sources():
                        select_bounds = vs_info.vspace.get_select_bounds()
                        left_bound = select_bounds[0]
                        right_bound = select_bounds[1]
                        # warning: for now step is not managed with virtual
                        # dataset

                        length = right_bound[0] - left_bound[0] + 1
                        # warning: for now step is not managed with virtual
                        # dataset
                        virtual_source = h5py.VirtualSource(
                            vs_file_path_to_real_path(
                                file_path=file_path, vs_file_path=vs_info.file_name
                            ),
                            vs_info.dset_name,
                            vs_info.vspace.shape,
                        )
                        # here we could provide dataset but we won't to
                        # insure file path will be relative.
                        type_code = vs_info.src_space.get_select_type()
                        # check for unlimited selections in case where selection is regular
                        # hyperslab, which is the only allowed case for h5s.UNLIMITED to be
                        # in the selection
                        if (
                            type_code == h5py_h5s.SEL_HYPERSLABS
                            and vs_info.src_space.is_regular_hyperslab()
                        ):
                            (
                                source_start,
                                stride,
                                count,
                                block,
                            ) = vs_info.src_space.get_regular_hyperslab()
                            source_end = source_start[0] + length

                            sel = selection.select(
                                dataset.shape,
                                slice(source_start[0], source_end),
                                dataset=dataset,
                            )
                            virtual_source.sel = sel

                        urls.append(from_virtual_source_to_data_url(virtual_source))
                else:
                    urls = [
                        DataUrl(
                            file_path=file_path,
                            data_path=data_dataset_path,
                            scheme="silx",
                        )
                    ]
                self.data = urls
            elif load_data_as == "as_virtual_source":
                if dataset.is_virtual:
                    virtual_sources = []
                    for vs_info in dataset.virtual_sources():
                        u_vs_info = VDSmap(
                            vspace=vs_info.vspace,
                            file_name=vs_file_path_to_real_path(
                                file_path=file_path, vs_file_path=vs_info.file_name
                            ),
                            dset_name=vs_info.dset_name,
                            src_space=vs_info.src_space,
                        )

                        _, vs = FrameAppender._recreate_vs(
                            vs_info=u_vs_info, vds_file=file_path
                        )
                        virtual_sources.append(vs)
                    self.data = virtual_sources
                else:
                    raise ValueError(f"{data_dataset_path} is not virtual")

        # step 2: load metadata
        x_rotation_axis_pixel_position_path = (
            nexus_detector_paths.X_ROTATION_AXIS_PIXEL_POSITION
            or nexus_detector_paths.ESTIMATED_COR_FRM_MOTOR
        )
        if x_rotation_axis_pixel_position_path is not None:
            self.x_rotation_axis_pixel_position = get_data(
                file_path=file_path,
                data_path=f"{data_path}/{x_rotation_axis_pixel_position_path}",
            )

        if nexus_detector_paths.Y_ROTATION_AXIS_PIXEL_POSITION is not None:
            self.y_rotation_axis_pixel_position = get_data(
                file_path=file_path,
                data_path=f"{data_path}/{nexus_detector_paths.Y_ROTATION_AXIS_PIXEL_POSITION}",
            )

        # TODO Henri: create a function without the warning for the backward compatibility
        if nexus_detector_paths.X_FLIPPED is not None:
            self.set_transformation_from_x_flipped(
                get_data(
                    file_path=file_path,
                    data_path="/".join([data_path, nexus_detector_paths.X_FLIPPED]),
                )
            )
        if nexus_detector_paths.Y_FLIPPED is not None:
            self.set_transformation_from_y_flipped(
                get_data(
                    file_path=file_path,
                    data_path="/".join([data_path, nexus_detector_paths.Y_FLIPPED]),
                )
            )
        if nexus_detector_paths.NX_TRANSFORMATIONS is not None:
            transformations = self.load_transformations(
                file_path=file_path,
                data_path=data_path,
                nexus_version=nexus_version,
            )
            if transformations is not None:
                transformations.parent = self
                self.transformations = transformations

        try:
            self.distance = get_quantity(
                file_path=file_path,
                data_path="/".join([data_path, nexus_detector_paths.DISTANCE]),
                default_unit=_meter,
            )
        except TypeError as e:
            # in case loaded pixel size doesn't fit the type (case Diamond dataset)
            _logger.warning(f"Fail to load distance. Error is {e}")

        self.field_of_view = get_data(
            file_path=file_path,
            data_path="/".join([data_path, nexus_detector_paths.FOV]),
        )
        self.count_time = get_quantity(
            file_path=file_path,
            data_path="/".join([data_path, nexus_detector_paths.EXPOSURE_TIME]),
            default_unit=_second,
        )
        self.tomo_n = get_data(
            file_path=file_path,
            data_path="/".join([data_path, nexus_paths.TOMO_N_SCAN]),
        )
        self.group_size = get_data(
            file_path=file_path,
            data_path="/".join([data_path, nexus_paths.GRP_SIZE_ATTR]),
        )
        self.image_key_control = get_data(
            file_path=file_path,
            data_path="/".join([data_path, nexus_detector_paths.IMAGE_KEY_CONTROL]),
        )
        if self.image_key_control is None:
            # in the case image_key_control doesn't exists (dimaond dataset use case)
            self.image_key_control = get_data(
                file_path=file_path,
                data_path="/".join([data_path, nexus_detector_paths.IMAGE_KEY]),
            )
        if nexus_detector_paths.SEQUENCE_NUMBER is not None:
            self.sequence_number = get_data(
                file_path=file_path,
                data_path="/".join([data_path, nexus_detector_paths.SEQUENCE_NUMBER]),
            )
        roi = get_data(
            file_path=file_path,
            data_path="/".join([data_path, nexus_detector_paths.ROI]),
        )
        if roi is not None:
            self.roi = roi

        _ObjectWithPixelSizeMixIn._load(
            self,
            file_path=file_path,
            x_pixel_size_path=(
                "/".join([data_path, nexus_detector_paths.X_PIXEL_SIZE])
                if nexus_detector_paths.X_PIXEL_SIZE
                else None
            ),
            y_pixel_size_path=(
                "/".join([data_path, nexus_detector_paths.Y_PIXEL_SIZE])
                if nexus_detector_paths.Y_PIXEL_SIZE
                else None
            ),
        )

    @staticmethod
    def load_transformations(
        file_path: str, data_path: str, nexus_version
    ) -> NXtransformations | None:
        """
        Transformations are not stored at a fixed position: try to load them from
        the default location ('transformations'); otherwise, browse all HDF5 groups
        to retrieve an NXtransformations group.
        """
        nexus_paths = get_nexus_path(nexus_version)
        nexus_detector_paths = nexus_paths.nx_detector_paths

        with hdf5_open(file_path) as h5f:
            if data_path not in h5f:
                return None

            detector_grp = h5f[data_path]
            # filter valid groups (fitting NXtransformations definition)
            valid_data_paths = dict(
                filter(
                    lambda item: NXtransformations.is_a_valid_group(item[1]),
                    detector_grp.items(),
                )
            )

        if len(valid_data_paths) == 0:
            return None
        elif len(valid_data_paths) > 1:
            issue = "more than one NXtransformations group found"
            if nexus_detector_paths.NX_TRANSFORMATIONS in valid_data_paths:
                _logger.warning(
                    f"{issue}. Will pick the default path as there ({nexus_detector_paths.NX_TRANSFORMATIONS})"
                )
                return NXtransformations.load_from_file(
                    file_path=file_path,
                    data_path="/".join(
                        [data_path, nexus_detector_paths.NX_TRANSFORMATIONS]
                    ),
                    nexus_version=nexus_version,
                )
            raise ValueError(f"{issue} - ({valid_data_paths}). Unable to handle it")
        else:
            return NXtransformations.load_from_file(
                file_path=file_path,
                data_path="/".join([data_path, list(valid_data_paths.keys())[0]]),
                nexus_version=nexus_version,
            )

    @staticmethod
    def _concatenate_except_data(nx_detector, nx_objects: tuple):
        image_key_ctrl = [
            nx_obj.image_key_control
            for nx_obj in nx_objects
            if nx_obj.image_key_control is not None
        ]
        if len(image_key_ctrl) > 0:
            nx_detector.image_key_control = numpy.concatenate(image_key_ctrl)

        _ObjectWithPixelSizeMixIn.concatenate(
            output_nx_object=nx_detector, nx_objects=nx_objects
        )
        # note: image_key is deduced from image_key_control
        nx_detector.x_pixel_size = nx_objects[0].x_pixel_size
        nx_detector.roi = nx_objects[0].roi
        nx_detector.y_pixel_size = nx_objects[0].y_pixel_size
        nx_detector.x_rotation_axis_pixel_position = nx_objects[
            0
        ].x_rotation_axis_pixel_position
        nx_detector.y_rotation_axis_pixel_position = nx_objects[
            0
        ].y_rotation_axis_pixel_position
        nx_detector.roi = nx_objects[0].roi
        nx_detector.distance = nx_objects[0].distance
        nx_detector.field_of_view = nx_objects[0].field_of_view
        nx_detector.transformations = nx_objects[0].transformations
        for nx_obj in nx_objects[1:]:
            if nx_detector.transformations != nx_obj.transformations:
                _logger.warning(
                    f"found different NXTransformations. ({nx_detector.transformations.to_nx_dict()} vs {nx_obj.transformations.to_nx_dict()}). Pick the first one"
                )

            check_quantity_consistency(
                reference=nx_detector.distance,
                candidate=nx_obj.distance,
                label="detector distance",
                logger=_logger,
            )
            if (
                nx_detector.field_of_view
                and nx_detector.field_of_view != nx_obj.field_of_view
            ):
                _logger.warning(
                    f"found different field_of_view value. ({nx_detector.field_of_view} vs {nx_obj.field_of_view}). Pick the first one"
                )
            if nx_detector.roi != nx_obj.roi:
                _logger.warning(
                    f"found different detector roi value. ({nx_detector.roi} vs {nx_obj.roi}). Pick the first one"
                )

    @staticmethod
    @docstring(NXobject)
    def concatenate(nx_objects: tuple, node_name="detector"):
        # filter None obj
        nx_objects = tuple(filter(partial(is_not, None), nx_objects))
        if len(nx_objects) == 0:
            return None
        # warning: later we make the assumption that nx_objects contains at least one element
        for nx_obj in nx_objects:
            if not isinstance(nx_obj, NXdetector):
                raise TypeError("Cannot concatenate non NXinstrument object")

        nx_detector = NXdetector(node_name=node_name)
        NXdetector._concatenate_except_data(
            nx_objects=nx_objects, nx_detector=nx_detector
        )

        # now handle data on it's own
        detector_data = [
            nx_obj.data for nx_obj in nx_objects if nx_obj.data is not None
        ]
        if len(detector_data) > 0:
            if isinstance(detector_data[0], numpy.ndarray):
                # store_as = "as_numpy_array"
                expected = numpy.ndarray
            elif isinstance(detector_data[0], Iterable):
                if isinstance(detector_data[0][0], h5py.VirtualSource):
                    # store_as = "as_virtual_source"
                    expected = h5py.VirtualSource
                elif isinstance(detector_data[0][0], DataUrl):
                    # store_as = "as_data_url"
                    expected = DataUrl
                else:
                    raise TypeError(
                        f"detector data is expected to be a numpy array or a h5py.VirtualSource or a numpy array. {type(detector_data[0][0])} is not handled."
                    )
            else:
                raise TypeError(
                    f"detector data is expected to be a numpy array or a h5py.VirtualSource or a numpy array. {type(detector_data[0])} is not handled."
                )

            for data in detector_data:
                if expected in (DataUrl, h5py.VirtualSource):
                    # for DataUrl and VirtualSource check type of the element
                    cond = isinstance(data[0], expected)
                else:
                    cond = isinstance(data, expected)
                if not cond:
                    raise TypeError(
                        f"Incoherent data type cross detector data ({type(data)} when {expected} expected)"
                    )

            if expected in (DataUrl, h5py.VirtualSource):
                new_data = []
                [new_data.extend(data) for data in detector_data]
            else:
                new_data = numpy.concatenate(detector_data)
            nx_detector.data = new_data

        return nx_detector

    @property
    def transformations(self):
        """
        `NXtransformation <https://manual.nexusformat.org/classes/base_classes/NXtransformations.html>`_
        objects describing detector flips or manual rotations.
        """
        return self._transformations

    @transformations.setter
    def transformations(self, transformations: NXtransformations) -> None:
        self._transformations = transformations


class NXdetectorWithUnit(NXdetector):
    def __init__(
        self,
        default_unit: pint.Unit,
        node_name="detector",
        parent=None,
        field_of_view=None,
        expected_dim: tuple | None = None,
    ) -> None:
        self._default_unit = default_unit
        super().__init__(node_name, parent, field_of_view, expected_dim)
        self._data = None

    @property
    def data(self) -> pint.Quantity | None:
        """
        Detector data.
        Can be a NumPy array, list of DataUrl objects, VirtualSource instances, or a pint.Quantity.
        """
        return self._data

    @data.setter
    def data(self, data: pint.Quantity | numpy.ndarray | tuple | None):
        if isinstance(data, pint.Quantity):
            # Ensure that the magnitude is a NumPy array
            if not isinstance(data.magnitude, numpy.ndarray):
                raise TypeError(
                    "pint.Quantity must have a NumPy array as its magnitude."
                )
            if (
                self._expected_dim is not None
                and data.magnitude.ndim not in self._expected_dim
            ):
                raise ValueError(
                    f"data is expected to be {len(self._expected_dim)}D, not {data.magnitude.ndim}D"
                )
        elif isinstance(data, (tuple, list)) or (
            isinstance(data, numpy.ndarray)
            and data.ndim == 1
            and (self._expected_dim is None or len(self._expected_dim) > 1)
        ):
            for elmt in data:
                if has_VDSmap:
                    if not isinstance(elmt, (DataUrl, VirtualSource, VDSmap)):
                        raise TypeError(
                            f"Elements of 'data' are expected to be a {len(self._expected_dim)}D numpy array, "
                            f"a list of silx DataUrl, or a list of h5py VirtualSource. Not {type(elmt)}."
                        )
            data = tuple(data)
        elif isinstance(data, numpy.ndarray):
            if self._expected_dim is not None and data.ndim not in self._expected_dim:
                raise ValueError(
                    f"data is expected to be {len(self._expected_dim)}D, not {data.ndim}D"
                )
        elif data is None:
            pass
        else:
            raise TypeError(
                f"data is expected to be a pint.Quantity, numpy.ndarray, None, or a list of silx DataUrl/h5py Virtual Source. "
                f"Not {type(data)}."
            )

        self._data = data

    def _data_to_nx_dict(
        self,
        nexus_path_version: float | None = None,
        data_path: str | None = None,
    ) -> dict:
        nexus_paths = get_nexus_path(nexus_path_version)
        nexus_detector_paths = nexus_paths.nx_detector_paths

        nx_dict = {}
        if self.data is not None:
            # add data
            path_data = f"{self.path}/{nexus_detector_paths.DATA}"
            nx_dict[path_data] = self.data
            nx_dict["@".join([path_data, "interpretation"])] = "image"
            # add attributes to data
            nx_dict[f"{self.path}@NX_class"] = "NXdetector"
            nx_dict[f"{self.path}@signal"] = nexus_detector_paths.DATA
            nx_dict[f"{self.path}@SILX_style/axis_scale_types"] = [
                "linear",
                "linear",
            ]
        return nx_dict

    @staticmethod
    @docstring(NXobject)
    def concatenate(
        nx_objects: tuple, default_unit, expected_dim, node_name="detector"
    ):
        # Filter out None objects
        nx_objects = tuple(filter(partial(is_not, None), nx_objects))
        if len(nx_objects) == 0:
            return None

        # Ensure all objects are NXdetector instances
        for nx_obj in nx_objects:
            if not isinstance(nx_obj, NXdetector):
                raise TypeError("Cannot concatenate non-NXdetector object")

        # Create new detector instance
        nx_detector = NXdetectorWithUnit(
            node_name=node_name, default_unit=default_unit, expected_dim=expected_dim
        )
        NXdetector._concatenate_except_data(
            nx_objects=nx_objects, nx_detector=nx_detector
        )

        # Handle data concatenation
        detector_data = [
            nx_obj.data for nx_obj in nx_objects if nx_obj.data is not None
        ]

        # Ensure unit consistency
        detector_units = set(
            nx_obj.data.units
            for nx_obj in nx_objects
            if nx_obj.data is not None and isinstance(nx_obj.data, pint.Quantity)
        )

        if len(detector_units) > 1:
            raise ValueError("More than one unit found. Unable to build the detector.")

        # If no data is present, return early
        if not detector_data or len(detector_data) == 0:
            return nx_detector

        expected_unit = list(detector_units)[0] if detector_units else default_unit

        # Check data type and expected structure
        first_data = detector_data[0]

        if isinstance(first_data, pint.Quantity):
            expected = pint.Quantity
        elif isinstance(first_data, numpy.ndarray):
            expected = numpy.ndarray
        elif isinstance(first_data, Iterable):
            if isinstance(first_data[0], h5py.VirtualSource):
                expected = h5py.VirtualSource
            elif isinstance(first_data[0], DataUrl):
                expected = DataUrl
            else:
                raise TypeError(
                    f"Detector data must be a numpy array, h5py.VirtualSource, or DataUrl. "
                    f"Found {type(first_data[0])}."
                )
        else:
            raise TypeError(
                f"Detector data must be a numpy array, h5py.VirtualSource, or DataUrl. "
                f"Found {type(first_data)}."
            )

        # Validate all data entries
        for data in detector_data:
            if expected in (DataUrl, h5py.VirtualSource):
                cond = isinstance(data[0], expected)
            else:
                cond = isinstance(data, expected) or isinstance(data, pint.Quantity)

            if not cond:
                raise TypeError(
                    f"Incoherent data type across detector data: {type(data)} when {expected} expected."
                )

        # Perform concatenation with proper unit handling
        if expected in (DataUrl, h5py.VirtualSource):
            new_data = []
            for data in detector_data:
                new_data.extend(data)
        else:
            # If the data is pint.Quantity, concatenate magnitudes and reapply the unit
            if isinstance(first_data, pint.Quantity):
                new_data = (
                    numpy.concatenate([data.magnitude for data in detector_data])
                    * expected_unit
                )
            else:
                new_data = numpy.concatenate(detector_data)

        # Assign data correctly
        nx_detector.data = new_data

        return nx_detector
