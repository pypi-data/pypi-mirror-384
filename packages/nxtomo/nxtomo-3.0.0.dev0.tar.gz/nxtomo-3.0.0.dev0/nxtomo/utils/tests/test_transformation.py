import numpy
import pint
import pytest

from nxtomo.paths.nxtransformations import NEXUS_TRANSFORMATIONS_PATH
from nxtomo.utils.transformation import (
    DetXFlipTransformation,
    DetYFlipTransformation,
    DetZFlipTransformation,
    GravityTransformation,
    Transformation,
    TransformationAxis,
    TransformationType,
    build_matrix,
    get_lr_flip,
    get_ud_flip,
)

_ureg = pint.UnitRegistry()


def test_Transformation():
    """
    test Transformation class
    """
    transformation_translation = Transformation(
        axis_name="tz",
        value=12.2 * _ureg.meter,
        transformation_type="translation",
        vector=TransformationAxis.AXIS_Z,
    )

    # test defining units
    transformation_translation = Transformation(
        axis_name="tx",
        value=45 * _ureg.meter,
        transformation_type=TransformationType.TRANSLATION,
        vector=(0, 1, 0),
    )
    with pytest.raises(pint.DimensionalityError):
        transformation_translation.transformation_values = (
            transformation_translation.transformation_values.to("degree")
        )
    transformation_translation.transformation_values = (
        transformation_translation.transformation_values.to("cm")
    )

    transformation_rotation = Transformation(
        axis_name="rx",
        value=(45, 56, 89) * _ureg.degree,
        transformation_type="rotation",
        vector=TransformationAxis.AXIS_X,
    )
    with pytest.raises(pint.DimensionalityError):
        transformation_rotation.transformation_values = (
            transformation_rotation.transformation_values.to("cm")
        )
    transformation_rotation.transformation_values = (
        transformation_rotation.transformation_values.to("degree")
    )

    # make sure the API is freezed
    with pytest.raises(AttributeError):
        transformation_rotation.toto = "test"

    # test from / to dict functions
    transformations_nexus_paths = NEXUS_TRANSFORMATIONS_PATH

    assert transformation_translation == Transformation.from_nx_dict(
        axis_name=transformation_translation.axis_name,
        dict_=transformation_translation.to_nx_dict(
            transformations_nexus_paths=transformations_nexus_paths,
            data_path="",
        ),
        transformations_nexus_paths=transformations_nexus_paths,
    )
    assert transformation_rotation == Transformation.from_nx_dict(
        axis_name=transformation_rotation.axis_name,
        dict_=transformation_rotation.to_nx_dict(
            transformations_nexus_paths=transformations_nexus_paths,
            data_path="",
        ),
        transformations_nexus_paths=transformations_nexus_paths,
    )


def test_helpers():
    """simple test on some helper class / function"""
    DetXFlipTransformation(flip=True)
    DetYFlipTransformation(flip=True)
    DetZFlipTransformation(flip=True)


def test_get_lr_flip() -> tuple:
    """
    test `get_lr_flip` function
    """
    trans_as_rad = Transformation(
        axis_name="rad_rot",
        transformation_type="rotation",
        value=numpy.pi * _ureg.radian,
        vector=TransformationAxis.AXIS_Y,
    )
    assert trans_as_rad == DetYFlipTransformation(flip=True)
    transformations = (
        DetYFlipTransformation(flip=True),
        Transformation(
            axis_name="toto",
            transformation_type="rotation",
            value=-180 * _ureg.degree,
            vector=TransformationAxis.AXIS_Y,
        ),
        Transformation(
            axis_name="other",
            transformation_type="rotation",
            value=70 * _ureg.degree,
            vector=TransformationAxis.AXIS_Y,
        ),
        trans_as_rad,
        Transformation(
            axis_name="other2",
            transformation_type="rotation",
            value=180 * _ureg.degree,
            vector=TransformationAxis.AXIS_X,
        ),
    )
    assert get_lr_flip(transformations=transformations) == (
        DetYFlipTransformation(flip=True),
        Transformation(
            axis_name="toto",
            transformation_type="rotation",
            value=-180 * _ureg.degree,
            vector=TransformationAxis.AXIS_Y,
        ),
        trans_as_rad,
    )


def test_get_ud_flip() -> tuple:
    """
    test `get_ud_flip` function
    """
    transformations = (
        Transformation(
            axis_name="other",
            transformation_type="rotation",
            value=70 * _ureg.degree,
            vector=TransformationAxis.AXIS_Y,
        ),
        Transformation(
            axis_name="toto",
            transformation_type="rotation",
            value=-180 * _ureg.degree,
            vector=TransformationAxis.AXIS_X,
        ),
        DetXFlipTransformation(flip=True),
        Transformation(
            axis_name="other2",
            transformation_type="rotation",
            value=180 * _ureg.degree,
            vector=TransformationAxis.AXIS_X,
        ),
        DetYFlipTransformation(flip=True),
    )
    assert get_ud_flip(transformations=transformations) == (
        Transformation(
            axis_name="toto",
            transformation_type="rotation",
            value=-180 * _ureg.degree,
            vector=TransformationAxis.AXIS_X,
        ),
        DetXFlipTransformation(flip=True),
        Transformation(
            axis_name="other2",
            transformation_type="rotation",
            value=180 * _ureg.degree,
            vector=TransformationAxis.AXIS_X,
        ),
    )


def test_transformation_as_matrix():
    """
    test Transformation().as_matrix() function
    """
    numpy.testing.assert_array_equal(
        DetYFlipTransformation(flip=True).as_matrix(),
        numpy.array(
            [
                [numpy.cos(numpy.pi), 0, numpy.sin(numpy.pi)],
                [0, 1, 0],
                [-numpy.sin(numpy.pi), 0, numpy.cos(numpy.pi)],
            ],
            dtype=numpy.float32,
        ),
    )

    numpy.testing.assert_array_equal(
        DetZFlipTransformation(flip=True).as_matrix(),
        numpy.array(
            [
                [numpy.cos(numpy.pi), -numpy.sin(numpy.pi), 0],
                [numpy.sin(numpy.pi), numpy.cos(numpy.pi), 0],
                [0, 0, 1],
            ],
            dtype=numpy.float32,
        ),
    )

    with pytest.raises(ValueError):
        Transformation(
            axis_name="rx",
            transformation_type="rotation",
            value=None,
            vector=(1, 0, 0),
        ).as_matrix()

    with pytest.raises(ValueError):
        Transformation(
            axis_name="rx",
            transformation_type="rotation",
            value=None,
            vector=(1, 0, 0),
        ).as_matrix()

    with pytest.raises(ValueError):
        Transformation(
            axis_name="rx",
            transformation_type="rotation",
            value=1 * _ureg.degree,
            vector=(0, 0, 0),
        ).as_matrix()


def test_build_matrix():
    """ """
    gravity = GravityTransformation()
    rz = DetZFlipTransformation(flip=True, depends_on="gravity")
    ry = DetYFlipTransformation(flip=True, depends_on="rz")
    tx = Transformation(
        axis_name="tx",
        transformation_type=TransformationType.TRANSLATION,
        depends_on="ry",
        vector=TransformationAxis.AXIS_X,
        value=5 * _ureg.meter,
    )

    expected_result = numpy.matmul(
        numpy.matmul(
            numpy.array(
                [
                    [numpy.cos(numpy.pi), -numpy.sin(numpy.pi), 0],
                    [numpy.sin(numpy.pi), numpy.cos(numpy.pi), 0],
                    [0, 0, 1],
                ],
                dtype=numpy.float32,
            ),
            numpy.array(
                [
                    [numpy.cos(numpy.pi), 0, numpy.sin(numpy.pi)],
                    [0, 1, 0],
                    [-numpy.sin(numpy.pi), 0, numpy.cos(numpy.pi)],
                ],
                dtype=numpy.float32,
            ),
        ),
        numpy.array(
            [
                [5, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
            ],
            dtype=numpy.float32,
        ),
    )

    numpy.testing.assert_array_almost_equal(
        expected_result,
        build_matrix([gravity, rz, ry, tx]),
    )

    # test incoherence on the resolution chain
    rz2 = DetZFlipTransformation(flip=True, depends_on="unknown axis")
    with pytest.raises(ValueError):
        build_matrix([gravity, rz2, ry, tx]),
