"""NeXus paths used to define an `NXsource <https://manual.nexusformat.org/classes/base_classes/NXsource.html>`_."""


class NEXUS_SOURCE_PATH:
    NAME = "name"
    TYPE = "type"
    PROBE = "probe"
    DISTANCE = None


class NEXUS_SOURCE_PATH_V_1_0(NEXUS_SOURCE_PATH):
    pass


class NEXUS_SOURCE_PATH_V_1_1(NEXUS_SOURCE_PATH_V_1_0):
    pass


class NEXUS_SOURCE_PATH_V_1_2(NEXUS_SOURCE_PATH_V_1_1):
    pass


class NEXUS_SOURCE_PATH_V_1_3(NEXUS_SOURCE_PATH_V_1_2):
    pass


class NEXUS_SOURCE_PATH_V_1_4(NEXUS_SOURCE_PATH_V_1_3):
    DISTANCE = "distance"


class NEXUS_SOURCE_PATH_V_1_5(NEXUS_SOURCE_PATH_V_1_4):
    pass
