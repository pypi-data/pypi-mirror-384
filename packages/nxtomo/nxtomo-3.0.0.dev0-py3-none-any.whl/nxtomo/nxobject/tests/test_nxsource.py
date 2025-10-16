import pint
import pytest

from nxtomo.nxobject.nxsource import NXsource

ureg = pint.get_application_registry()

meter = ureg.meter


def test_nx_source():
    """Test creation and saving of an NXsource."""
    nx_source = NXsource()

    with pytest.raises(TypeError):
        nx_source.name = 12
    nx_source.name = "my source"

    with pytest.raises(AttributeError):
        nx_source.source_name = "test"

    with pytest.raises(ValueError):
        nx_source.type = "toto"
    nx_source.type = "Synchrotron X-ray Source"
    str(nx_source)
    nx_source.type = None
    str(nx_source)

    assert nx_source.probe is None
    nx_source.probe = "neutron"
    assert nx_source.probe.value == "neutron"
    with pytest.raises(ValueError):
        nx_source.probe = 12

    assert nx_source.distance is None

    nx_source.distance = 12.6 * meter
    assert nx_source.distance.magnitude == 12.6
    assert nx_source.distance.units == "meter"

    with pytest.raises(TypeError):
        nx_source.distance = "ddsad"

    assert isinstance(nx_source.to_nx_dict(), dict)

    # Check we can't set undefined attributes
    with pytest.raises(AttributeError):
        nx_source.test = 12

    # Test some concatenation
    nx_source_concatenate = NXsource.concatenate([nx_source, nx_source])
    assert nx_source_concatenate.name == "my source"
    assert nx_source_concatenate.type is None
    assert nx_source_concatenate.probe.value == "neutron"
    assert nx_source_concatenate.distance.magnitude == 12.6
    assert nx_source_concatenate.distance.units == "meter"
