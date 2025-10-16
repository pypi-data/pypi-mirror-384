import numpy
import pint
import pytest

from nxtomo.nxobject.nxmonitor import NXmonitor
from nxtomo.nxobject.utils.concatenate import concatenate

_ureg = pint.UnitRegistry()


def test_nx_sample():
    """Test creation and saving of an NXmonitor."""
    nx_monitor = NXmonitor()
    # check name
    with pytest.raises(TypeError):
        nx_monitor.data = 12
    with pytest.raises(ValueError):
        nx_monitor.data = numpy.zeros([12, 12])
    nx_monitor.data = tuple()
    nx_monitor.data = numpy.zeros(12)

    assert isinstance(nx_monitor.to_nx_dict(), dict)

    # test concatenate
    nx_monitor_1 = NXmonitor()
    nx_monitor_1.data = numpy.arange(10)
    nx_monitor_2 = NXmonitor()
    nx_monitor_2.data = numpy.arange(10)[::-1] * _ureg.milliampere

    nx_monitor_concat = concatenate([nx_monitor_1, nx_monitor_2])
    assert isinstance(nx_monitor_concat, NXmonitor)
    numpy.testing.assert_array_equal(
        nx_monitor_concat.data,
        numpy.concatenate(
            [
                nx_monitor_1.data,
                nx_monitor_2.data,
            ]
        ),
    )
