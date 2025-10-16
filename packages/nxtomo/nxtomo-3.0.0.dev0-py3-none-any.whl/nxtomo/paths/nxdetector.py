"""NeXus paths used to define an `NXdetector <https://manual.nexusformat.org/classes/base_classes/NXdetector.html>`_."""


class NEXUS_DETECTOR_PATH:
    DATA = "data"

    IMAGE_KEY_CONTROL = "image_key_control"

    IMAGE_KEY = "image_key"

    X_PIXEL_SIZE = "x_pixel_size"

    Y_PIXEL_SIZE = "y_pixel_size"

    X_PIXEL_SIZE_MAGNIFIED = "x_magnified_pixel_size"

    Y_PIXEL_SIZE_MAGNIFIED = "y_magnified_pixel_size"

    X_REAL_PIXEL_SIZE = "real_x_pixel_size"

    Y_REAL_PIXEL_SIZE = "real_y_pixel_size"

    MAGNIFICATION = "magnification"

    DISTANCE = "distance"

    FOV = "field_of_view"

    ESTIMATED_COR_FRM_MOTOR = "estimated_cor_from_motor"
    "warning: replace by Y_ROTATION_AXIS_PIXEL_POSITION"

    ROI = "roi"

    EXPOSURE_TIME = "count_time"

    X_FLIPPED = "x_flipped"

    Y_FLIPPED = "y_flipped"

    NX_TRANSFORMATIONS = None
    # path in the NXdetector where are store the transformations

    X_ROTATION_AXIS_PIXEL_POSITION = None

    Y_ROTATION_AXIS_PIXEL_POSITION = None

    SEQUENCE_NUMBER = None


class NEXUS_DETECTOR_PATH_V_1_0(NEXUS_DETECTOR_PATH):
    pass


class NEXUS_DETECTOR_PATH_V_1_1(NEXUS_DETECTOR_PATH):
    pass


class NEXUS_DETECTOR_PATH_V_1_2(NEXUS_DETECTOR_PATH_V_1_1):
    pass


class NEXUS_DETECTOR_PATH_V_1_3(NEXUS_DETECTOR_PATH_V_1_2):
    # in this version we expect `x_flipped`, `y_flipped` to be replaced by  ̀TRANSFORMATIONS` NXtransformations group
    NX_TRANSFORMATIONS = "transformations"

    X_FLIPPED = None

    Y_FLIPPED = None


class NEXUS_DETECTOR_PATH_V_1_4(NEXUS_DETECTOR_PATH_V_1_3):

    ESTIMATED_COR_FRM_MOTOR = None  # replaced by 'X_ROTATION_AXIS_PIXEL_POSITION'

    X_ROTATION_AXIS_PIXEL_POSITION = "x_rotation_axis_pixel_position"

    Y_ROTATION_AXIS_PIXEL_POSITION = "y_rotation_axis_pixel_position"


class NEXUS_DETECTOR_PATH_V_1_5(NEXUS_DETECTOR_PATH_V_1_4):

    SEQUENCE_NUMBER = "sequence_number"
