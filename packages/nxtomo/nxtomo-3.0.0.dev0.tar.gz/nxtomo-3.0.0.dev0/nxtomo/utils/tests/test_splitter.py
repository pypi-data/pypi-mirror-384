import os
from tempfile import TemporaryDirectory

import h5py
import numpy
import pint
import pytest
from silx.io.url import DataUrl

from nxtomo.application.nxtomo import NXtomo
from nxtomo.utils.NXtomoSplitter import NXtomoSplitter

ureg = pint.get_application_registry()
degree = ureg.degree
meter = ureg.meter


def test_NXtomoSplitter_get_invalid_datasets():
    """Test the NXtomoSplitter `get_invalid_datasets` function."""
    nx_tomo = NXtomo()
    n_frames = 10
    nx_tomo.instrument.detector.data = numpy.random.random(100 * 100 * 10).reshape(
        [n_frames, 100, 100]
    )

    splitter = NXtomoSplitter(nx_tomo=nx_tomo)

    assert len(splitter.get_invalid_datasets()) == 0

    # test rotation angle
    nx_tomo.sample.rotation_angle = [12, 13] * degree
    assert len(splitter.get_invalid_datasets()) == 1
    nx_tomo.sample.rotation_angle = [0] * n_frames * degree
    assert len(splitter.get_invalid_datasets()) == 0

    # test image_key_control
    nx_tomo.instrument.detector.image_key_control = [0]
    assert len(splitter.get_invalid_datasets()) == 1
    nx_tomo.instrument.detector.image_key_control = [0] * n_frames
    assert len(splitter.get_invalid_datasets()) == 0

    # test x_translation
    nx_tomo.sample.x_translation = [0] * meter
    assert len(splitter.get_invalid_datasets()) == 1
    nx_tomo.sample.x_translation = [0] * n_frames * meter
    assert len(splitter.get_invalid_datasets()) == 0

    # test y_translation
    nx_tomo.sample.y_translation = [0] * meter
    assert len(splitter.get_invalid_datasets()) == 1
    nx_tomo.sample.y_translation = [0] * n_frames * meter
    assert len(splitter.get_invalid_datasets()) == 0

    # test z_translation
    nx_tomo.sample.z_translation = [0] * meter
    assert len(splitter.get_invalid_datasets()) == 1
    nx_tomo.sample.z_translation = [0] * n_frames * meter
    assert len(splitter.get_invalid_datasets()) == 0


def test_spliter_raw_data():
    """Test the splitter on a simple non-virtual h5py dataset."""
    nx_tomo = NXtomo()
    n_frames = 20
    nx_tomo.instrument.detector.data = numpy.random.random(
        100 * 100 * n_frames
    ).reshape([n_frames, 100, 100])
    nx_tomo.sample.rotation_angle = [0, 12] * degree
    nx_tomo.instrument.detector.sequence_number = numpy.linspace(
        0, n_frames, n_frames, dtype=numpy.uint32
    )

    splitter = NXtomoSplitter(nx_tomo=nx_tomo)
    # check incoherent number of rotation
    with pytest.raises(ValueError):
        splitter.split(data_slice=slice(0, 100, 1), nb_part=2)
    nx_tomo.sample.rotation_angle = (
        numpy.linspace(0, 180, num=n_frames, endpoint=False) * degree
    )
    # check slice nb_part < 0
    with pytest.raises(ValueError):
        splitter.split(data_slice=slice(0, 100, 1), nb_part=-1)
    # check slice step != 1
    with pytest.raises(ValueError):
        splitter.split(data_slice=slice(0, 100, 2), nb_part=2)
    # check incoherent number of frames
    with pytest.raises(ValueError):
        splitter.split(data_slice=slice(0, 99, 2), nb_part=2)

    # check x translation
    nx_tomo.sample.x_translation = [0, 12] * meter
    with pytest.raises(ValueError):
        splitter.split(data_slice=slice(0, 100, 1), nb_part=2)
    nx_tomo.sample.x_translation = numpy.random.random(n_frames) * meter
    nx_tomo.sample.y_translation = numpy.random.random(n_frames) * meter
    nx_tomo.sample.z_translation = numpy.random.random(n_frames) * meter
    # check image key
    nx_tomo.instrument.detector.image_key_control = [0, 2]
    with pytest.raises(ValueError):
        splitter.split(data_slice=slice(0, 100, 1), nb_part=2)
    nx_tomo.instrument.detector.image_key_control = [
        numpy.random.randint(low=-1, high=2) for i in range(n_frames)
    ]

    assert splitter.split(data_slice=slice(0, 100, 1), nb_part=1) == [
        nx_tomo,
    ]

    # check error if request to split a region bigger that the one (100 vs n_frames)
    with pytest.raises(ValueError):
        splitted_nx_tomo = splitter.split(data_slice=slice(0, 100, 1), nb_part=2)

    splitted_nx_tomo = splitter.split(data_slice=slice(0, 20, 1), nb_part=2)
    assert len(splitted_nx_tomo) == 2
    s_nx_tomo_1, s_nx_tomo_2 = splitted_nx_tomo
    # chek rotation_angle
    numpy.testing.assert_array_equal(
        s_nx_tomo_1.sample.rotation_angle,
        nx_tomo.sample.rotation_angle[0 : n_frames // 2],
    )
    numpy.testing.assert_array_equal(
        s_nx_tomo_2.sample.rotation_angle,
        nx_tomo.sample.rotation_angle[n_frames // 2 :],
    )
    # check image key and image key
    numpy.testing.assert_array_equal(
        s_nx_tomo_1.instrument.detector.image_key_control,
        nx_tomo.instrument.detector.image_key_control[0 : n_frames // 2],
    )
    numpy.testing.assert_array_equal(
        s_nx_tomo_2.instrument.detector.image_key_control,
        nx_tomo.instrument.detector.image_key_control[n_frames // 2 :],
    )
    # check sequence_number
    numpy.testing.assert_array_equal(
        s_nx_tomo_1.instrument.detector.sequence_number,
        numpy.linspace(0, n_frames // 2 - 1, n_frames // 2, dtype=numpy.uint32),
    )
    numpy.testing.assert_array_equal(
        s_nx_tomo_2.instrument.detector.sequence_number,
        numpy.linspace(n_frames // 2, n_frames, n_frames // 2, dtype=numpy.uint32),
    )

    # chek x translation
    numpy.testing.assert_array_equal(
        s_nx_tomo_1.sample.x_translation,
        nx_tomo.sample.x_translation[0 : n_frames // 2],
    )
    numpy.testing.assert_array_equal(
        s_nx_tomo_2.sample.x_translation,
        nx_tomo.sample.x_translation[n_frames // 2 :],
    )

    # chek y translation
    numpy.testing.assert_array_equal(
        s_nx_tomo_1.sample.y_translation,
        nx_tomo.sample.y_translation[0 : n_frames // 2],
    )
    numpy.testing.assert_array_equal(
        s_nx_tomo_2.sample.y_translation,
        nx_tomo.sample.y_translation[n_frames // 2 :],
    )
    # chek z translation
    numpy.testing.assert_array_equal(
        s_nx_tomo_1.sample.z_translation,
        nx_tomo.sample.z_translation[0 : n_frames // 2],
    )
    numpy.testing.assert_array_equal(
        s_nx_tomo_2.sample.z_translation,
        nx_tomo.sample.z_translation[n_frames // 2 :],
    )
    # check detector data
    numpy.testing.assert_array_equal(
        s_nx_tomo_1.instrument.detector.data,
        nx_tomo.instrument.detector.data[0 : n_frames // 2],
    )
    numpy.testing.assert_array_equal(
        s_nx_tomo_2.instrument.detector.data,
        nx_tomo.instrument.detector.data[n_frames // 2 :],
    )


def test_spliter_virtual_sources_1():
    """
    Test the splitter on a simulated h5py virtual dataset composed of two virtual sources.
    Both resulting NXtomo instances must reference the same virtual sources.
    Rotation_angle, [W]_translation, and image_key datasets are handled as NumPy arrays
    that do not point to external resources, so only `detector.data` is tested here.
    """
    nx_tomo = NXtomo()
    nx_tomo.instrument.detector.data = [
        h5py.VirtualSource("path_to_dataset_1", name="dataset_1", shape=[10, 100, 100]),
        h5py.VirtualSource("path_to_dataset_2", name="dataset_2", shape=[10, 100, 100]),
    ]
    splitter = NXtomoSplitter(nx_tomo=nx_tomo)
    splitted_nx_tomo = splitter.split(data_slice=slice(0, 20, 1), nb_part=2)
    assert len(splitted_nx_tomo) == 2
    s_nx_tomo_1, s_nx_tomo_2 = splitted_nx_tomo
    det_dataset_1 = s_nx_tomo_1.instrument.detector.data
    det_dataset_2 = s_nx_tomo_2.instrument.detector.data
    assert len(det_dataset_1) == 1
    assert len(det_dataset_2) == 1

    det_dataset_vs1 = det_dataset_1[0]
    det_dataset_vs2 = det_dataset_2[0]
    assert isinstance(det_dataset_vs1, h5py.VirtualSource)
    assert det_dataset_vs1.path == "path_to_dataset_1"
    assert det_dataset_vs1.shape == (10, 100, 100)

    assert isinstance(det_dataset_vs2, h5py.VirtualSource)
    assert det_dataset_vs2.path == "path_to_dataset_2"
    assert det_dataset_vs2.shape == (10, 100, 100)


def test_spliter_virtual_sources_2():
    """
    Test the splitter on an h5py virtual dataset composed of a single virtual source.
    It must split this source into two VirtualSource objects.
    Rotation_angle, [W]_translation, and image_key datasets are handled as NumPy arrays
    that do not point to external resources, so only `detector.data` is tested here.
    """
    nx_tomo = NXtomo()
    nx_tomo.instrument.detector.data = [
        h5py.VirtualSource(
            "path_to_dataset", name="path_to_dataset", shape=[20, 100, 100]
        ),
    ]
    splitter = NXtomoSplitter(nx_tomo=nx_tomo)
    splitted_nx_tomo = splitter.split(data_slice=slice(0, 20, 1), nb_part=2)
    assert len(splitted_nx_tomo) == 2

    splitted_nx_tomo = splitter.split(data_slice=slice(0, 20, 1), nb_part=4)
    assert len(splitted_nx_tomo) == 4


def test_spliter_virtual_sources_3():
    """
    Test the splitter on a concrete h5py virtual dataset.
    Rotation_angle, [W]_translation, and image_key datasets are handled as NumPy arrays
    that do not point to external resources, so only `detector.data` is tested here.
    """
    n_file = 5
    n_frame_per_file = 20
    layout = h5py.VirtualLayout(
        shape=(n_file * n_frame_per_file, 100, 100), dtype=float
    )
    with TemporaryDirectory() as folder:
        for i_file in range(n_file):
            file_path = os.path.join(folder, f"file{i_file}.hdf5")
            data_path = f"path_to_dataset_{i_file}"
            with h5py.File(file_path, mode="w") as h5f:
                if i_file == 0:
                    data = numpy.ones([n_frame_per_file, 100, 100])
                elif i_file == n_file - 1:
                    data = numpy.ones([n_frame_per_file, 100, 100]) * 2
                else:
                    start = i_file * 1000.0
                    stop = i_file * 1000.0 + (n_frame_per_file * 100 * 100)
                    data = numpy.arange(start, stop).reshape(n_frame_per_file, 100, 100)
                h5f[data_path] = data
                vs = h5py.VirtualSource(h5f[data_path])
                layout[i_file * n_frame_per_file : (i_file + 1) * n_frame_per_file] = vs

        master_file = os.path.join(folder, "master_file.hdf5")
        with h5py.File(master_file, mode="w") as h5f:
            h5f.create_virtual_dataset("data", layout)
            original_data = h5f["data"][()]

        nx_tomo = NXtomo()
        with h5py.File(master_file, mode="r") as h5f:
            vs_ = []
            for vs_info in h5f["data"].virtual_sources():
                vs_.append(
                    h5py.VirtualSource(
                        vs_info.file_name,
                        vs_info.dset_name,
                        shape=(n_frame_per_file, 100, 100),
                    )
                )

            nx_tomo.instrument.detector.data = vs_

        splitter = NXtomoSplitter(nx_tomo=nx_tomo)
        data_slice = slice(10, n_frame_per_file * n_file - 10, 1)
        splitted_nx_tomo = splitter.split(data_slice=data_slice, nb_part=2)
        assert len(splitted_nx_tomo) == 2
        # check the two dataset created
        s_nx_tomo_1, s_nx_tomo_2 = splitted_nx_tomo
        output_file_1 = os.path.join(folder, "output_file_1.nx")

        # data must contains a common section between the two nxtomo: the first 10 and last 10 frames
        # then the rest must be splitted between the two NXtomo
        assert len(s_nx_tomo_1.instrument.detector.data) == 5
        assert s_nx_tomo_1.instrument.detector.data[0].shape[0] == 10
        assert s_nx_tomo_1.instrument.detector.data[1].shape[0] == 10
        assert s_nx_tomo_1.instrument.detector.data[2].shape[0] == 20
        assert s_nx_tomo_1.instrument.detector.data[3].shape[0] == 10
        assert s_nx_tomo_1.instrument.detector.data[4].shape[0] == 10
        s_nx_tomo_1.save(output_file_1, "entry0000")

        output_file_2 = os.path.join(folder, "output_file_2.nx")
        assert len(s_nx_tomo_2.instrument.detector.data) == 5
        assert s_nx_tomo_2.instrument.detector.data[0].shape[0] == 10
        assert s_nx_tomo_2.instrument.detector.data[1].shape[0] == 10
        assert s_nx_tomo_2.instrument.detector.data[2].shape[0] == 20
        assert s_nx_tomo_2.instrument.detector.data[3].shape[0] == 10
        assert s_nx_tomo_2.instrument.detector.data[4].shape[0] == 10
        s_nx_tomo_2.save(output_file_2, "entry0000")

        # check final datasets are correctly formed
        with h5py.File(output_file_1, mode="r") as h5f:
            nx_1_data = h5f["entry0000/instrument/detector/data"][()]
        assert nx_1_data.shape[0] == 60

        # check final datasets are correctly formed
        with h5py.File(output_file_2, mode="r") as h5f:
            nx_2_data = h5f["entry0000/instrument/detector/data"][()]
        assert nx_2_data.shape[0] == 60

        # first 10 frames (common between the three nxtomo)
        numpy.testing.assert_array_equal(
            nx_1_data[0:10],
            nx_2_data[0:10],
        )
        numpy.testing.assert_array_equal(
            nx_1_data[0:10],
            original_data[0:10],
        )

        # last 10 frames (common between the three nxtomo)
        numpy.testing.assert_array_equal(
            nx_1_data[-10:],
            nx_2_data[-10:],
        )
        numpy.testing.assert_array_equal(
            nx_1_data[-10:],
            original_data[-10:],
        )

        # test nx_1_data unique region
        numpy.testing.assert_array_equal(
            nx_1_data[10:50],
            original_data[10:50],
        )

        # test nx_2_data unique region
        numpy.testing.assert_array_equal(
            nx_2_data[10:50],
            original_data[50:90],
        )


def test_spliter_data_url():
    """
    Test the splitter on a list of DataUrl objects.
    Rotation_angle, [W]_translation, and image_key datasets are handled as NumPy arrays
    that do not point to external resources, so only `detector.data` is tested here.
    """
    urls = []
    n_frame_per_file = 20
    n_file = 5
    original_data = []
    with TemporaryDirectory() as folder:
        for i_file in range(n_file):
            file_path = os.path.join(folder, f"file{i_file}.hdf5")
            data_path = f"path_to_dataset_{i_file}"
            with h5py.File(file_path, mode="w") as h5f:
                if i_file == 0:
                    data = numpy.ones([n_frame_per_file, 100, 100])
                elif i_file == n_file - 1:
                    data = numpy.ones([n_frame_per_file, 100, 100]) * 2
                else:
                    start = i_file * 1000.0
                    stop = i_file * 1000.0 + (n_frame_per_file * 100 * 100)
                    data = numpy.arange(start, stop).reshape(n_frame_per_file, 100, 100)
                h5f[data_path] = data
                original_data.append(data)

            urls.append(
                DataUrl(
                    file_path=file_path,
                    data_path=data_path,
                    scheme="silx",
                )
            )

        original_data = numpy.concatenate(original_data)

        nx_tomo = NXtomo()
        nx_tomo.instrument.detector.data = urls

        splitter = NXtomoSplitter(nx_tomo=nx_tomo)
        data_slice = slice(10, n_frame_per_file * n_file - 10, 1)
        data_slice = slice(10, n_frame_per_file * n_file - 10, 1)
        splitted_nx_tomo = splitter.split(data_slice=data_slice, nb_part=2)
        assert len(splitted_nx_tomo) == 2
        # check the two dataset created
        s_nx_tomo_1, s_nx_tomo_2 = splitted_nx_tomo
        output_file_1 = os.path.join(folder, "output_file_1.nx")

        # data must contains a common section between the two nxtomo: the first 10 and last 10 frames
        # then the rest must be splitted between the two NXtomo
        def n_elmt(slice_):
            return slice_.stop - slice_.start

        assert len(s_nx_tomo_1.instrument.detector.data) == 5
        assert n_elmt(s_nx_tomo_1.instrument.detector.data[0].data_slice()) == 10
        assert n_elmt(s_nx_tomo_1.instrument.detector.data[1].data_slice()) == 10
        assert n_elmt(s_nx_tomo_1.instrument.detector.data[2].data_slice()) == 20
        assert n_elmt(s_nx_tomo_1.instrument.detector.data[3].data_slice()) == 10
        assert n_elmt(s_nx_tomo_1.instrument.detector.data[4].data_slice()) == 10
        s_nx_tomo_1.save(output_file_1, "entry0000")

        output_file_2 = os.path.join(folder, "output_file_2.nx")
        assert len(s_nx_tomo_2.instrument.detector.data) == 5
        assert n_elmt(s_nx_tomo_2.instrument.detector.data[0].data_slice()) == 10
        assert n_elmt(s_nx_tomo_2.instrument.detector.data[1].data_slice()) == 10
        assert n_elmt(s_nx_tomo_2.instrument.detector.data[2].data_slice()) == 20
        assert n_elmt(s_nx_tomo_2.instrument.detector.data[3].data_slice()) == 10
        assert n_elmt(s_nx_tomo_2.instrument.detector.data[4].data_slice()) == 10
        s_nx_tomo_2.save(output_file_2, "entry0000")

        # check final datasets are correctly formed
        with h5py.File(output_file_1, mode="r") as h5f:
            nx_1_data = h5f["entry0000/instrument/detector/data"][()]
        assert nx_1_data.shape[0] == 60

        # check final datasets are correctly formed
        with h5py.File(output_file_2, mode="r") as h5f:
            nx_2_data = h5f["entry0000/instrument/detector/data"][()]
        assert nx_2_data.shape[0] == 60

        # first 10 frames (common between the three nxtomo)
        numpy.testing.assert_array_equal(
            nx_1_data[0:10],
            nx_2_data[0:10],
        )
        numpy.testing.assert_array_equal(
            nx_1_data[0:10],
            original_data[0:10],
        )

        # last 10 frames (common between the three nxtomo)
        numpy.testing.assert_array_equal(
            nx_1_data[-10:],
            nx_2_data[-10:],
        )
        numpy.testing.assert_array_equal(
            nx_1_data[-10:],
            original_data[-10:],
        )

        # test nx_1_data unique region
        numpy.testing.assert_array_equal(
            nx_1_data[10:50],
            original_data[10:50],
        )

        # test nx_2_data unique region
        numpy.testing.assert_array_equal(
            nx_2_data[10:50],
            original_data[50:90],
        )


def test_spliter_missing_projections():
    """
    If some projections are missing and `nb_turn` cannot be used, fall back to `tomo_n`.
    """
    urls = []
    n_frame_per_file = 20
    n_file = 5
    original_data = []
    with TemporaryDirectory() as folder:
        for i_file in range(n_file):
            file_path = os.path.join(folder, f"file{i_file}.hdf5")
            data_path = f"path_to_dataset_{i_file}"
            with h5py.File(file_path, mode="w") as h5f:
                if i_file == 0:
                    data = numpy.ones([n_frame_per_file, 100, 100])
                elif i_file == n_file - 1:
                    data = numpy.ones([n_frame_per_file, 100, 100]) * 2
                else:
                    start = i_file * 1000.0
                    stop = i_file * 1000.0 + (n_frame_per_file * 100 * 100)
                    data = numpy.arange(start, stop).reshape(n_frame_per_file, 100, 100)
                h5f[data_path] = data
                original_data.append(data)

            urls.append(
                DataUrl(
                    file_path=file_path,
                    data_path=data_path,
                    scheme="silx",
                )
            )

        original_data = numpy.concatenate(original_data)

        nx_tomo = NXtomo()
        nx_tomo.instrument.detector.data = urls

        splitter = NXtomoSplitter(nx_tomo=nx_tomo)
        data_slice = slice(0, 100, 1)
        data_slice = slice(0, 100, 1)
        splitted_nx_tomo = splitter.split(data_slice=data_slice, nb_part=2)
        assert len(splitted_nx_tomo) == 2

        splitted_nx_tomo = splitter.split(
            data_slice=data_slice, nb_part=None, tomo_n=20
        )
        assert len(splitted_nx_tomo) == 5

        splitted_nx_tomo = splitter.split(
            data_slice=data_slice, nb_part=None, tomo_n=40
        )
        assert len(splitted_nx_tomo) == 3

        splitted_nx_tomo = splitter.split(
            data_slice=data_slice, nb_part=None, tomo_n=65
        )
        assert len(splitted_nx_tomo) == 2
