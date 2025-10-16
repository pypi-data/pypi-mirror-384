"""Define NXtomo application and related functions and classes"""

from __future__ import annotations

import logging
import os
from copy import deepcopy
from datetime import datetime
from functools import partial
from operator import is_not

import h5py
import numpy
import pint
from silx.io.url import DataUrl
from silx.io.utils import open as hdf5_open
from silx.utils.proxy import docstring

from nxtomo.geometry._CoordinateSystem import CoordinateSystem
from nxtomo.nxobject.nxdetector import ImageKey
from nxtomo.nxobject.nxinstrument import NXinstrument
from nxtomo.nxobject.nxmonitor import NXmonitor
from nxtomo.nxobject.nxobject import NXobject
from nxtomo.nxobject.nxsample import NXsample
from nxtomo.nxobject.utils.decorator import check_dimensionality
from nxtomo.paths.nxtomo import LATEST_VERSION as LATEST_NXTOMO_VERSION
from nxtomo.paths.nxtomo import get_paths as get_nexus_paths
from nxtomo.utils import get_data, get_quantity

_logger = logging.getLogger(__name__)


__all__ = ["NXtomo", "copy_nxtomo_file"]

_ureg = pint.UnitRegistry()


class NXtomo(NXobject):
    """
    Class defining an NXtomo.
    Its primary goal is to save data to disk.

    :param node_name: node_name is used by the NXobject parent to order children when dumping it to file.
        As NXtomo is expected to be the highest object in the hierarchy, node_name will only be used for saving if no `data_path` is provided when calling the `save` function.
    :param parent: parent of this NXobject. Most likely None for NXtomo.
    """

    def __init__(self, parent: NXobject | None = None) -> None:
        super().__init__(node_name="", parent=parent)
        self._set_freeze(False)
        self._coordinate_system: CoordinateSystem | None = CoordinateSystem.McStas
        self._start_time = None
        self._end_time = None
        self._instrument = NXinstrument(node_name="instrument", parent=self)
        self._sample = NXsample(node_name="sample", parent=self)
        self._control = NXmonitor(node_name="control", parent=self)
        self._group_size = None
        self._bliss_original_files = None  # warning: output will be different if set to None (dataset not exported) or an empty tuple (exported but empty)
        self._energy: pint.Quantity | None = None
        self._title = None
        self._set_freeze(True)

    @property
    def start_time(self) -> datetime | str | None:
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: datetime | str | None):
        if not isinstance(start_time, (type(None), datetime, str)):
            raise TypeError(
                f"start_time is expected ot be an instance of datetime or None. Not {type(start_time)}"
            )
        self._start_time = start_time

    @property
    def end_time(self) -> datetime | str | None:
        return self._end_time

    @end_time.setter
    def end_time(self, end_time: datetime | str | None):
        if not isinstance(end_time, (type(None), datetime, str)):
            raise TypeError(
                f"end_time is expected ot be an instance of datetime or None. Not {type(end_time)}"
            )
        self._end_time = end_time

    @property
    def title(self) -> str | None:
        return self._title

    @title.setter
    def title(self, title: str | None):
        if isinstance(title, numpy.ndarray):
            # handle diamond use case
            title = str(title)
        elif not isinstance(title, (type(None), str)):
            raise TypeError(
                f"title is expected ot be an instance of str or None. Not {type(title)}"
            )
        self._title = title

    @property
    def instrument(self) -> NXinstrument | None:
        return self._instrument

    @instrument.setter
    def instrument(self, instrument: NXinstrument | None) -> None:
        if not isinstance(instrument, (type(None), NXinstrument)):
            raise TypeError(
                f"instrument is expected ot be an instance of {NXinstrument} or None. Not {type(instrument)}"
            )
        self._instrument = instrument

    @property
    def sample(self) -> NXsample | None:
        return self._sample

    @sample.setter
    def sample(self, sample: NXsample | None):
        if not isinstance(sample, (type(None), NXsample)):
            raise TypeError(
                f"sample is expected ot be an instance of {NXsample} or None. Not {type(sample)}"
            )
        self._sample = sample

    @property
    def control(self) -> NXmonitor | None:
        return self._control

    @control.setter
    def control(self, control: NXmonitor | None) -> None:
        if not isinstance(control, (type(None), NXmonitor)):
            raise TypeError(
                f"control is expected ot be an instance of {NXmonitor} or None. Not {type(control)}"
            )
        self._control = control

    @property
    def energy(self) -> pint.Quantity | None:
        return self._energy

    @energy.setter
    @check_dimensionality(expected_dimension="[energy]")
    def energy(self, energy: pint.Quantity | None) -> None:
        if energy is None:
            self._energy = None
        elif isinstance(energy, pint.Quantity):
            self._energy = energy.to(_ureg.keV)
        else:
            raise TypeError(
                f"energy is expected to be a pint.Quantity or None. Not {type(energy)}"
            )

    @property
    def group_size(self) -> int | None:
        return self._group_size

    @group_size.setter
    def group_size(self, group_size: int | None):
        if not (
            isinstance(group_size, (type(None), int))
            or (numpy.isscalar(group_size) and not isinstance(group_size, (str, bytes)))
        ):
            raise TypeError(
                f"group_size is expected ot be None or a scalar. Not {type(group_size)}"
            )
        self._group_size = group_size

    @property
    def bliss_original_files(self) -> tuple | None:
        return self._bliss_original_files

    @bliss_original_files.setter
    def bliss_original_files(self, files: tuple | numpy.ndarray | None):
        if isinstance(files, numpy.ndarray):
            files = tuple(files)
        if not isinstance(files, (type(None), tuple)):
            raise TypeError(
                f"files is expected to be None or a tuple. {type(files)} provided instead"
            )
        self._bliss_original_files = files

    @docstring(NXobject)
    def to_nx_dict(
        self,
        nexus_path_version: float | None = None,
        data_path: str | None = None,
    ) -> dict:
        if data_path is None:
            data_path = ""

        nexus_paths = get_nexus_paths(nexus_path_version)
        nx_dict = {}

        if self.sample is not None:
            nx_dict.update(
                self.sample.to_nx_dict(nexus_path_version=nexus_path_version)
            )
        else:
            _logger.info("no sample found. Won't be saved")

        if self.instrument is not None:
            nx_dict.update(
                self.instrument.to_nx_dict(nexus_path_version=nexus_path_version)
            )
        else:
            _logger.info("no instrument found. Won't be saved")

        if self.control is not None:
            nx_dict.update(
                self.control.to_nx_dict(nexus_path_version=nexus_path_version)
            )
        else:
            _logger.info("no control found. Won't be saved")

        if self.start_time is not None:
            path_start_time = f"{self.path}/{nexus_paths.START_TIME_PATH}"
            if isinstance(self.start_time, datetime):
                start_time = self.start_time.isoformat()
            else:
                start_time = self.start_time
            nx_dict[path_start_time] = start_time
        if self.end_time is not None:
            path_end_time = f"{self.path}/{nexus_paths.END_TIME_PATH}"
            if isinstance(self.end_time, datetime):
                end_time = self.end_time.isoformat()
            else:
                end_time = self.end_time
            nx_dict[path_end_time] = end_time
        if self.group_size is not None:
            path_grp_size = f"{self.path}/{nexus_paths.GRP_SIZE_ATTR}"
            nx_dict[path_grp_size] = self.group_size
        if self.energy is not None:
            path_energy = f"{self.path}/{nexus_paths.ENERGY_PATH}"

            nx_dict[path_energy] = self.energy.magnitude
            nx_dict["@".join([path_energy, "units"])] = f"{self.energy.units:~}"
            path_beam = f"{self.path}/{nexus_paths.BEAM_PATH}"
            nx_dict["@".join([path_beam, "NX_class"])] = "NXbeam"

            if nexus_paths.VERSION > 1.0:
                nx_dict[f">/{self.path}/beam/incident_energy"] = (
                    f"/{data_path}/{self.path}/{nexus_paths.ENERGY_PATH}"
                )
        if self.title is not None:
            path_title = f"{self.path}/{nexus_paths.NAME_PATH}"
            nx_dict[path_title] = self.title

        if self.bliss_original_files is not None:
            nx_dict[f"/{self.path}/bliss_original_files"] = self.bliss_original_files

        # create data group from symbolic links

        if self.instrument.detector.image_key is not None:
            nx_dict[f">/{self.path}/data/image_key"] = (
                f"/{data_path}/{self.instrument.detector.path}/{nexus_paths.nx_detector_paths.IMAGE_KEY}"
            )
            nx_dict[f">/{self.path}/data/image_key_control"] = (
                f"/{data_path}/{self.instrument.detector.path}/{nexus_paths.nx_detector_paths.IMAGE_KEY_CONTROL}"
            )
        if self.instrument.detector.data is not None:
            nx_dict[f">/{self.path}/data/data"] = (
                f"/{data_path}/{self.instrument.detector.path}/{nexus_paths.nx_detector_paths.DATA}"
            )
            nx_dict[f"/{self.path}/data@NX_class"] = "NXdata"
            nx_dict[f"/{self.path}/data@signal"] = "data"
            nx_dict[f"/{self.path}@default"] = "data"
            nx_dict[f"{self.path}/data@SILX_style/axis_scale_types"] = [
                "linear",
                "linear",
            ]
        if self.sample.rotation_angle is not None:
            nx_dict[f">/{self.path}/data/rotation_angle"] = (
                f"/{data_path}/{self.sample.path}/{nexus_paths.nx_sample_paths.ROTATION_ANGLE}"
            )

        if nx_dict != {}:
            nx_dict[f"{self.path}@NX_class"] = "NXentry"
            nx_dict[f"{self.path}@definition"] = "NXtomo"
            nx_dict[f"{self.path}/definition"] = "NXtomo"
            nx_dict[f"{self.path}@version"] = nexus_paths.VERSION

            if self._coordinate_system is not None:
                nx_dict[f"{self.path}@NeXus_Coordinate_System"] = (
                    self._coordinate_system.value
                )

        return nx_dict

    def detector_data_is_defined_by_url(self) -> bool:
        return self._detector_data_is_defined_by_type(DataUrl)

    def detector_data_is_defined_by_virtual_source(self) -> bool:
        return self._detector_data_is_defined_by_type(h5py.VirtualSource)

    def _detector_data_is_defined_by_type(self, type_):
        return (
            self.instrument is not None
            and self.instrument.detector is not None
            and self.instrument.detector.data is not None
            and isinstance(self.instrument.detector.data, (str, tuple))
            and isinstance(self.instrument.detector.data[0], type_)
        )

    def load(
        self, file_path: str, data_path: str, detector_data_as="as_data_url"
    ) -> NXobject:
        """
        Load NXtomo instance from file_path and data_path

        :param file_path: hdf5 file path containing the NXtomo
        :param data_path: location of the NXtomo
        :param detector_data_as: how to load detector data. Can be:
                                     * "as_virtual_source": load it as h5py's VirtualGroup
                                     * "as_data_url": load it as silx's DataUrl
                                     * "as_numpy_array": load them as a numpy array (warning: can be memory consuming since all the data will be loaded)
        """
        possible_as_values = ("as_virtual_source", "as_data_url", "as_numpy_array")
        if detector_data_as not in possible_as_values:
            raise ValueError(
                f"detector_data_as is expected to be in {possible_as_values} and not {detector_data_as}"
            )

        if not os.path.exists(file_path):
            raise IOError(f"{file_path} does not exists")
        with hdf5_open(file_path) as h5f:
            if data_path not in h5f:
                raise ValueError(f"{data_path} cannot be find in {file_path}")
            root_node = h5f[data_path]

            if "version" in root_node.attrs:
                nexus_version = root_node.attrs["version"]
            else:
                _logger.warning(
                    f"Unable to find nexus version associated with {data_path}@{file_path}"
                )
                nexus_version = LATEST_NXTOMO_VERSION

            coordinate_system = root_node.attrs.get("NeXus_Coordinate_System", None)
            if coordinate_system is not None:
                coordinate_system = CoordinateSystem(coordinate_system)
            self._coordinate_system = coordinate_system

        nexus_paths = get_nexus_paths(nexus_version)
        self.energy = get_quantity(
            file_path=file_path,
            data_path="/".join([data_path, nexus_paths.ENERGY_PATH]),
            default_unit=_ureg.keV,
        )
        start_time = get_data(
            file_path=file_path,
            data_path="/".join([data_path, nexus_paths.START_TIME_PATH]),
        )
        try:
            start_time = datetime.fromisoformat(start_time)
        except Exception:
            start_time = str(start_time) if start_time is not None else None
        self.start_time = start_time

        end_time = get_data(
            file_path=file_path,
            data_path="/".join([data_path, nexus_paths.END_TIME_PATH]),
        )
        try:
            end_time = datetime.fromisoformat(end_time)
        except Exception:
            end_time = str(end_time) if end_time is not None else None
        self.end_time = end_time

        self.bliss_original_files = get_data(
            file_path=file_path,
            data_path="/".join([data_path, "bliss_original_files"]),
        )

        self.title = get_data(
            file_path=file_path, data_path="/".join([data_path, nexus_paths.NAME_PATH])
        )

        self.sample._load(
            file_path, "/".join([data_path, "sample"]), nexus_version=nexus_version
        )
        self.instrument._load(
            file_path,
            "/".join([data_path, "instrument"]),
            nexus_version=nexus_version,
            detector_data_as=detector_data_as,
        )
        self.control._load(
            file_path, "/".join([data_path, "control"]), nexus_version=nexus_version
        )
        return self

    @staticmethod
    def check_consistency(nx_tomo, raises_error: bool = False):
        """
        Ensure some key datasets have the expected number of values.

        :param NXtomo nx_tomo: NXtomo to check
        :param raises_error: if True, raise ValueError when some incoherent number of values is encountered (if missing will drop a warning only).
            if False, only warnings will be issued.
        """
        if not isinstance(nx_tomo, NXtomo):
            raise TypeError(
                f"nx_tomo is expected to be an instance of {NXtomo}. {type(nx_tomo)} provided"
            )
        if nx_tomo.sample is not None:
            n_rotation_angle = (
                len(nx_tomo.sample.rotation_angle)
                if nx_tomo.sample.rotation_angle is not None
                else None
            )
            n_x_trans = (
                len(nx_tomo.sample.x_translation)
                if nx_tomo.sample.x_translation is not None
                else None
            )
            n_y_trans = (
                len(nx_tomo.sample.y_translation)
                if nx_tomo.sample.y_translation is not None
                else None
            )
            n_z_trans = (
                len(nx_tomo.sample.z_translation)
                if nx_tomo.sample.z_translation is not None
                else None
            )
        else:
            n_rotation_angle = None
            n_x_trans = None
            n_y_trans = None
            n_z_trans = None

        if nx_tomo.instrument is not None and nx_tomo.instrument.detector is not None:
            frames = (
                nx_tomo.instrument.detector.data
                if nx_tomo.instrument.detector.data is not None
                else None
            )
            n_frames = len(frames) if frames is not None else None
            image_keys = (
                nx_tomo.instrument.detector.image_key_control
                if nx_tomo.instrument.detector.image_key_control is not None
                else None
            )
            n_image_key = len(image_keys) if image_keys is not None else None
            n_count_time = (
                len(nx_tomo.instrument.detector.count_time)
                if nx_tomo.instrument.detector.count_time is not None
                else None
            )
        else:
            frames = None
            n_frames = None
            n_image_key = None
            image_keys = None
            n_count_time = None

        n_expected_frames = max(
            (n_rotation_angle or 0),
            (n_frames or 0),
            (n_image_key or 0),
            (n_x_trans or 0),
            (n_y_trans or 0),
            (n_z_trans or 0),
        )

        def check(nb_values, info):
            if nb_values is None:
                _logger.warning(f"{info} not defined")
            elif nb_values != n_expected_frames:
                mess = (
                    f"{info} has {nb_values} values when {n_expected_frames} expected"
                )
                if raises_error:
                    raise ValueError(mess)
                else:
                    _logger.warning(mess)

        check(n_rotation_angle, f"{nx_tomo.node_name}.sample.rotation_angle")
        check(n_x_trans, f"{nx_tomo.node_name}.sample.x_translation")
        check(n_y_trans, f"{nx_tomo.node_name}.sample.y_translation")
        check(n_z_trans, f"{nx_tomo.node_name}.sample.z_translation")
        check(n_frames, f"{nx_tomo.node_name}.instrument.detector.data")
        check(n_image_key, f"{nx_tomo.node_name}.instrument.detector.image_key_control")
        check(n_count_time, f"{nx_tomo.node_name}.instrument.detector.count_time")

        tomo_n = (
            nx_tomo.instrument.detector.tomo_n
            if (
                nx_tomo.instrument is not None
                and nx_tomo.instrument.detector is not None
            )
            else None
        )
        if tomo_n is not None and frames is not None:
            n_projection = len(frames[image_keys == ImageKey.PROJECTION.value])
            if n_projection != tomo_n:
                mess = f"incoherent number of projections found ({n_projection}) compared to tomo_n ({tomo_n})"
                if raises_error:
                    raise ValueError(mess)
                else:
                    _logger.warning(mess)

    @staticmethod
    @docstring(NXobject)
    def concatenate(nx_objects: tuple):
        """
        Concatenate a tuple of NXobject instances into a single NXobject.

        :param nx_objects:
        :return: NXtomo instance which is the concatenation of the nx_objects
        """
        nx_objects = tuple(filter(partial(is_not, None), nx_objects))
        # filter None obj
        if len(nx_objects) == 0:
            return None
        # warning: later we make the assumption that nx_objects contains at least one element
        for nx_obj in nx_objects:
            if not isinstance(nx_obj, NXtomo):
                raise TypeError("Cannot concatenate non NXtomo object")

        nx_tomo = NXtomo()

        # check object concatenation can be handled
        def get_energy() -> pint.Quantity | None:
            """
            Determines the expected energy value from a list of NXobjects.
            Ensures energy values are consistent across NXobjects.
            """
            nxtomos_with_energy = filter(
                lambda energy: energy is not None,
                nx_objects,
            )
            try:
                first_nx_tomo_with_energy = next(nxtomos_with_energy)
            except StopIteration:
                return None
            else:
                return first_nx_tomo_with_energy.energy

        nx_tomo.energy = get_energy()

        _logger.info(f"title {nx_objects[0].title} will be picked")
        nx_tomo.title = nx_objects[0].title
        start_times = tuple(
            filter(
                lambda x: x is not None, [nx_obj.start_time for nx_obj in nx_objects]
            )
        )
        end_times = tuple(
            filter(lambda x: x is not None, [nx_obj.end_time for nx_obj in nx_objects])
        )

        nx_tomo.start_time = min(start_times) if len(start_times) > 0 else None
        nx_tomo.end_time = max(end_times) if len(end_times) > 0 else None

        nx_tomo.sample = NXsample.concatenate(
            tuple([nx_obj.sample for nx_obj in nx_objects])
        )
        nx_tomo.sample.parent = nx_tomo

        nx_tomo.instrument = NXinstrument.concatenate(
            tuple([nx_obj.instrument for nx_obj in nx_objects]),
        )
        nx_tomo.instrument.parent = nx_tomo

        nx_tomo.control = NXmonitor.concatenate(
            tuple([nx_obj.control for nx_obj in nx_objects]),
        )
        nx_tomo.control.parent = nx_tomo

        bliss_original_files = set()
        bof_only_none = True
        for nx_obj in nx_objects:
            if nx_obj.bliss_original_files is not None:
                # current behavior of 'bliss_original_files' is that if there is no information (None) then we won't
                # save it to the file as this is a pure 'esrf' information. Else if it is there (even if empty) we save it
                bof_only_none = False
                bliss_original_files.update(nx_obj.bliss_original_files)

        bliss_original_files = tuple(
            sorted(bliss_original_files)
        )  # it is more convenient ot have it sorted - else sorted along obj id
        nx_tomo.bliss_original_files = None if bof_only_none else bliss_original_files

        return nx_tomo

    def check_can_select_from_rotation_angle(self):
        if (
            self.sample is None
            or self.sample.rotation_angle is None
            or len(self.sample.rotation_angle) == 0
        ):
            raise ValueError(
                "No information on rotation angle found. Unable to do a selection based on angles"
            )
        if self.instrument is None or self.instrument.detector is None:
            raise ValueError(
                "No detector found. Unable to do a selection based on angles"
            )

    @docstring(NXobject)
    def save(
        self,
        file_path: str,
        data_path: str,
        nexus_path_version: float | None = None,
        overwrite: bool = False,
    ) -> None:
        # Note: we overwrite save function for NXtomo in order to force 'data_path' to be provided.
        # Else we get both name and data_path and increase complexity to determine
        # the fiinal location
        super().save(
            file_path=file_path,
            data_path=data_path,
            nexus_path_version=nexus_path_version,
            overwrite=overwrite,
        )

    def sub_select_selection_from_angle_range(
        nx_tomo, start_angle: float, stop_angle: float, copy=True
    ):
        """
        Create an NXtomo like `nx_tomo` but update `image_key_control` to INVALID for
        all projections that do not fulfill the condition: start_angle < rotation_angle < stop_angle.

        Note: Darks and flat fields will not be affected by this sub-selection.

        :param start_angle: Left bound for selection (float, in degrees).
        :param stop_angle: Right bound for selection (float, in degrees).
        :param copy: If True, return a copy of nx_tomo; otherwise, modify nx_tomo in place.
        """
        nx_tomo.check_can_select_from_rotation_angle()
        if copy:
            res = deepcopy(nx_tomo)
        else:
            res = nx_tomo

        angles = res.sample.rotation_angle.magnitude

        mask = numpy.logical_and(
            res.instrument.detector.image_key_control == ImageKey.PROJECTION,
            numpy.logical_or(angles < start_angle, angles > stop_angle),
        )
        res.instrument.detector.image_key_control[mask] = ImageKey.INVALID
        return res

    @staticmethod
    def sub_select_from_angle_offset(
        nx_tomo,
        start_angle_offset: float,
        angle_interval: float | None,
        shift_angles: bool,
        copy=True,
    ):
        """
        Get a sub-selection of NXtomo projections that start with a `start_angle_offset` and
        cover `angle_interval`.

        Note: Darks and flat fields will not be affected by this sub-selection.

        :param start_angle_offset: Offset for selection (float, in degrees).
                                The offset is always relative to the first projection angle.
        :param angle_interval: Interval covered by the selection (float, in degrees).
                            If None, selects until the end.
        :param shift_angles: If True, shift angles by `-start_angle_offset` after selection.
        :param copy: If True, return a copy of nx_tomo; otherwise, modify nx_tomo in place.
        """
        nx_tomo.check_can_select_from_rotation_angle()

        if copy:
            res = deepcopy(nx_tomo)
        else:
            res = nx_tomo

        if shift_angles:
            # for the shift we shift all the projection angle. Simpler
            mask_shift = (
                res.instrument.detector.image_key_control == ImageKey.PROJECTION
            )

        # Extract angles as float values
        projection_angles = res.sample.rotation_angle.magnitude[
            res.instrument.detector.image_key_control == ImageKey.PROJECTION
        ]

        if angle_interval is None:
            # Compute full available interval
            angle_interval = abs(
                projection_angles.max() - projection_angles.min()
            ) + abs(start_angle_offset)

        # Determine start and stop angles as floats
        if len(projection_angles) < 2 or projection_angles[1] > projection_angles[0]:
            # rotate with positive angles
            start_angle = projection_angles[0] + start_angle_offset
            stop_angle = start_angle + angle_interval
        else:
            # rotate with negative angles
            start_angle = projection_angles[0] + start_angle_offset
            stop_angle = start_angle - angle_interval

        NXtomo.sub_select_selection_from_angle_range(
            res,
            start_angle=float(start_angle),
            stop_angle=float(stop_angle),
            copy=False,
        )

        if shift_angles:
            angles = res.sample.rotation_angle.magnitude
            angles[mask_shift] -= start_angle_offset
            res.sample.rotation_angle = angles * _ureg.degree

        return res

    @staticmethod
    def clamp_angles(nx_tomo, angle_range, offset=0, copy=True, image_keys=None):
        if copy:
            res = deepcopy(nx_tomo)
        else:
            res = nx_tomo

        if image_keys is None:
            image_keys = ImageKey.values()

        mask_shift = numpy.logical_or(
            *(
                [
                    res.instrument.detector.image_key_control == ImageKey(image_key)
                    for image_key in image_keys
                ]
            )
        )

        angles = res.sample.rotation_angle.magnitude
        angles[mask_shift] -= offset
        angles[mask_shift] = angles[mask_shift] % angle_range
        res.sample.rotation_angle = angles * _ureg.degree
        return res

    @staticmethod
    def get_valid_entries(file_path: str) -> tuple:
        """
        Return the list of 'NXtomo' entries at the root level.

        :param file_path:
        :return: list of valid NXtomo nodes (ordered alphabetically)

        .. note: entries are sorted to ensure consistency
        """
        if not os.path.isfile(file_path):
            raise ValueError("given file path should be a file")

        def browse_group(group):
            res_buf = []
            for entry_alias in group.keys():
                entry = group.get(entry_alias)
                if isinstance(entry, h5py.Group):
                    if NXtomo.node_is_nxtomo(entry):
                        res_buf.append(entry.name)
                    else:
                        res_buf.extend(browse_group(entry))
            return res_buf

        with hdf5_open(file_path) as h5f:
            res = browse_group(h5f)
        res.sort()
        return tuple(res)

    @staticmethod
    def node_is_nxtomo(node: h5py.Group) -> bool:
        """Check whether the given h5py node is an NXtomo node."""
        if "NX_class" in node.attrs or "NXclass" in node.attrs:
            _logger.debug(f"{node.name} is recognized as a nx class.")
        else:
            _logger.debug(f"{node.name} isn't recognized as a nx class.")
            return False
        if "definition" in node.attrs and node.attrs["definition"].lower() == "nxtomo":
            _logger.debug(f"{node.name} is recognized as an NXtomo class.")
            return True
        elif (
            "instrument" in node
            and "NX_class" in node["instrument"].attrs
            and node["instrument"].attrs["NX_class"]
            in (
                "NXinstrument",
                b"NXinstrument",
            )  # b"NXinstrument" is needed for Diamond compatibility
        ):
            return "detector" in node["instrument"]
        return False


def copy_nxtomo_file(
    input_file: str,
    output_file: str,
    entries: tuple | None,
    overwrite: bool = False,
    vds_resolution="update",
):
    """
    Copy one or several NXtomo entries from one file to another (solving relative links).

    :param input_file: NeXus file from which NXtomo entries have to be copied.
    :param output_file: output file.
    :param entries: entries to be copied. If set to None then all entries will be copied.
    :param overwrite: overwrite data path if already exists.
    :param vds_resolution: How to solve virtual datasets. Options are:
        * update: update Virtual source (relative) paths according to the new location of the file.
        * remove: replace the virtual data source by copying directly the resulting dataset. Warning: in this case all the dataset will be loaded in memory.

        In the future another option could be:
        * embed: copy all VDS to new datasets in the output file 'as they are' (avoid to load all the data in memory).

    """
    input_file = os.path.abspath(input_file)
    output_file = os.path.abspath(output_file)
    if input_file == output_file:
        raise ValueError("input file and output file are the same")

    if entries is None:
        entries = NXtomo.get_valid_entries(file_path=input_file)
        if len(entries) == 0:
            _logger.warning(f"no valid entries for {input_file}")

    for entry in entries:
        if vds_resolution == "remove":
            detector_data_as = "as_numpy_array"
        elif vds_resolution == "update":
            detector_data_as = "as_data_url"
        else:
            raise ValueError(
                f"Unexpected value for 'vds_resolution': {vds_resolution}. Valid values are 'remove' and 'update'"
            )

        nx_tomo = NXtomo().load(input_file, entry, detector_data_as=detector_data_as)
        nx_tomo.save(output_file, entry, overwrite=overwrite)
