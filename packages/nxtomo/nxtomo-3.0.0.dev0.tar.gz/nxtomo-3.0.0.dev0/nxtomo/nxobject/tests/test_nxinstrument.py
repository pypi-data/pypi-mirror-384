import pytest

from nxtomo.nxobject.nxdetector import NXdetector
from nxtomo.nxobject.nxinstrument import NXinstrument
from nxtomo.nxobject.nxsource import DefaultESRFSource, NXsource


def test_nx_instrument():
    """Test creation and saving of an NXinstrument."""
    nx_instrument = NXinstrument()

    # check data
    with pytest.raises(TypeError):
        nx_instrument.detector = 12
    nx_instrument.detector = NXdetector(node_name="test")

    with pytest.raises(TypeError):
        nx_instrument.diode = 12
    nx_instrument.diode = NXdetector(node_name="test 2")

    with pytest.raises(TypeError):
        nx_instrument.source = 12
    nx_instrument.source = DefaultESRFSource()

    with pytest.raises(TypeError):
        nx_instrument.diode = NXsource(node_name="my source")
    nx_instrument.diode = NXdetector(node_name="det34")

    assert isinstance(nx_instrument.to_nx_dict(), dict)

    with pytest.raises(TypeError):
        nx_instrument.name = 12
    nx_instrument.name = "test name"
    assert nx_instrument.name == "test name"

    # check we can't set undefined attributes
    with pytest.raises(AttributeError):
        nx_instrument.test = 12

    # test concatenation
    nx_instrument_concat = NXinstrument.concatenate([nx_instrument, nx_instrument])
    assert nx_instrument_concat.name == "test name"
