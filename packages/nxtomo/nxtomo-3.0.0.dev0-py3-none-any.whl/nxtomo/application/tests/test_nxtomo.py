import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime

import h5py
import numpy
import pint
import pytest
from silx.io.url import DataUrl
from silx.io.utils import h5py_read_dataset

from nxtomo.application.nxtomo import NXtomo, copy_nxtomo_file
from nxtomo.geometry._CoordinateSystem import CoordinateSystem
from nxtomo.io import HDF5File
from nxtomo.nxobject.nxdetector import FieldOfView, ImageKey
from nxtomo.nxobject.utils.concatenate import concatenate

try:
    import tifffile
except ImportError:
    has_tifffile = False
else:
    from nxtomo.utils.utils import create_detector_dataset_from_tiff

    has_tifffile = True


nexus_path_versions = (1.5, 1.4, 1.3, 1.2, 1.1, 1.0, None)
ureg = pint.get_application_registry()
second = ureg.second
degree = ureg.degree
meter = ureg.meter


@pytest.mark.parametrize("nexus_path_version", nexus_path_versions)
def test_nx_tomo(nexus_path_version, tmp_path):
    nx_tomo = NXtomo()

    # check start time
    with pytest.raises(TypeError):
        nx_tomo.start_time = 12
    nx_tomo.start_time = datetime.now()

    # check end time
    with pytest.raises(TypeError):
        nx_tomo.end_time = 12
    nx_tomo.end_time = datetime(2022, 2, 27)

    # check sample
    with pytest.raises(TypeError):
        nx_tomo.sample = "tata"

    # check detector
    with pytest.raises(TypeError):
        nx_tomo.instrument.detector = "tata"

    # check energy
    with pytest.raises(TypeError):
        nx_tomo.energy = "tata"
    nx_tomo.energy = 12.3 * ureg.keV

    # check group size
    with pytest.raises(TypeError):
        nx_tomo.group_size = "tata"
    nx_tomo.group_size = 3

    # check title
    with pytest.raises(TypeError):
        nx_tomo.title = 12
    nx_tomo.title = "title"

    # check instrument
    with pytest.raises(TypeError):
        nx_tomo.instrument = "test"

    # check we can't set undefined attributes
    with pytest.raises(AttributeError):
        nx_tomo.test = 12

    # create detector for test
    projections = numpy.random.random(100 * 100 * 8).reshape([8, 100, 100])
    flats_1 = numpy.random.random(100 * 100 * 2).reshape([2, 100, 100])
    darks = numpy.random.random(100 * 100 * 3).reshape([3, 100, 100])
    flats_2 = numpy.random.random(100 * 100 * 2).reshape([2, 100, 100])
    alignment = numpy.random.random(100 * 100 * 1).reshape([1, 100, 100])

    n_frames = 3 + 2 + 8 + 2 + 1

    nx_tomo.instrument.detector.data = numpy.concatenate(
        [
            darks,
            flats_1,
            projections,
            flats_2,
            alignment,
        ]
    )

    nx_tomo.instrument.detector.image_key_control = numpy.concatenate(
        [
            [ImageKey.DARK_FIELD] * 3,
            [ImageKey.FLAT_FIELD] * 2,
            [ImageKey.PROJECTION] * 8,
            [ImageKey.FLAT_FIELD] * 2,
            [ImageKey.ALIGNMENT] * 1,
        ]
    )
    nx_tomo.instrument.detector.sequence_number = numpy.linspace(
        0, n_frames, n_frames, dtype=numpy.uint32
    )

    nx_tomo.instrument.detector.x_pixel_size = (
        nx_tomo.instrument.detector.y_pixel_size
    ) = (1e-7 * meter)
    nx_tomo.instrument.detector.distance = 0.2 * meter
    nx_tomo.instrument.detector.field_of_view = FieldOfView.HALF
    nx_tomo.instrument.detector.count_time = (
        numpy.concatenate(
            [
                [0.2] * 3,  # darks
                [0.1] * 2,  # flats 1
                [0.1] * 8,  # projections
                [0.1] * 2,  # flats 2
                [0.1] * 1,  # alignment
            ]
        )
        * second
    )

    # create sample for test
    nx_tomo.sample.name = "my sample"
    nx_tomo.sample.rotation_angle = (
        numpy.concatenate(
            [
                [0.0] * 3,  # darks
                [0.0] * 2,  # flats 1
                numpy.linspace(0, 180, num=8, endpoint=False),  # projections
                [180.0] * 2,  # flats 2
                [0.0],  # alignment
            ]
        )
        * degree
    )

    if nexus_path_version is None or nexus_path_version >= 1.4:
        # create source and detector for test
        nx_tomo.instrument.source.distance = 3.6 * meter
        nx_tomo.instrument.detector.y_rotation_axis_pixel_position = 1.1
    nx_tomo.instrument.detector.x_rotation_axis_pixel_position = 1.2

    nx_tomo.sample.x_translation = [0.6] * n_frames * meter
    nx_tomo.sample.y_translation = [0.2] * n_frames * meter
    nx_tomo.sample.z_translation = [0.1] * n_frames * meter
    nx_tomo.sample.x_pixel_size = 90.8 * ureg.nanometer
    nx_tomo.sample.y_pixel_size = 8.2 * ureg.micrometer

    assert nx_tomo.is_root is True
    assert nx_tomo.instrument.is_root is False
    assert (
        nx_tomo.root_path
        == nx_tomo.instrument.root_path
        == nx_tomo.instrument.detector.root_path
    )

    NXtomo.check_consistency(nx_tomo=nx_tomo, raises_error=True)

    folder = tmp_path / "test_folder"
    folder.mkdir()

    file_path = os.path.join(folder, "nexus_file.hdf5")

    nx_tomo.save(
        file_path=file_path,
        data_path="entry",
        nexus_path_version=nexus_path_version,
    )
    assert os.path.exists(file_path)

    # insure we can read it back
    scan = NXtomo().load(file_path, data_path="entry")
    assert (
        len(
            tuple(
                filter(
                    lambda image_key: image_key is ImageKey.FLAT_FIELD,
                    scan.instrument.detector.image_key_control,
                )
            )
        )
        == 4
    )
    assert (
        len(
            tuple(
                filter(
                    lambda image_key: image_key is ImageKey.DARK_FIELD,
                    scan.instrument.detector.image_key_control,
                )
            )
        )
        == 3
    )
    assert (
        len(
            tuple(
                filter(
                    lambda image_key: image_key is ImageKey.PROJECTION,
                    scan.instrument.detector.image_key_control,
                )
            )
        )
        == 8
    )
    assert (
        len(
            tuple(
                filter(
                    lambda image_key: image_key is ImageKey.ALIGNMENT,
                    scan.instrument.detector.image_key_control,
                )
            )
        )
        == 1
    )
    if nexus_path_version is None or nexus_path_version >= 1.5:
        numpy.testing.assert_array_equal(
            scan.instrument.detector.sequence_number,
            numpy.linspace(0, n_frames, n_frames, dtype=numpy.uint32),
        )
    assert scan.energy.magnitude == 12.3
    assert scan.instrument.detector.x_pixel_size.magnitude == 1e-7
    assert scan.instrument.detector.y_pixel_size.magnitude == 1e-7
    assert scan.instrument.detector.distance.magnitude == 0.2
    assert scan.instrument.detector.field_of_view == FieldOfView.HALF
    assert scan.sample.name == "my sample"
    assert (
        len(scan.sample.x_translation.magnitude)
        == len(scan.sample.y_translation.magnitude)
        == len(scan.sample.z_translation.magnitude)
        == n_frames
    )
    assert scan.sample.x_translation.magnitude[0] == 0.6
    assert scan.sample.y_translation.magnitude[0] == 0.2
    assert scan.sample.z_translation.magnitude[0] == 0.1
    if nexus_path_version != 1.0:
        assert scan.instrument.source.name is not None
        assert scan.instrument.source.type is not None
    if nexus_path_version is None or nexus_path_version >= 1.4:
        assert nx_tomo.instrument.source.distance.to_base_units().magnitude == 3.6
        assert nx_tomo.instrument.detector.y_rotation_axis_pixel_position == 1.1
    assert nx_tomo.instrument.detector.x_rotation_axis_pixel_position == 1.2

    # try to load it from the disk
    loaded_nx_tomo = NXtomo().load(file_path=file_path, data_path="entry")
    assert isinstance(loaded_nx_tomo, NXtomo)
    assert loaded_nx_tomo.energy.magnitude == nx_tomo.energy.magnitude
    assert str(loaded_nx_tomo.energy.units) == str(nx_tomo.energy.units)
    assert loaded_nx_tomo.start_time == nx_tomo.start_time
    assert loaded_nx_tomo.end_time == nx_tomo.end_time
    if nexus_path_version is None or nexus_path_version >= 1.4:
        assert (
            loaded_nx_tomo.instrument.source.distance.to_base_units().magnitude
            == nx_tomo.instrument.source.distance.to_base_units().magnitude
        )
        assert (
            loaded_nx_tomo.instrument.detector.y_rotation_axis_pixel_position
            == nx_tomo.instrument.detector.y_rotation_axis_pixel_position
        )
    assert (
        loaded_nx_tomo.instrument.detector.x_rotation_axis_pixel_position
        == nx_tomo.instrument.detector.x_rotation_axis_pixel_position
    )
    numpy.testing.assert_equal(
        loaded_nx_tomo.instrument.detector.x_pixel_size.to_base_units().magnitude,
        nx_tomo.instrument.detector.x_pixel_size.to_base_units().magnitude,
    )
    assert str(loaded_nx_tomo.instrument.detector.x_pixel_size.units) == str(
        nx_tomo.instrument.detector.x_pixel_size.units
    )
    numpy.testing.assert_equal(
        loaded_nx_tomo.instrument.detector.y_pixel_size.to_base_units().magnitude,
        nx_tomo.instrument.detector.y_pixel_size.to_base_units().magnitude,
    )
    assert str(loaded_nx_tomo.instrument.detector.y_pixel_size.units) == str(
        nx_tomo.instrument.detector.y_pixel_size.units
    )
    assert (
        loaded_nx_tomo.instrument.detector.field_of_view
        == nx_tomo.instrument.detector.field_of_view
    )
    numpy.testing.assert_equal(
        loaded_nx_tomo.instrument.detector.count_time.to_base_units().magnitude,
        nx_tomo.instrument.detector.count_time.to_base_units().magnitude,
    )
    assert str(loaded_nx_tomo.instrument.detector.count_time.units) == str(
        nx_tomo.instrument.detector.count_time.units
    )
    assert (
        loaded_nx_tomo.instrument.detector.distance
        == nx_tomo.instrument.detector.distance
    )

    numpy.testing.assert_array_equal(
        loaded_nx_tomo.instrument.detector.image_key_control,
        nx_tomo.instrument.detector.image_key_control,
    )
    numpy.testing.assert_array_equal(
        loaded_nx_tomo.instrument.detector.image_key,
        nx_tomo.instrument.detector.image_key,
    )
    if nexus_path_version is None or nexus_path_version >= 1.5:
        numpy.testing.assert_array_equal(
            loaded_nx_tomo.instrument.detector.sequence_number,
            nx_tomo.instrument.detector.sequence_number,
        )
    else:
        assert loaded_nx_tomo.instrument.detector.sequence_number is None
    assert loaded_nx_tomo.sample.name == nx_tomo.sample.name
    assert loaded_nx_tomo.sample.rotation_angle is not None
    numpy.testing.assert_array_almost_equal(
        loaded_nx_tomo.sample.rotation_angle, nx_tomo.sample.rotation_angle
    )
    numpy.testing.assert_array_almost_equal(
        loaded_nx_tomo.sample.x_translation,
        nx_tomo.sample.x_translation,
    )
    numpy.testing.assert_array_almost_equal(
        loaded_nx_tomo.sample.y_translation,
        nx_tomo.sample.y_translation,
    )
    numpy.testing.assert_array_almost_equal(
        loaded_nx_tomo.sample.z_translation,
        nx_tomo.sample.z_translation,
    )
    if nexus_path_version is None or nexus_path_version >= 1.5:
        assert loaded_nx_tomo.sample.x_pixel_size == 90.8 * ureg.nanometer
        assert loaded_nx_tomo.sample.y_pixel_size == 8.2 * ureg.micrometer
    else:
        assert loaded_nx_tomo.sample.x_pixel_size is None
        assert loaded_nx_tomo.sample.y_pixel_size is None

    loaded_nx_tomo = NXtomo().load(
        file_path=file_path, data_path="entry", detector_data_as="as_numpy_array"
    )
    numpy.testing.assert_array_almost_equal(
        loaded_nx_tomo.instrument.detector.data,
        nx_tomo.instrument.detector.data,
    )
    loaded_nx_tomo = NXtomo().load(
        file_path=file_path, data_path="entry", detector_data_as="as_data_url"
    )
    assert isinstance(loaded_nx_tomo.instrument.detector.data[0], DataUrl)
    with pytest.raises(ValueError):
        # check an error is raise because the dataset is not virtual
        loaded_nx_tomo = NXtomo().load(
            file_path=file_path,
            data_path="entry",
            detector_data_as="as_virtual_source",
        )
    assert loaded_nx_tomo._coordinate_system == CoordinateSystem.McStas

    # test concatenation
    nx_tomo_concat = concatenate([loaded_nx_tomo, None, loaded_nx_tomo])
    concat_file = os.path.join(folder, "concatenated_nexus_file.hdf5")

    nx_tomo_concat.save(
        file_path=concat_file,
        data_path="myentry",
        nexus_path_version=nexus_path_version,
    )
    loaded_concatenated_nx_tomo = NXtomo().load(
        file_path=concat_file,
        data_path="myentry",
        detector_data_as="as_virtual_source",
    )
    numpy.testing.assert_array_almost_equal(
        loaded_concatenated_nx_tomo.sample.rotation_angle,
        numpy.concatenate(
            [
                nx_tomo.sample.rotation_angle,
                nx_tomo.sample.rotation_angle,
            ]
        ),
    )
    numpy.testing.assert_array_almost_equal(
        loaded_concatenated_nx_tomo.sample.x_translation,
        numpy.concatenate(
            [
                nx_tomo.sample.x_translation,
                nx_tomo.sample.x_translation,
            ]
        ),
    )

    with pytest.raises(TypeError):
        concatenate([1, 2])

    with h5py.File(concat_file, mode="r") as h5f:
        h5py_read_dataset(h5f["myentry/definition"]) == "NXtomo"

    if nexus_path_version is None or nexus_path_version >= 1.4:
        assert (
            loaded_concatenated_nx_tomo.instrument.source.distance.to_base_units().magnitude
            == loaded_nx_tomo.instrument.source.distance.to_base_units().magnitude
        )
        assert (
            loaded_concatenated_nx_tomo.instrument.detector.x_rotation_axis_pixel_position
            == loaded_nx_tomo.instrument.detector.x_rotation_axis_pixel_position
        )
        assert (
            loaded_concatenated_nx_tomo.instrument.detector.y_rotation_axis_pixel_position
            == loaded_nx_tomo.instrument.detector.y_rotation_axis_pixel_position
        )


@pytest.mark.parametrize("nexus_path_version", nexus_path_versions)
def test_nx_tomo_subselection(nexus_path_version):
    """
    test sub_select_from_projection_angle_range
    """
    nx_tomo = NXtomo()
    nx_tomo.energy = 12.3 * ureg.keV
    shape = (12, 12)
    data_dark = numpy.ones(shape)
    data_flat = numpy.ones(shape) * 2.0
    data_projection = numpy.ones(shape) * 3.0
    str(nx_tomo)
    nx_tomo.instrument.detector.data = numpy.concatenate(
        (
            data_dark,
            data_dark,
            data_flat,
            data_projection,
            data_projection,
            data_projection,
            data_flat,
            data_projection,
            data_projection,
            data_projection,
            data_flat,
        )
    )
    nx_tomo.instrument.detector.image_key_control = numpy.array(
        (
            ImageKey.DARK_FIELD,
            ImageKey.DARK_FIELD,
            ImageKey.FLAT_FIELD,
            ImageKey.PROJECTION,
            ImageKey.PROJECTION,
            ImageKey.PROJECTION,
            ImageKey.FLAT_FIELD,
            ImageKey.PROJECTION,
            ImageKey.PROJECTION,
            ImageKey.PROJECTION,
            ImageKey.FLAT_FIELD,
        )
    )
    nx_tomo.instrument.detector.sequence_number = numpy.linspace(
        0, 11, 11, dtype=numpy.uint32
    )

    original_angles = numpy.array(
        (
            0,
            0,
            0,
            10,
            20.5,
            22.5,
            180,
            180,
            200,
            300.2,
            300.2,
        )
    )
    nx_tomo.sample.rotation_angle = original_angles * degree

    nx_tomo_sub_1 = NXtomo.sub_select_from_angle_offset(
        nx_tomo=nx_tomo,
        start_angle_offset=10,
        angle_interval=12.5,
        shift_angles=False,
    )

    numpy.testing.assert_equal(
        nx_tomo_sub_1.instrument.detector.image_key_control,
        numpy.array(
            (
                ImageKey.DARK_FIELD,
                ImageKey.DARK_FIELD,
                ImageKey.FLAT_FIELD,
                ImageKey.INVALID,
                ImageKey.PROJECTION,
                ImageKey.PROJECTION,
                ImageKey.FLAT_FIELD,
                ImageKey.INVALID,
                ImageKey.INVALID,
                ImageKey.INVALID,
                ImageKey.FLAT_FIELD,
            )
        ),
    )
    numpy.testing.assert_equal(
        nx_tomo_sub_1.sample.rotation_angle.magnitude,
        original_angles,
    )

    nx_tomo_sub_2 = NXtomo.sub_select_from_angle_offset(
        nx_tomo=nx_tomo,
        start_angle_offset=10,
        angle_interval=20,
        shift_angles=True,
    )

    numpy.testing.assert_equal(
        nx_tomo_sub_2.sample.rotation_angle.magnitude[0:3],
        0.0,
    )
    numpy.testing.assert_array_equal(
        nx_tomo_sub_2.sample.rotation_angle.magnitude[3:6],
        numpy.array([0.0, 10.5, 12.5]),
    )

    nx_tomo_sub_3 = NXtomo.sub_select_from_angle_offset(
        nx_tomo=nx_tomo,
        start_angle_offset=-10,
        angle_interval=300,
        shift_angles=False,
    )

    numpy.testing.assert_equal(
        nx_tomo_sub_3.instrument.detector.image_key_control,
        numpy.array(
            (
                ImageKey.DARK_FIELD,
                ImageKey.DARK_FIELD,
                ImageKey.FLAT_FIELD,
                ImageKey.PROJECTION,
                ImageKey.PROJECTION,
                ImageKey.PROJECTION,
                ImageKey.FLAT_FIELD,
                ImageKey.PROJECTION,
                ImageKey.PROJECTION,
                ImageKey.INVALID,
                ImageKey.FLAT_FIELD,
            )
        ),
    )

    nx_tomo_sub_4 = NXtomo.sub_select_from_angle_offset(
        nx_tomo=nx_tomo,
        start_angle_offset=-10,
        angle_interval=None,
        shift_angles=False,
    )
    numpy.testing.assert_equal(
        nx_tomo_sub_4.instrument.detector.image_key_control,
        numpy.array(
            (
                ImageKey.DARK_FIELD,
                ImageKey.DARK_FIELD,
                ImageKey.FLAT_FIELD,
                ImageKey.PROJECTION,
                ImageKey.PROJECTION,
                ImageKey.PROJECTION,
                ImageKey.FLAT_FIELD,
                ImageKey.PROJECTION,
                ImageKey.PROJECTION,
                ImageKey.PROJECTION,
                ImageKey.FLAT_FIELD,
            )
        ),
    )
    numpy.testing.assert_equal(
        nx_tomo_sub_4.instrument.detector.sequence_number,
        numpy.linspace(0, 11, 11, dtype=numpy.uint32),
    )


def test_bliss_original_files(tmp_path):
    """
    test about NXtomo.bliss_original_files
    """
    test_dir = tmp_path / "test_bliss_original_files"
    test_dir.mkdir()

    nx_tomo_1 = NXtomo()
    with pytest.raises(TypeError):
        nx_tomo_1.bliss_original_files = 12

    nx_tomo_1.bliss_original_files = ("/path/1", "/path/2")

    nx_tomo_2 = NXtomo()
    nx_tomo_2.bliss_original_files = ("/path/2", "/path/3")

    nx_tomo_3 = NXtomo()

    nx_tomo_4 = NXtomo()
    nx_tomo_4.bliss_original_files = ()

    nx_tomo_concat = concatenate([nx_tomo_1, nx_tomo_2, nx_tomo_3])
    assert nx_tomo_concat.bliss_original_files == ("/path/1", "/path/2", "/path/3")

    output_nx_tomo_concat = os.path.join(test_dir, "nx_concat.nx")
    nx_tomo_concat.save(output_nx_tomo_concat, "/entry_concat")

    loaded_nx_tomo = NXtomo().load(output_nx_tomo_concat, "/entry_concat")
    assert loaded_nx_tomo.bliss_original_files == ("/path/1", "/path/2", "/path/3")

    output_nx_tomo_file = os.path.join(test_dir, "nx_tomo.nx")
    nx_tomo_3.save(output_nx_tomo_file, "/entry0000")
    loaded_nx_tomo = NXtomo().load(output_nx_tomo_file, "/entry0000")
    assert loaded_nx_tomo.bliss_original_files is None

    nx_tomo_4.save(output_nx_tomo_file, "/entry0000", overwrite=True)
    loaded_nx_tomo = NXtomo().load(output_nx_tomo_file, "/entry0000")
    assert loaded_nx_tomo.bliss_original_files == ()


@pytest.mark.parametrize("vds_resolution", ("update", "remove"))
def test_copy_nxtomo_file(tmp_path, vds_resolution):
    """test 'copy_nxtomo_file' function"""
    input_folder = tmp_path / "input"
    input_folder.mkdir()
    input_nx_tomo_file = os.path.join(input_folder, "nexus.nx")

    output_folder = tmp_path / "output"
    output_folder.mkdir()

    nx_tomo = NXtomo()
    nx_tomo.save(input_nx_tomo_file, "/entry0000")

    output_file = os.path.join(output_folder, "nxtomo.nx")

    copy_nxtomo_file(
        input_nx_tomo_file,
        entries=None,
        output_file=output_file,
        vds_resolution=vds_resolution,
    )
    assert os.path.exists(output_file)


def test_multiple_readers(tmp_path):
    """Test that several readers can access the file in parallel with a thread pool or a process pool."""
    input_folder = tmp_path / "input"
    input_folder.mkdir()
    input_nx_tomo_file = os.path.join(input_folder, "nexus.nx")

    output_folder = tmp_path / "output"
    output_folder.mkdir()

    nx_tomo = NXtomo()
    detector_data = numpy.linspace(0, 100, 1000).reshape(10, 10, 10)
    nx_tomo.instrument.detector.data = detector_data
    nx_tomo.save(input_nx_tomo_file, "/entry0000")
    from time import sleep

    def read_data():
        with HDF5File(input_nx_tomo_file, mode="r") as h5f:
            # with h5py.File(input_nx_tomo_file, mode="r") as h5f:
            sleep(0.2)
            return h5f["/entry0000/instrument/detector/data"][()]

    futures = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        for _ in range(10):
            futures.append(executor.submit(read_data))
    for future in futures:
        numpy.testing.assert_array_equal(future.result(), detector_data)

    with ProcessPoolExecutor() as executor:
        results = executor.map(read_data)
        for result in results:
            numpy.testing.assert_array_equal(result, detector_data)


@pytest.mark.skipif(not has_tifffile, reason="tifffile not installed")
@pytest.mark.parametrize("dtype", (numpy.uint16, numpy.float32))
@pytest.mark.parametrize("provide_dtype", (True, False))
@pytest.mark.parametrize("relative_link", (True, False))
def test_nxtomo_from_tiff(tmp_path, dtype, provide_dtype, relative_link):
    """Test creation of an NXtomo from a set of .tiff files."""
    tifffile_folder = tmp_path / "tiffs"
    tifffile_folder.mkdir()

    tiff_files = []
    raw_data = numpy.linspace(
        start=0,
        stop=1000,
        num=1000,
        dtype=dtype,
    ).reshape(10, 10, 10)
    for i in range(10):
        tiff_file = os.path.join(tifffile_folder, f"my_file{i}.tif")
        tifffile.imwrite(tiff_file, raw_data[i])
        tiff_files.append(tiff_file)

    output_nxtomo = os.path.join(tmp_path, "my_nxtomo.nx")
    nxtomo = NXtomo()
    with h5py.File(output_nxtomo, mode="w") as h5f:

        external_dataset_group = h5f.require_group("external_datasets")
        nxtomo.instrument.detector.data = create_detector_dataset_from_tiff(
            tiff_files=tiff_files,
            external_dataset_group=external_dataset_group,
            dtype=dtype if provide_dtype else None,
            relative_link=relative_link,
        )
    nxtomo.save(
        file_path=output_nxtomo,
        data_path="entry0000",
    )

    loaded_nxtomo = NXtomo().load(
        output_nxtomo, "entry0000", detector_data_as="as_numpy_array"
    )
    numpy.testing.assert_array_equal(
        loaded_nxtomo.instrument.detector.data,
        raw_data,
    )
