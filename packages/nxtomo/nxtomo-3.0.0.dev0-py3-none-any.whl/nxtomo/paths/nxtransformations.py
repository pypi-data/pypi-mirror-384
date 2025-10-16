"""NeXus paths used to define an `NXtransformations <https://manual.nexusformat.org/classes/base_classes/NXtransformations.html>`_."""


class NEXUS_TRANSFORMATIONS_PATH:
    TRANSFORMATION_TYPE = "@transformation_type"
    VECTOR = "@vector"
    OFFSET = "@offset"
    EQUIPMENT_COMPONENT = "@equipment_component"
    DEPENDS_ON = "@depends_on"


class NEXUS_TRANSFORMATIONS_PATH_V_1_0(NEXUS_TRANSFORMATIONS_PATH):
    pass


class NEXUS_TRANSFORMATIONS_PATH_V_1_1(NEXUS_TRANSFORMATIONS_PATH_V_1_0):
    pass


class NEXUS_TRANSFORMATIONS_PATH_V_1_2(NEXUS_TRANSFORMATIONS_PATH_V_1_1):
    pass


class NEXUS_TRANSFORMATIONS_PATH_V_1_3(NEXUS_TRANSFORMATIONS_PATH_V_1_2):
    pass


class NEXUS_TRANSFORMATIONS_PATH_V_1_4(NEXUS_TRANSFORMATIONS_PATH_V_1_3):
    pass


class NEXUS_TRANSFORMATIONS_PATH_V_1_5(NEXUS_TRANSFORMATIONS_PATH_V_1_4):
    pass
