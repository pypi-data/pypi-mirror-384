import numpy
import pint
import pytest

from nxtomo.nxobject.nxtransformations import NXtransformations
from nxtomo.utils.transformation import (
    GravityTransformation,
    Transformation,
    TransformationAxis,
)

_ureg = pint.UnitRegistry()


def test_nx_transformations(tmp_path):
    """test creation and saving of an NXtransformations"""
    nx_transformations_1 = NXtransformations()
    with pytest.raises(TypeError):
        nx_transformations_1.transformations = 12
    with pytest.raises(TypeError):
        nx_transformations_1.transformations = {12: 12}

    translation_along_x = Transformation(
        axis_name="tx",
        value=9.6 * _ureg.meter,
        transformation_type="translation",
        vector=TransformationAxis.AXIS_X,
    )
    nx_transformations_1.add_transformation(
        transformation=translation_along_x,
    )
    rotation_along_z = Transformation(
        axis_name="rz",
        value=90 * _ureg.degree,
        transformation_type="rotation",
        vector=TransformationAxis.AXIS_Z,
    )
    rotation_along_z.offset = (12.0, 0, 0)
    assert numpy.array_equal(rotation_along_z.offset, numpy.array([12.0, 0, 0]))
    rotation_along_z.transformation_values = rotation_along_z.transformation_values.to(
        "deg"
    )

    rotation_along_z.depends_on = "tx"
    assert rotation_along_z.depends_on == "tx"
    with pytest.raises(AttributeError):
        rotation_along_z.vector = TransformationAxis.AXIS_Z
    assert rotation_along_z.vector == (0, 0, 1)

    nx_transformations_1.add_transformation(
        rotation_along_z,
    )
    assert len(nx_transformations_1.transformations) == 2

    assert nx_transformations_1.to_nx_dict(data_path="") == {
        # ty specifics
        "tx": 9.6,
        "tx@transformation_type": "translation",
        "tx@units": "m",
        "tx@vector": (1, 0, 0),
        "tx@offset": (0, 0, 0),
        # tx specifics
        "rz": 90,
        "rz@depends_on": "tx",
        "rz@offset": (12.0, 0, 0),
        "rz@transformation_type": "rotation",
        "rz@units": "deg",
        "rz@vector": (0, 0, 1),
        # class attributes
        "@NX_class": "NX_transformations",
        "@units": "NX_TRANSFORMATION",
    }

    # check solving empty dependancy
    assert nx_transformations_1.to_nx_dict(
        data_path="", solve_empty_dependency=True
    ) == {
        # ty specifics
        "tx": 9.6,
        "tx@transformation_type": "translation",
        "tx@units": "m",
        "tx@vector": (1, 0, 0),
        "tx@offset": (0, 0, 0),
        "tx@depends_on": "gravity",
        # tx specifics
        "rz": 90,
        "rz@depends_on": "tx",
        "rz@offset": (12.0, 0, 0),
        "rz@transformation_type": "rotation",
        "rz@units": "deg",
        "rz@vector": (0, 0, 1),
        # gravity
        "gravity": 9.80665,
        "gravity@offset": (0, 0, 0),
        "gravity@transformation_type": "gravity",
        "gravity@units": "m / s ** 2",
        "gravity@vector": (0, 0, -1),
        # class attributes
        "@NX_class": "NX_transformations",
        "@units": "NX_TRANSFORMATION",
    }

    nx_transformations_2 = NXtransformations()
    nx_transformations_2.transformations = (
        Transformation(
            "rx", 60 * _ureg.degree, "rotation", vector=TransformationAxis.AXIS_X
        ),
        Transformation(
            "rz", -60 * _ureg.degree, "rotation", vector=TransformationAxis.AXIS_Z
        ),
    )

    assert NXtransformations.concatenate(
        [nx_transformations_2, nx_transformations_1]
    ).transformations == (
        Transformation(
            "rx", 60 * _ureg.degree, "rotation", vector=TransformationAxis.AXIS_X
        ),
        Transformation(
            "rz", -60 * _ureg.degree, "rotation", vector=TransformationAxis.AXIS_Z
        ),
        translation_along_x,
    )

    assert NXtransformations.concatenate(
        [nx_transformations_1, nx_transformations_2]
    ).transformations != (
        translation_along_x,
        Transformation(
            "rx", 60 * _ureg.degree, "rotation", vector=TransformationAxis.AXIS_X
        ),
        Transformation(
            "rz", -60 * _ureg.degree, "rotation", vector=TransformationAxis.AXIS_Z
        ),
    )

    # save NXtransformation to file and load it
    output_file_path = str(tmp_path / "test_nxtransformations.nx")
    nx_transformations_2.save(output_file_path, "transformations")
    assert len(nx_transformations_2.transformations) == 2

    # test backward compatibility
    loaded_transformations = NXtransformations()._load(
        output_file_path, "transformations", 1.2
    )
    assert isinstance(loaded_transformations, NXtransformations)
    assert len(loaded_transformations.transformations) == 0

    # test backward compatibility
    loaded_transformations = NXtransformations()._load(
        output_file_path, "transformations", 1.3
    )
    assert isinstance(loaded_transformations, NXtransformations)
    assert len(loaded_transformations.transformations) == 2
    assert loaded_transformations == nx_transformations_2

    # check that Gravity will not affect the equality
    nx_transformations_2.add_transformation(GravityTransformation())
    assert loaded_transformations == nx_transformations_2

    loaded_transformations.add_transformation(GravityTransformation())
    assert loaded_transformations == nx_transformations_2

    output_file_path_2 = str(tmp_path / "test_nxtransformations.nx")
    nx_transformations_2.save(output_file_path_2, "/entry/toto/transformations")

    loaded_transformations = NXtransformations()._load(
        output_file_path_2, "/entry/toto/transformations", 1.3
    )
    assert isinstance(loaded_transformations, NXtransformations)
    assert len(loaded_transformations.transformations) == 3
    assert loaded_transformations == nx_transformations_2
