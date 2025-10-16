import numpy
import pint
import pytest

from nxtomo.nxobject.nxsample import NXsample

ureg = pint.get_application_registry()
degree = ureg.degree
meter = ureg.meter


def test_nx_sample():
    """Test creation and saving of an NXsample."""
    nx_sample = NXsample()
    # check name
    with pytest.raises(TypeError):
        nx_sample.name = 12
    nx_sample.name = "my sample"

    # check rotation angle
    with pytest.raises(TypeError):
        nx_sample.rotation_angle = 56
    nx_sample.rotation_angle = numpy.linspace(0, 180, 180, endpoint=False) * degree

    # check x translation
    with pytest.raises(TypeError):
        nx_sample.x_translation = 56
    nx_sample.x_translation = numpy.linspace(0, 180, 180, endpoint=False) * meter

    # check y translation
    with pytest.raises(TypeError):
        nx_sample.y_translation = 56
    nx_sample.y_translation = [0.0] * 180 * meter

    # check z translation
    with pytest.raises(TypeError):
        nx_sample.z_translation = 56
    nx_sample.z_translation = None

    # check propagation distance
    with pytest.raises(TypeError):
        nx_sample.propagation_distance = "45"
    nx_sample.propagation_distance = None
    nx_sample.propagation_distance = 12.2 * ureg.centimeter

    # check pixel size
    with pytest.raises(TypeError):
        nx_sample.x_pixel_size = "toto"
    nx_sample.x_pixel_size = 12.6 * ureg.meter
    nx_sample.y_pixel_size = 5.6 * ureg.centimeter

    assert isinstance(nx_sample.to_nx_dict(), dict)

    # check we can't set undefined attributes
    with pytest.raises(AttributeError):
        nx_sample.test = 12

    # test concatenation
    nx_sample_concat = NXsample.concatenate([nx_sample, nx_sample])
    assert nx_sample_concat.name == "my sample"
    numpy.testing.assert_array_equal(
        nx_sample_concat.rotation_angle,
        numpy.concatenate(
            [
                numpy.linspace(0, 180, 180, endpoint=False),
                numpy.linspace(0, 180, 180, endpoint=False),
            ]
        ),
    )

    numpy.testing.assert_array_equal(
        nx_sample_concat.x_translation,
        numpy.concatenate(
            [
                numpy.linspace(0, 180, 180, endpoint=False),
                numpy.linspace(0, 180, 180, endpoint=False),
            ]
        ),
    )

    numpy.testing.assert_array_equal(
        nx_sample_concat.y_translation,
        numpy.concatenate(
            [
                numpy.asarray([0.0] * 180),
                numpy.asarray([0.0] * 180),
            ]
        ),
    )

    assert nx_sample_concat.z_translation is None
    assert nx_sample_concat.x_pixel_size == nx_sample.x_pixel_size
    assert nx_sample_concat.y_pixel_size == nx_sample.y_pixel_size
