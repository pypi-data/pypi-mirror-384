import os
import tempfile

import h5py
import numpy.random
import pint
import pytest
from silx.io.url import DataUrl

from nxtomo.io import cwd_context
from nxtomo.nxobject.nxdetector import (
    FieldOfView,
    ImageKey,
    NXdetector,
    NXdetectorWithUnit,
)
from nxtomo.utils.transformation import (
    DetXFlipTransformation,
    DetYFlipTransformation,
    Transformation,
    TransformationAxis,
)

_ureg = pint.UnitRegistry()
_volt = _ureg.volt
_second = _ureg.second
_meter = _ureg.meter
_degree = _ureg.degree


def test_nx_detector():
    """Test creation and saving of an NXdetector."""
    nx_detector = NXdetector(expected_dim=(2, 3))

    # check data
    with pytest.raises(TypeError):
        nx_detector.data = 12
    # if expected dims is not fulfill
    with pytest.raises(ValueError):
        nx_detector.data = numpy.random.random(100 * 100 * 5).reshape(5, 10, 10, 100)
    with pytest.raises(TypeError):
        nx_detector.data = (
            12,
            13,
        )
    nx_detector.data = numpy.random.random(100 * 100 * 5).reshape(5, 100, 100)

    # check image key control
    with pytest.raises(TypeError):
        nx_detector.image_key_control = 12
    nx_detector.image_key_control = [1] * 5
    nx_detector.image_key_control = [ImageKey.PROJECTION] * 5

    # check x and y pixel size (both 'real' and 'sample')
    with pytest.raises(TypeError):
        nx_detector.x_pixel_size = "test"
    nx_detector.x_pixel_size = 1e-7 * _meter

    with pytest.raises(TypeError):
        nx_detector.y_pixel_size = {}
    nx_detector.y_pixel_size = 2e-7 * _meter

    # check detector distance
    with pytest.raises(TypeError):
        nx_detector.distance = "test"
    nx_detector.distance = 0.02 * _meter

    # check field of view
    with pytest.raises(ValueError):
        nx_detector.field_of_view = "test"
    nx_detector.field_of_view = FieldOfView.HALF

    # check count time
    with pytest.raises(TypeError):
        nx_detector.count_time = 12
    with pytest.raises(TypeError):
        nx_detector.count_time = 12 * _volt
    nx_detector.count_time = [0.1] * 5 * _second

    # check x, y rotation axis positions
    with pytest.raises(TypeError):
        nx_detector.x_rotation_axis_pixel_position = "toto"
    nx_detector.x_rotation_axis_pixel_position = 12.3
    with pytest.raises(TypeError):
        nx_detector.y_rotation_axis_pixel_position = "toto"
    nx_detector.y_rotation_axis_pixel_position = 2.3

    # check sequence number
    with pytest.raises(TypeError):
        nx_detector.sequence_number = "test"
    with pytest.raises(TypeError):
        nx_detector.sequence_number = numpy.linspace(0, 9, 9).reshape(3, 3)
    nx_detector.sequence_number = numpy.linspace(0, 9, 9, dtype=numpy.uint32)

    assert isinstance(nx_detector.to_nx_dict(), dict)

    # check we can't set undefined attributes
    with pytest.raises(AttributeError):
        nx_detector.test = 12

    # test nx_detector concatenation
    concatenated_nx_detector = NXdetector.concatenate([nx_detector, nx_detector])
    numpy.testing.assert_array_equal(
        concatenated_nx_detector.image_key_control, [ImageKey.PROJECTION] * 10
    )
    assert concatenated_nx_detector.x_pixel_size.magnitude == 1e-7
    assert concatenated_nx_detector.y_pixel_size.magnitude == 2e-7
    assert concatenated_nx_detector.distance.magnitude == 0.02
    assert nx_detector.x_rotation_axis_pixel_position == 12.3
    assert nx_detector.y_rotation_axis_pixel_position == 2.3

    nx_detector.field_of_view = FieldOfView.HALF
    nx_detector.count_time = [0.1] * 10 * _second

    nx_detector.roi = None
    nx_detector.roi = (0, 0, 2052, 1024)
    with pytest.raises(TypeError):
        nx_detector.roi = "toto"
    with pytest.raises(ValueError):
        nx_detector.roi = (12,)


def test_nx_detector_with_unit():
    diode = NXdetectorWithUnit(
        node_name="diode",
        expected_dim=(1,),
        default_unit=_volt,
    )

    with pytest.raises(ValueError):
        diode.data = numpy.arange(10 * 10).reshape([10, 10])

    with pytest.raises(TypeError):
        diode.data = [10, 12]

    with pytest.raises(TypeError):
        diode.data = "test"

    diode.data = None
    diode.data = numpy.random.random(12) * _volt
    diode.data = pint.Quantity(numpy.random.random(12), _volt)

    diode.data = (DataUrl(),)
    concatenated_nx_detector = NXdetectorWithUnit.concatenate(
        [diode, diode],
        expected_dim=(1,),
        default_unit=_volt,
    )
    if isinstance(concatenated_nx_detector.data, tuple):
        assert all(isinstance(item, DataUrl) for item in concatenated_nx_detector.data)
        assert len(concatenated_nx_detector.data) == 2
    else:
        assert isinstance(concatenated_nx_detector.data, pint.Quantity)
        assert concatenated_nx_detector.data.units == _volt
        assert (
            concatenated_nx_detector.data.magnitude.shape[0]
            == 2 * diode.data.magnitude.shape[0]
        )


def test_nx_detector_with_virtual_source():
    """Ensure detector data can be written from virtual sources."""
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp_folder:
        # create virtual dataset
        n_base_raw_dataset = 5
        n_z, n_y, n_x = 4, 100, 100
        base_raw_dataset_shape = (n_z, n_y, n_x)
        n_base_raw_dataset_elmts = n_z * n_y * n_x

        v_sources = []

        raw_files = [
            os.path.join(tmp_folder, f"raw_file_{i_file}.hdf5")
            for i_file in range(n_base_raw_dataset)
        ]
        for i_raw_file, raw_file in enumerate(raw_files):
            with h5py.File(raw_file, mode="w") as h5f:
                h5f["data"] = numpy.arange(
                    start=n_base_raw_dataset_elmts * i_raw_file,
                    stop=n_base_raw_dataset_elmts * (i_raw_file + 1),
                ).reshape(base_raw_dataset_shape)
                v_sources.append(h5py.VirtualSource(h5f["data"]))

        nx_detector = NXdetector()
        nx_detector.data = v_sources

        detector_file = os.path.join(tmp_folder, "detector_file.hdf5")
        nx_detector.save(file_path=detector_file)

        # check the virtual dataset has been properly created and linked
        with h5py.File(detector_file, mode="r") as h5f_master:
            dataset = h5f_master["/detector/data"]
            assert dataset.is_virtual
            for i_raw_file, raw_file in enumerate(raw_files):
                with h5py.File(raw_file, mode="r") as h5f_raw:
                    numpy.testing.assert_array_equal(
                        dataset[i_raw_file * n_z : (i_raw_file + 1) * n_z],
                        h5f_raw["data"],
                    )
            # check attributes have been rewrite as expected
            assert "interpretation" in dataset.attrs

            # check virtual dataset is composed of relative links
            for vs_info in dataset.virtual_sources():
                assert vs_info.file_name.startswith(".")
        assert cwd == os.getcwd()

    # check concatenation
    concatenated_nx_detector = NXdetector.concatenate([nx_detector, nx_detector])
    assert isinstance(concatenated_nx_detector.data[1], h5py.VirtualSource)
    assert len(concatenated_nx_detector.data) == len(raw_files) * 2


def test_nx_detector_with_local_urls():
    """Ensure detector data can be written from DataUrl objects linking to local datasets (in the same file)."""

    cwd = os.getcwd()
    n_base_dataset = 3
    n_z, n_y, n_x = 2, 10, 20
    base_dataset_shape = (n_z, n_y, n_x)
    n_base_dataset_elmts = n_z * n_y * n_x
    urls = []

    with tempfile.TemporaryDirectory() as tmp_folder:
        master_file = os.path.join(tmp_folder, "master_file.hdf5")
        with h5py.File(master_file, mode="a") as h5f:
            for i in range(n_base_dataset):
                data_path = f"/data_{i}"
                h5f[data_path] = numpy.arange(
                    start=n_base_dataset_elmts * i,
                    stop=n_base_dataset_elmts * (i + 1),
                ).reshape(base_dataset_shape)
                urls.append(
                    DataUrl(
                        file_path=master_file,
                        data_path=data_path,
                        scheme="silx",
                    )
                )
        nx_detector = NXdetector()
        nx_detector.data = urls
        nx_detector.save(file_path=master_file)

        # check the virtual dataset has been properly createde and linked
        with h5py.File(master_file, mode="r") as h5f_master:
            dataset = h5f_master["/detector/data"]
            assert dataset.is_virtual
            for i in range(n_base_dataset):
                numpy.testing.assert_array_equal(
                    dataset[i * n_z : (i + 1) * n_z],
                    numpy.arange(
                        start=n_base_dataset_elmts * i,
                        stop=n_base_dataset_elmts * (i + 1),
                    ).reshape(base_dataset_shape),
                )
            # check virtual dataset is composed of relative links
            for vs_info in dataset.virtual_sources():
                assert vs_info.file_name.startswith(".")
        assert cwd == os.getcwd()

    # check concatenation
    concatenated_nx_detector = NXdetector.concatenate([nx_detector, nx_detector])
    assert isinstance(concatenated_nx_detector.data[1], DataUrl)
    assert len(concatenated_nx_detector.data) == n_base_dataset * 2


def test_nx_detector_with_external_urls():
    """Ensure detector data can be written from DataUrl objects linking to external datasets."""
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp_folder:
        # create virtual dataset
        n_base_raw_dataset = 5
        n_z, n_y, n_x = 4, 100, 100
        base_raw_dataset_shape = (n_z, n_y, n_x)
        n_base_raw_dataset_elmts = n_z * n_y * n_x

        urls = []

        raw_files = [
            os.path.join(tmp_folder, f"raw_file_{i_file}.hdf5")
            for i_file in range(n_base_raw_dataset)
        ]
        for i_raw_file, raw_file in enumerate(raw_files):
            with h5py.File(raw_file, mode="w") as h5f:
                h5f["data"] = numpy.arange(
                    start=n_base_raw_dataset_elmts * i_raw_file,
                    stop=n_base_raw_dataset_elmts * (i_raw_file + 1),
                ).reshape(base_raw_dataset_shape)
                # provide one file path each two as an absolue path
                if i_raw_file % 2 == 0:
                    file_path = os.path.abspath(raw_file)
                else:
                    file_path = os.path.relpath(raw_file, tmp_folder)
                urls.append(
                    DataUrl(
                        file_path=file_path,
                        data_path="data",
                        scheme="silx",
                    )
                )

        nx_detector = NXdetector()
        nx_detector.data = urls

        detector_file = os.path.join(tmp_folder, "detector_file.hdf5")
        # needed as we provide some link with relative path
        with cwd_context(tmp_folder):
            nx_detector.save(file_path=detector_file)

        # check the virtual dataset has been properly createde and linked
        with h5py.File(detector_file, mode="r") as h5f_master:
            dataset = h5f_master["/detector/data"]
            assert dataset.is_virtual
            for i_raw_file, raw_file in enumerate(raw_files):
                with h5py.File(raw_file, mode="r") as h5f_raw:
                    numpy.testing.assert_array_equal(
                        dataset[i_raw_file * n_z : (i_raw_file + 1) * n_z],
                        h5f_raw["data"],
                    )
            # check virtual dataset is composed of relative links
            for vs_info in dataset.virtual_sources():
                assert vs_info.file_name.startswith(".")

        assert cwd == os.getcwd()
        # check concatenation
        concatenated_nx_detector = NXdetector.concatenate([nx_detector, nx_detector])
        assert isinstance(concatenated_nx_detector.data[1], DataUrl)
        assert len(concatenated_nx_detector.data) == n_base_raw_dataset * 2


@pytest.mark.parametrize(
    "load_data_as, expected_type",
    [
        ("as_numpy_array", numpy.ndarray),
        ("as_virtual_source", h5py.VirtualSource),
        ("as_data_url", DataUrl),
    ],
)
def test_load_detector_data(tmp_path, load_data_as, expected_type):
    layout = h5py.VirtualLayout(shape=(4 * 2, 100, 100), dtype="i4")

    for n in range(0, 4):
        filename = os.path.join(tmp_path, "{n}.h5")
        with h5py.File(filename, "w") as f:
            f["data"] = numpy.arange(100 * 100 * 2).reshape(2, 100, 100)

        vsource = h5py.VirtualSource(filename, "data", shape=(2, 100, 100))
        start_n = n * 2
        end_n = start_n + 2
        layout[start_n:end_n] = vsource

    output_file = os.path.join(tmp_path, "VDS.h5")
    with h5py.File(output_file, "w") as f:
        f.create_virtual_dataset("data", layout, fillvalue=-5)

    nx_detector = NXdetector()
    nx_detector._load(
        file_path=output_file,
        data_path="/",
        load_data_as=load_data_as,
        nexus_version=None,
    )

    if expected_type is numpy.ndarray:
        assert isinstance(nx_detector.data, expected_type)
    else:
        for elmt in nx_detector.data:
            assert isinstance(elmt, expected_type)
    nx_detector.save(os.path.join(tmp_path, "output_file.nx"))


def test_nxtransformations_with_nxdetector(tmp_path):
    """
    Test the behaviour of NXtransformations with an NXtomo and ensure coherence between the
    ``lr_flip``/``ud_flip`` convenience API and providing transformations directly.
    """

    def build_detector():
        nx_detector = NXdetector(expected_dim=(2, 3))
        nx_detector.data = numpy.random.random(100 * 100 * 5).reshape(5, 100, 100)
        nx_detector.image_key_control = [1] * 5
        nx_detector.image_key_control = [ImageKey.PROJECTION] * 5
        return nx_detector

    nx_detector_1 = build_detector()
    nx_detector_2 = build_detector()

    # test having a left-right flip
    nx_detector_1.transformations.add_transformation(
        Transformation(
            axis_name="ry",
            value=180 * _degree,
            transformation_type="rotation",
            vector=TransformationAxis.AXIS_Y,
        )
    )
    nx_detector_2.set_transformation_from_x_flipped(True)

    assert (
        nx_detector_1.transformations.to_nx_dict()
        == nx_detector_2.transformations.to_nx_dict()
    )

    # test having a up-down flip
    nx_detector_3 = build_detector()
    nx_detector_4 = build_detector()
    nx_detector_3.transformations.add_transformation(
        Transformation(
            axis_name="rx",
            value=180 * _degree,
            transformation_type="rotation",
            vector=TransformationAxis.AXIS_X,
        )
    )
    nx_detector_4.set_transformation_from_y_flipped(True)

    assert (
        nx_detector_3.transformations.to_nx_dict()
        == nx_detector_4.transformations.to_nx_dict()
    )

    # having both lr and ud
    nx_detector_5 = build_detector()
    nx_detector_6 = build_detector()

    nx_detector_5.transformations.add_transformation(
        Transformation(
            axis_name="rx",
            value=180 * _degree,
            transformation_type="rotation",
            vector=TransformationAxis.AXIS_X,
        )
    )
    nx_detector_5.transformations.add_transformation(
        Transformation(
            axis_name="ry",
            value=180 * _degree,
            transformation_type="rotation",
            vector=TransformationAxis.AXIS_Y,
        )
    )
    nx_detector_6.set_transformation_from_x_flipped(True)
    nx_detector_6.set_transformation_from_y_flipped(True)

    assert (
        nx_detector_5.transformations.to_nx_dict()
        == nx_detector_6.transformations.to_nx_dict()
    )


def test_several_nxtransformations(tmp_path):
    """Try loading multiple NXtransformations."""
    file_path = str(tmp_path / "test_transformations.nx")
    nx_detector = NXdetector(expected_dim=(2, 3))
    nx_detector.data = numpy.random.random(100 * 100 * 5).reshape(5, 100, 100)
    nx_detector.image_key_control = [1] * 5
    nx_detector.image_key_control = [ImageKey.PROJECTION] * 5
    nx_detector.transformations.add_transformation(DetYFlipTransformation(flip=True))

    nx_detector.save(file_path=file_path, data_path="detector", nexus_path_version=1.3)

    # test 1: one detector with one NXtransformations stored at the default location
    load_det = NXdetector()
    load_det._load(
        file_path=file_path,
        data_path="detector",
        load_data_as="as_numpy_array",
        nexus_version=1.3,
    )
    assert (
        len(load_det.transformations.transformations) == 2
    )  # the DetYFlipTransformation + gravity

    # test2: two transformations - one stored at the default location
    with h5py.File(file_path, mode="a") as h5f:
        assert "detector/transformations" in h5f
        h5f["detector"].copy(source="transformations", dest="new_transformations")

    load_det = NXdetector()
    load_det._load(
        file_path=file_path,
        data_path="detector",
        load_data_as="as_numpy_array",
        nexus_version=1.3,
    )
    assert (
        len(load_det.transformations.transformations) == 2
    )  # the DetYFlipTransformation + gravity

    # test3: two transformations - none at the default location
    with h5py.File(file_path, mode="a") as h5f:
        assert "detector/transformations" in h5f
        h5f["detector"].move(source="transformations", dest="new_new_transformations")

    load_det = NXdetector()
    with pytest.raises(ValueError):
        load_det._load(
            file_path=file_path,
            data_path="detector",
            load_data_as="as_numpy_array",
            nexus_version=1.3,
        )

    # test4: one transformation - not stored at the default location
    with h5py.File(file_path, mode="a") as h5f:
        del h5f["detector/new_new_transformations"]

    load_det = NXdetector()
    load_det._load(
        file_path=file_path,
        data_path="detector",
        load_data_as="as_numpy_array",
        nexus_version=1.3,
    )
    assert (
        len(load_det.transformations.transformations) == 2
    )  # the DetYFlipTransformation + gravity


def test_detector_flips(tmp_path):
    """Ensure the deprecated `x_flip` and `y_flip` APIs still work."""
    # build some default detector
    nx_detector = NXdetector(expected_dim=(2, 3))
    nx_detector.data = numpy.random.random(100 * 100 * 5).reshape(5, 100, 100)
    nx_detector.image_key_control = [1] * 5
    nx_detector.image_key_control = [ImageKey.PROJECTION] * 5

    nx_detector.set_transformation_from_y_flipped(True)
    assert (
        DetYFlipTransformation(flip=True)
        not in nx_detector.transformations.transformations
    )
    assert (
        DetXFlipTransformation(flip=True) in nx_detector.transformations.transformations
    )
    nx_detector.set_transformation_from_x_flipped(True)
    assert (
        DetYFlipTransformation(flip=True) in nx_detector.transformations.transformations
    )
    nx_detector.set_transformation_from_x_flipped(False)
    assert (
        DetYFlipTransformation(flip=True)
        not in nx_detector.transformations.transformations
    )

    file_path = os.path.join(tmp_path, "test_nx_detectors")
    nx_detector.save(file_path=file_path, data_path="detector")

    loaded_nx_detector = NXdetector()
    loaded_nx_detector._load(
        file_path=file_path,
        data_path="detector",
        load_data_as="as_numpy_array",
        nexus_version=1.3,
    )
    assert len(loaded_nx_detector.transformations) == 3
    assert (
        DetYFlipTransformation(flip=True)
        not in loaded_nx_detector.transformations.transformations
    )

    assert (
        DetXFlipTransformation(flip=True)
        in loaded_nx_detector.transformations.transformations
    )
