"""test of the .vol Volume"""

import os

import numpy
import pytest
from silx.io.url import DataUrl

from tomoscan.esrf.identifier import RawVolumeIdentifier
from tomoscan.esrf.volume.mock import create_volume
from tomoscan.esrf.volume.rawvolume import RawVolume
from tomoscan.identifier import VolumeIdentifier

_data = create_volume(frame_dims=(20, 20), z_size=60)
_data = _data.astype(numpy.uint8)

metadata_info = {
    "NUM_X": 20,
    "NUM_Y": 20,
    "NUM_Z": 60,
    "voxelSize": 2.3e-2,
    "BYTEORDER": "LOWBYTEFIRST",
    "ValMin": _data.min(),
    "ValMax": _data.max(),
    "s1": -1.13,
    "s2": 8.19,
    "S1": -4.13,
    "S2": 5.15,
}

metadata_xml = {
    "idAc": "N_A_",
    "listSubVolume": {
        "SUBVOLUME_NAME": "toto_volume",
        "SIZEX": metadata_info["NUM_X"],
        "SIZEY": metadata_info["NUM_Y"],
        "SIZEZ": metadata_info["NUM_Z"],
        "ORIGINX": 1,
        "ORIGINY": 1,
        "ORIGINZ": 1,
        "DIM_REC": 14155776000,
        "voxelsize": metadata_info["voxelSize"],
        "BYTE_ORDER": metadata_info["BYTEORDER"],
        "ValMin": metadata_info["ValMin"],
        "ValMax": metadata_info["ValMax"],
        "s1": metadata_info["s1"],
        "s2": metadata_info["s2"],
        "S1": metadata_info["S1"],
        "S2": metadata_info["S2"],
    },
}


def test_raw_volume(tmp_path):
    test_dir = str(tmp_path / "test_volume_url")
    os.makedirs(test_dir)
    volume_file = os.path.join(test_dir, "volume.vol")
    metadata_info_volume_file = os.path.join(test_dir, "volume.vol.info")
    metadata_xml_volume_file = os.path.join(test_dir, "volume.vol.xml")

    volume = RawVolume(
        file_path=volume_file,
        data=_data,
        metadata=metadata_info,
    )
    assert volume.url.file_path() == volume_file

    assert volume.url.data_path() is None
    assert volume.data_url.scheme() == "raw"
    assert volume.data_url.file_path() == volume_file
    assert volume.data_url.data_path() is None
    assert volume.metadata_url.scheme() == "info"
    assert volume.metadata_url.file_path() == metadata_info_volume_file
    assert volume.metadata_url.data_path() is None

    volume_identifier = volume.get_identifier()
    assert isinstance(volume_identifier.short_description(), str)
    assert isinstance(volume_identifier, VolumeIdentifier)

    assert not os.path.exists(volume_file)
    assert not os.path.exists(metadata_info_volume_file)
    assert not os.path.exists(metadata_xml_volume_file)

    # make sure saving other file format than float32 make it fails
    with pytest.raises(TypeError):
        volume.save()
    data_cast = volume.data.astype(numpy.float32)
    volume.data = data_cast
    volume.save()
    # try to save it twice to make sure we are not appending data to it

    assert os.path.exists(volume_file)
    assert os.path.exists(metadata_info_volume_file)
    assert not os.path.exists(metadata_xml_volume_file)
    xml_url = DataUrl(
        file_path=metadata_xml_volume_file,
        scheme="lxml",
    )
    volume.metadata = metadata_xml
    volume.save_metadata(url=xml_url)
    assert os.path.exists(metadata_xml_volume_file)

    assert tuple(volume.browse_data_urls()) == (volume.data_url,)
    assert tuple(volume.browse_data_files()) == (volume.data_url.file_path(),)
    assert tuple(volume.browse_metadata_files()) == (volume.metadata_url.file_path(),)

    volume_loaded = RawVolume(file_path=volume_file)
    assert volume.url.file_path() == volume_file
    assert volume.metadata_url.file_path() == metadata_info_volume_file
    data_no_cache = volume_loaded.load_data(volume_loaded.data_url, store=False)
    metadata_no_cache = volume_loaded.load_metadata(
        volume_loaded.metadata_url, store=False
    )
    assert data_no_cache is not None
    assert metadata_no_cache is not None
    assert volume_loaded.data is None
    assert volume_loaded.metadata is None
    data_float_32 = _data.astype(numpy.float32)
    numpy.testing.assert_array_almost_equal(data_float_32, data_no_cache)
    # only check keys because values are not cast (once read everything is a str...)
    assert metadata_info.keys() == metadata_no_cache.keys()
    assert volume.get_min_max_values() == (data_float_32.min(), data_float_32.max())
    # check error is raised if byte order is incorrect
    highbytefirst = numpy.dtype(">" + volume.data.dtype.char)
    volume.data = volume.data.astype(highbytefirst)
    with pytest.raises(TypeError):
        volume.save_data()

    # get the volume from the identifier
    volume_from_id = RawVolume.from_identifier(identifier=volume_identifier)
    assert volume_from_id.data is None
    assert volume_from_id.metadata is None

    # get the volume from the identifier str
    volume_from_str = RawVolume.from_identifier(
        identifier=RawVolumeIdentifier.from_str(volume_identifier.to_str())
    )
    assert volume_from_str.data is None
    assert volume_from_str.metadata is None
    assert volume_from_str.get_identifier() == volume_from_id.get_identifier()

    # test browsing frames
    # TODO

    # test hash
    hash(volume_from_str)
    assert volume.data_extension == "vol"
    assert volume.metadata_extension == "info"


def test_data_file_saver_generator(tmp_path):
    """
    data_file_saver_generator (dumping frame by frame a volume to disk)
    """
    volume_file_path = str(tmp_path / "volume_for_file_generator.vol")
    volume = RawVolume(file_path=volume_file_path)
    data_cast = _data.astype(numpy.float32)

    for slice_, slice_saver in zip(
        data_cast,
        volume.data_file_saver_generator(
            n_frames=_data.shape[0], data_url=volume.data_url, overwrite=False
        ),
    ):
        slice_saver[:] = slice_
    assert volume.data is None
    volume.metadata = metadata_info
    volume.save_metadata()
    numpy.testing.assert_array_equal(
        volume.load_data(),
        data_cast,
    )


def test_raw_volume_slice_getter(tmp_path):
    """
    tset slice getters
    """
    volume_file = str(tmp_path / "volume_test_getter.vol")
    data_cast = _data.astype(numpy.float32)

    volume = RawVolume(
        file_path=volume_file,
        data=data_cast,
        metadata=metadata_info,
        overwrite=True,
    )
    volume.save()
    assert os.path.exists(volume_file)

    volume_loaded = RawVolume(
        file_path=volume_file,
    )
    volume_loaded.load()
    numpy.testing.assert_array_equal(
        data_cast,
        volume_loaded.data,
    )

    # test get_slice function
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=0),
        data_cast[2],
    )
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=1),
        data_cast[:, 2, :],
    )
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=2),
        data_cast[:, :, 2],
    )
    volume_loaded.data = None

    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=0),
        data_cast[2],
    )
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=1),
        data_cast[:, 2, :],
    )
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=2),
        data_cast[:, :, 2],
    )


def test_append_writes(tmp_path):
    """
    Test trying to mimic PyHST2 output files that can be opened with imagej:
      - One single .vol, written in several steps (append mode)
      - One .info file (for users ?)
      - One .xml file (for ImageJ)
    """

    def generate_metadata(data, **kwargs):
        n_z, n_y, n_x = data.shape
        metadata = {
            "NUM_X": n_x,
            "NUM_Y": n_y,
            "NUM_Z": n_z,
            "voxelSize": kwargs.get("voxelSize", 40.0),
            "BYTEORDER": "LOWBYTEFIRST",
            "ValMin": kwargs.get("ValMin", 0.0),
            "ValMax": kwargs.get("ValMin", 1.0),
            "s1": 0.0,
            "s2": 0.0,
            "S1": 0.0,
            "S2": 0.0,
        }
        return metadata

    def sanitize_metadata(metadata):
        # To be fixed in RawVolume
        for what in ["NUM_X", "NUM_Y", "NUM_Z"]:
            metadata[what] = int(metadata[what])
        for what in ["voxelSize", "ValMin", "ValMax", "s1", "s2", "S1", "S2"]:
            metadata[what] = float(metadata[what])

    def write_data(volume, data):
        existing_metadata = volume.load_metadata()
        new_metadata = generate_metadata(data)
        if len(existing_metadata) == 0:
            # first write
            metadata = new_metadata
        else:
            # append write ; update metadata
            metadata = existing_metadata.copy()
            sanitize_metadata(metadata)
            metadata["NUM_Z"] += new_metadata["NUM_Z"]
        volume.data = data
        volume.metadata = metadata
        volume.save()
        # Also save .xml
        volume.save_metadata(
            url=DataUrl(
                scheme="lxml",
                file_path=volume.metadata_url.file_path().replace(".info", ".xml"),
            )
        )

    volume_file = str(tmp_path / "volume_append.vol")

    volume = RawVolume(
        file_path=volume_file,
        append=True,
    )

    # First write
    data_1 = numpy.arange(10 * 32 * 32, dtype="f").reshape((10, 32, 32))
    write_data(volume, data_1)

    # Second write - metadata should be updated
    data_2 = numpy.arange(11 * 32 * 32, dtype="f").reshape((11, 32, 32))
    write_data(volume, data_2)

    # Third write - metadata should be updated
    data_3 = numpy.arange(12 * 32 * 32, dtype="f").reshape((12, 32, 32))
    write_data(volume, data_3)

    assert int(volume.load_metadata()["NUM_Z"]) == 10 + 11 + 12
    assert os.path.getsize(volume_file) == data_1.nbytes + data_2.nbytes + data_3.nbytes


def test_example():
    """test static function 'example'"""
    assert isinstance(RawVolume.example_defined_from_str_identifier(), str)
