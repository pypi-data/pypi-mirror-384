"""NeXus paths used to define an `NXtomo <https://manual.nexusformat.org/classes/base_classes/NXtomo.html>`_."""

from __future__ import annotations

import logging

import nxtomo
from nxtomo.paths import (
    nxdetector,
    nxinstrument,
    nxmonitor,
    nxsample,
    nxsource,
    nxtransformations,
)
from nxtomo.utils.io import deprecated

_logger = logging.getLogger(__name__)


LATEST_VERSION = 2.0


class NXtomo_PATH:
    # list all path that can be used by an nxtomo entry and read by nxtomo.
    # this is also used by nxtomomill to know were to save data

    _NX_DETECTOR_PATHS = None
    _NX_INSTRUMENT_PATHS = None
    _NX_SAMPLE_PATHS = None
    _NX_SOURCE_PATHS = None
    _NX_CONTROL_PATHS = None

    _NX_TRANSFORMATIONS_PATHS = None
    # paths used per each transformation contained in NX_TRANSFORMATIONS

    VERSION = None

    @property
    def nx_detector_paths(self):
        return self._NX_DETECTOR_PATHS

    @property
    def nx_instrument_paths(self):
        return self._NX_INSTRUMENT_PATHS

    @property
    def nx_sample_paths(self):
        return self._NX_SAMPLE_PATHS

    @property
    def nx_source_paths(self):
        return self._NX_SOURCE_PATHS

    @property
    def nx_monitor_paths(self):
        return self._NX_CONTROL_PATHS

    @property
    def nx_transformations_paths(self):
        return self._NX_TRANSFORMATIONS_PATHS

    @property
    def PROJ_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.DATA,
            ]
        )

    @property
    def SCAN_META_PATH(self) -> str:
        # for now scan_meta and technique are not link to any nxtomo...
        return "scan_meta/technique/scan"

    @property
    def INSTRUMENT_PATH(self) -> str:
        return "instrument"

    @property
    def CONTROL_PATH(self) -> str:
        return "control"

    @property
    def DET_META_PATH(self) -> str:
        return "scan_meta/technique/detector"

    @property
    def ROTATION_ANGLE_PATH(self):
        return "/".join(["sample", self.nx_sample_paths.ROTATION_ANGLE])

    @property
    def SAMPLE_PATH(self) -> str:
        return "sample"

    @property
    def NAME_PATH(self) -> str:
        return "sample/name"

    @property
    def GRP_SIZE_ATTR(self) -> str:
        return "group_size"

    @property
    def SAMPLE_NAME_PATH(self) -> str:
        return "/".join([self.SAMPLE_PATH, self.nx_sample_paths.NAME])

    @property
    def X_TRANS_PATH(self) -> str:
        return "/".join([self.SAMPLE_PATH, self.nx_sample_paths.X_TRANSLATION])

    @property
    def Y_TRANS_PATH(self) -> str:
        return "/".join([self.SAMPLE_PATH, self.nx_sample_paths.Y_TRANSLATION])

    @property
    def Z_TRANS_PATH(self) -> str:
        return "/".join([self.SAMPLE_PATH, self.nx_sample_paths.Z_TRANSLATION])

    @property
    def IMG_KEY_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.IMAGE_KEY,
            ]
        )

    @property
    def IMG_KEY_CONTROL_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.IMAGE_KEY_CONTROL,
            ]
        )

    @property
    def X_PIXEL_SIZE_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.X_PIXEL_SIZE,
            ]
        )

    @property
    def Y_PIXEL_SIZE_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.Y_PIXEL_SIZE,
            ]
        )

    @property
    def X_REAL_PIXEL_SIZE_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.X_REAL_PIXEL_SIZE,
            ]
        )

    @property
    def Y_REAL_PIXEL_SIZE_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.Y_REAL_PIXEL_SIZE,
            ]
        )

    @property
    @deprecated(replacement="SAMPLE_DETECTOR_DISTANCE_PATH", since_version="2.0")
    def DISTANCE_PATH(self) -> str:
        return self.SAMPLE_DETECTOR_DISTANCE_PATH

    @property
    def SAMPLE_DETECTOR_DISTANCE_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.DISTANCE,
            ]
        )

    @property
    def FOV_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.FOV,
            ]
        )

    @property
    def EXPOSURE_TIME_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.EXPOSURE_TIME,
            ]
        )

    @property
    def ELECTRIC_CURRENT_PATH(self) -> str:
        return "/".join(
            [
                self.CONTROL_PATH,
                self.nx_monitor_paths.DATA_PATH,
            ]
        )

    @property
    def TOMO_N_SCAN(self) -> str:
        return "/".join(
            [self.INSTRUMENT_PATH, self.nx_instrument_paths.DETECTOR_PATH, "tomo_n"]
        )

    @property
    def BEAM_PATH(self) -> str:
        return "beam"

    @property
    def ENERGY_PATH(self) -> str:
        return f"{self.BEAM_PATH}/incident_energy"

    @property
    def START_TIME_PATH(self) -> str:
        return "start_time"

    @property
    def END_TIME_PATH(self) -> str:
        return "end_time"

    @property
    def INTENSITY_MONITOR_PATH(self) -> str:
        return "diode/data"

    @property
    def SOURCE_NAME(self) -> str | None:
        return None

    @property
    def SOURCE_TYPE(self) -> str | None:
        return None

    @property
    def SOURCE_PROBE(self) -> str | None:
        return None

    @property
    def INSTRUMENT_NAME(self) -> str | None:
        return None


# V 1.0


class NXtomo_PATH_v_1_0(NXtomo_PATH):
    VERSION = 1.0

    _NX_DETECTOR_PATHS = nxdetector.NEXUS_DETECTOR_PATH_V_1_0
    _NX_INSTRUMENT_PATHS = nxinstrument.NEXUS_INSTRUMENT_PATH_V_1_0
    _NX_SAMPLE_PATHS = nxsample.NEXUS_SAMPLE_PATH_V_1_0
    _NX_SOURCE_PATHS = nxsource.NEXUS_SOURCE_PATH_V_1_0
    _NX_CONTROL_PATHS = nxmonitor.NEXUS_MONITOR_PATH_V_1_1


nx_tomo_path_v_1_0 = NXtomo_PATH_v_1_0()

# V 1.1


class NXtomo_PATH_v_1_1(NXtomo_PATH_v_1_0):
    VERSION = 1.1

    _NX_DETECTOR_PATHS = nxdetector.NEXUS_DETECTOR_PATH_V_1_1
    _NX_INSTRUMENT_PATHS = nxinstrument.NEXUS_INSTRUMENT_PATH_V_1_1
    _NX_SAMPLE_PATHS = nxsample.NEXUS_SAMPLE_PATH_V_1_1
    _NX_SOURCE_PATHS = nxsource.NEXUS_SOURCE_PATH_V_1_1

    @property
    def NAME_PATH(self) -> str:
        return "title"

    @property
    def BEAM_PATH(self) -> str:
        return "/".join([self.INSTRUMENT_PATH, self.nx_instrument_paths.BEAM])

    @property
    def SOURCE_NAME(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.SOURCE,
                self.nx_source_paths.NAME,
            ]
        )

    @property
    def SOURCE_TYPE(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.SOURCE,
                self.nx_source_paths.TYPE,
            ]
        )

    @property
    def SOURCE_PROBE(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.SOURCE,
                self.nx_source_paths.PROBE,
            ]
        )

    @property
    def INSTRUMENT_NAME(self) -> str:
        return "/".join([self.INSTRUMENT_PATH, self.nx_instrument_paths.NAME])


nx_tomo_path_v_1_1 = NXtomo_PATH_v_1_1()

# V 1.2


class NXtomo_PATH_v_1_2(NXtomo_PATH_v_1_1):
    VERSION = 1.2

    _NX_DETECTOR_PATHS = nxdetector.NEXUS_DETECTOR_PATH_V_1_2
    _NX_INSTRUMENT_PATHS = nxinstrument.NEXUS_INSTRUMENT_PATH_V_1_2
    _NX_SAMPLE_PATHS = nxsample.NEXUS_SAMPLE_PATH_V_1_2
    _NX_SOURCE_PATHS = nxsource.NEXUS_SOURCE_PATH_V_1_2

    @property
    def INTENSITY_MONITOR_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DIODE,
                self.nx_detector_paths.DATA,
            ]
        )


nx_tomo_path_v_1_2 = NXtomo_PATH_v_1_2()

# V 1.3


class NXtomo_PATH_v_1_3(NXtomo_PATH_v_1_2):
    VERSION = 1.3
    _NX_DETECTOR_PATHS = nxdetector.NEXUS_DETECTOR_PATH_V_1_3
    _NX_INSTRUMENT_PATHS = nxinstrument.NEXUS_INSTRUMENT_PATH_V_1_3
    _NX_SAMPLE_PATHS = nxsample.NEXUS_SAMPLE_PATH_V_1_3
    _NX_SOURCE_PATHS = nxsource.NEXUS_SOURCE_PATH_V_1_3
    _NX_TRANSFORMATIONS_PATHS = nxtransformations.NEXUS_TRANSFORMATIONS_PATH_V_1_3


nx_tomo_path_v_1_3 = NXtomo_PATH_v_1_3()

# V 1.4


class NXtomo_PATH_v_1_4(NXtomo_PATH_v_1_3):
    VERSION = 1.4
    _NX_DETECTOR_PATHS = nxdetector.NEXUS_DETECTOR_PATH_V_1_4
    _NX_INSTRUMENT_PATHS = nxinstrument.NEXUS_INSTRUMENT_PATH_V_1_4
    _NX_SAMPLE_PATHS = nxsample.NEXUS_SAMPLE_PATH_V_1_4
    _NX_SOURCE_PATHS = nxsource.NEXUS_SOURCE_PATH_V_1_4
    _NX_TRANSFORMATIONS_PATHS = nxtransformations.NEXUS_TRANSFORMATIONS_PATH_V_1_4


nx_tomo_path_v_1_4 = NXtomo_PATH_v_1_4()

# V 1.5


class NXtomo_PATH_v_1_5(NXtomo_PATH_v_1_4):
    VERSION = 1.5
    _NX_DETECTOR_PATHS = nxdetector.NEXUS_DETECTOR_PATH_V_1_5
    _NX_INSTRUMENT_PATHS = nxinstrument.NEXUS_INSTRUMENT_PATH_V_1_5
    _NX_SAMPLE_PATHS = nxsample.NEXUS_SAMPLE_PATH_V_1_5
    _NX_SOURCE_PATHS = nxsource.NEXUS_SOURCE_PATH_V_1_5
    _NX_TRANSFORMATIONS_PATHS = nxtransformations.NEXUS_TRANSFORMATIONS_PATH_V_1_5

    @property
    def X_PIXEL_SIZE(self):
        raise NotImplementedError("Removed since 1.5 nexus version")

    @property
    def Y_PIXEL_SIZE(self):
        raise NotImplementedError("Removed since 1.5 nexus version")

    @property
    def DETECTOR_X_PIXEL_SIZE_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.X_PIXEL_SIZE,
            ]
        )

    @property
    def DETECTOR_Y_PIXEL_SIZE_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.DETECTOR_PATH,
                self.nx_detector_paths.Y_PIXEL_SIZE,
            ]
        )

    @property
    def SAMPLE_X_PIXEL_SIZE_PATH(self) -> str:
        return "/".join(
            [
                self.SAMPLE_PATH,
                self.nx_sample_paths.X_PIXEL_SIZE,
            ]
        )

    @property
    def SAMPLE_Y_PIXEL_SIZE_PATH(self) -> str:
        return "/".join(
            [
                self.SAMPLE_PATH,
                self.nx_sample_paths.Y_PIXEL_SIZE,
            ]
        )

    @property
    def PROPAGATION_DISTANCE(self) -> str:
        return "/".join(
            [
                self.SAMPLE_PATH,
                self.nx_sample_paths.PROPAGATION_DISTANCE,
            ]
        )

    @property
    def SAMPLE_SOURCE_DISTANCE_PATH(self) -> str:
        return "/".join(
            [
                self.INSTRUMENT_PATH,
                self.nx_instrument_paths.SOURCE,
                self.nx_source_paths.DISTANCE,
            ]
        )


nx_tomo_path_v_1_5 = NXtomo_PATH_v_1_5()


class NXtomo_PATH_v_2_0(NXtomo_PATH_v_1_5):
    # Warning: there was no modification on the path but
    # this is a milestone when moving to McStas
    VERSION = 2.0


nx_tomo_path_v_2_0 = NXtomo_PATH_v_2_0()


nx_tomo_path_latest = nx_tomo_path_v_2_0


def get_paths(version: float | None) -> NXtomo_PATH:
    if version is None:
        version = LATEST_VERSION
        _logger.warning(
            f"version of the NXtomo not found. Will take the latest one ({LATEST_VERSION})"
        )
    versions_dict = {
        # Ensure compatibility with "old" datasets (acquired before Dec. 2021).
        # nxtomo can still parse them provided that nx_version=1.0 is forced at init.
        0.0: nx_tomo_path_v_1_0,
        0.1: nx_tomo_path_v_1_0,
        #
        1.0: nx_tomo_path_v_1_0,
        1.1: nx_tomo_path_v_1_1,
        1.2: nx_tomo_path_v_1_2,
        1.3: nx_tomo_path_v_1_3,
        1.4: nx_tomo_path_v_1_4,
        1.5: nx_tomo_path_v_1_5,
        2.0: nx_tomo_path_v_2_0,
    }
    if version not in versions_dict:
        if int(version) == 1:
            _logger.warning(
                f"nexus path {version} requested but unknown from this version of nxtomo {nxtomo.__version__}. Pick latest one of this major version. You might miss some information"
            )
            version = LATEST_VERSION
        else:
            raise ValueError(f"Unknown major version of the nexus path ({version})")
    return versions_dict[version]
