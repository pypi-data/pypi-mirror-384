# coding: utf-8
# /*##########################################################################
# Copyright (C) 2016-2020 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#############################################################################

"""Test compatibility with previously existing NexusPath classes."""


__authors__ = ["H.Payno"]
__license__ = "MIT"
__date__ = "10/02/2022"


import pytest

from nxtomo.paths.nxtomo import get_paths as new_get_paths
from nxtomo.paths.nxtomo import nx_tomo_path_latest


# classes which were previously defining path to save data as NXtomo from tomoscan.esrf.scan.nxtomoscan.py file
class _NEXUS_PATHS:
    """Register paths for NXtomo.
    The raw data are those of the initial version.
    If the value is None then the path did not exist originally.
    """

    PROJ_PATH = "instrument/detector/data"

    SCAN_META_PATH = "scan_meta/technique/scan"

    DET_META_PATH = "scan_meta/technique/detector"

    ROTATION_ANGLE_PATH = "sample/rotation_angle"

    SAMPLE_PATH = "sample"

    NAME_PATH = "sample/name"

    GRP_SIZE_ATTR = "group_size"

    SAMPLE_NAME_PATH = "sample/sample_name"

    X_TRANS_PATH = "sample/x_translation"

    Y_TRANS_PATH = "sample/y_translation"

    Z_TRANS_PATH = "sample/z_translation"

    IMG_KEY_PATH = "instrument/detector/image_key"

    IMG_KEY_CONTROL_PATH = "instrument/detector/image_key_control"

    X_PIXEL_SIZE_PATH = "instrument/detector/x_pixel_size"

    Y_PIXEL_SIZE_PATH = "instrument/detector/y_pixel_size"

    X_PIXEL_MAG_SIZE_PATH = "instrument/detector/x_magnified_pixel_size"

    Y_PIXEL_MAG_SIZE_PATH = "instrument/detector/y_magnified_pixel_size"

    DISTANCE_PATH = "instrument/detector/distance"

    FOV_PATH = "instrument/detector/field_of_view"

    EXPOSURE_TIME_PATH = "instrument/detector/count_time"

    TOMO_N_SCAN = "instrument/detector/tomo_n"

    ENERGY_PATH = "beam/incident_energy"

    START_TIME_PATH = "start_time"

    END_TIME_START = "end_time"  # typo - deprecated

    END_TIME_PATH = "end_time"

    INTENSITY_MONITOR_PATH = "diode/data"

    SOURCE_NAME = None

    SOURCE_TYPE = None

    SOURCE_PROBE = None

    INSTRUMENT_NAME = None


class _NEXUS_PATHS_V_1_0(_NEXUS_PATHS):
    pass


class _NEXUS_PATHS_V_1_1(_NEXUS_PATHS_V_1_0):
    ENERGY_PATH = "instrument/beam/incident_energy"

    SOURCE_NAME = "instrument/source/name"

    SOURCE_TYPE = "instrument/source/type"

    SOURCE_PROBE = "instrument/source/probe"

    INSTRUMENT_NAME = "instrument/name"

    NAME_PATH = "title"

    SAMPLE_NAME_PATH = "sample/name"


_class_to_compare_versions = {
    1.0: (_NEXUS_PATHS_V_1_0, new_get_paths(1.0)),
    1.1: (_NEXUS_PATHS_V_1_1, new_get_paths(1.1)),
}


@pytest.mark.parametrize("path_version", (1.0, 1.1))
def test_compare_result(path_version):
    """Ensure the new way of providing NeXus paths does not break the previous API or values."""
    old_class, new_class = _class_to_compare_versions[path_version]
    assert old_class.PROJ_PATH == new_class.PROJ_PATH
    assert old_class.SCAN_META_PATH == new_class.SCAN_META_PATH
    assert old_class.DET_META_PATH == new_class.DET_META_PATH
    assert old_class.ROTATION_ANGLE_PATH == new_class.ROTATION_ANGLE_PATH
    assert old_class.SAMPLE_PATH == new_class.SAMPLE_PATH
    assert old_class.NAME_PATH == new_class.NAME_PATH
    assert old_class.GRP_SIZE_ATTR == new_class.GRP_SIZE_ATTR
    assert old_class.SAMPLE_NAME_PATH == new_class.SAMPLE_NAME_PATH
    assert old_class.X_TRANS_PATH == new_class.X_TRANS_PATH
    assert old_class.Y_TRANS_PATH == new_class.Y_TRANS_PATH
    assert old_class.Z_TRANS_PATH == new_class.Z_TRANS_PATH
    assert old_class.IMG_KEY_PATH == new_class.IMG_KEY_PATH
    assert old_class.IMG_KEY_CONTROL_PATH == new_class.IMG_KEY_CONTROL_PATH
    assert old_class.X_PIXEL_SIZE_PATH == new_class.X_PIXEL_SIZE_PATH
    assert old_class.Y_PIXEL_SIZE_PATH == new_class.Y_PIXEL_SIZE_PATH
    assert old_class.DISTANCE_PATH == new_class.DISTANCE_PATH
    assert old_class.FOV_PATH == new_class.FOV_PATH
    assert old_class.EXPOSURE_TIME_PATH == new_class.EXPOSURE_TIME_PATH
    assert old_class.TOMO_N_SCAN == new_class.TOMO_N_SCAN
    assert old_class.ENERGY_PATH == new_class.ENERGY_PATH
    assert old_class.START_TIME_PATH == new_class.START_TIME_PATH
    assert old_class.END_TIME_PATH == new_class.END_TIME_PATH
    assert old_class.INTENSITY_MONITOR_PATH == new_class.INTENSITY_MONITOR_PATH
    assert old_class.SOURCE_NAME == new_class.SOURCE_NAME
    assert old_class.SOURCE_TYPE == new_class.SOURCE_TYPE
    assert old_class.INSTRUMENT_NAME == new_class.INSTRUMENT_NAME


def test_unknow_nexus_path_version():
    assert new_get_paths(None) == nx_tomo_path_latest
    assert new_get_paths(1.99) == nx_tomo_path_latest
    with pytest.raises(ValueError):
        assert new_get_paths(-1.0) is None
    with pytest.raises(ValueError):
        assert new_get_paths(999.0) is None
