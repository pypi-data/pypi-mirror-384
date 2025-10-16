"""NeXus paths used to define an `NXinstrument <https://manual.nexusformat.org/classes/base_classes/NXinstrument.html>`_."""


class NEXUS_INSTRUMENT_PATH:
    DETECTOR_PATH = "detector"
    DIODE = None
    SOURCE = None
    BEAM = None
    NAME = None


class NEXUS_INSTRUMENT_PATH_V_1_0(NEXUS_INSTRUMENT_PATH):
    pass


class NEXUS_INSTRUMENT_PATH_V_1_1(NEXUS_INSTRUMENT_PATH_V_1_0):
    SOURCE = "source"
    BEAM = "beam"
    NAME = "name"


class NEXUS_INSTRUMENT_PATH_V_1_2(NEXUS_INSTRUMENT_PATH_V_1_1):
    DIODE = "diode"


class NEXUS_INSTRUMENT_PATH_V_1_3(NEXUS_INSTRUMENT_PATH_V_1_2):
    pass


class NEXUS_INSTRUMENT_PATH_V_1_4(NEXUS_INSTRUMENT_PATH_V_1_3):
    pass


class NEXUS_INSTRUMENT_PATH_V_1_5(NEXUS_INSTRUMENT_PATH_V_1_4):
    pass
