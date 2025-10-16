"""NeXus paths used to define an `NXsample <https://manual.nexusformat.org/classes/base_classes/NXsample.html>`_."""

from . import nxtransformations


class NEXUS_SAMPLE_PATH:
    NAME = "sample_name"

    ROTATION_ANGLE = "rotation_angle"

    X_TRANSLATION = "x_translation"

    Y_TRANSLATION = "y_translation"

    Z_TRANSLATION = "z_translation"

    NX_TRANSFORMATIONS = None

    NX_TRANSFORMATIONS_PATHS = None

    PROPAGATION_DISTANCE = None

    X_PIXEL_SIZE = None

    Y_PIXEL_SIZE = None


class NEXUS_SAMPLE_PATH_V_1_0(NEXUS_SAMPLE_PATH):
    pass


class NEXUS_SAMPLE_PATH_V_1_1(NEXUS_SAMPLE_PATH_V_1_0):
    NAME = "name"


class NEXUS_SAMPLE_PATH_V_1_2(NEXUS_SAMPLE_PATH_V_1_1):
    pass


class NEXUS_SAMPLE_PATH_V_1_3(NEXUS_SAMPLE_PATH_V_1_2):
    NX_TRANSFORMATIONS = "transformations"

    NX_TRANSFORMATIONS_PATHS = nxtransformations.NEXUS_TRANSFORMATIONS_PATH_V_1_3


class NEXUS_SAMPLE_PATH_V_1_4(NEXUS_SAMPLE_PATH_V_1_3):
    pass


class NEXUS_SAMPLE_PATH_V_1_5(NEXUS_SAMPLE_PATH_V_1_4):
    PROPAGATION_DISTANCE = "propagation_distance"

    X_PIXEL_SIZE = "x_pixel_size"

    Y_PIXEL_SIZE = "y_pixel_size"
