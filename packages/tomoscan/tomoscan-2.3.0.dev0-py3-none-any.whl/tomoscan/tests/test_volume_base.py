# coding: utf-8
"""Module containing validators"""

import pytest

from tomoscan.volumebase import VolumeBase


def test_volume_base():
    """Test VolumeBase file"""

    class UnimplementedVolumeBase(VolumeBase):
        def deduce_data_and_metadata_urls(self, url):
            return None, None

    volume_base = UnimplementedVolumeBase()

    with pytest.raises(NotImplementedError):
        volume_base.example_defined_from_str_identifier()

    with pytest.raises(NotImplementedError):
        volume_base.get_identifier()

    with pytest.raises(NotImplementedError):
        VolumeBase.from_identifier("")

    with pytest.raises(NotImplementedError):
        volume_base.save_data()

    with pytest.raises(NotImplementedError):
        volume_base.save_metadata()

    with pytest.raises(NotImplementedError):
        volume_base.save()

    with pytest.raises(NotImplementedError):
        volume_base.load_data()

    with pytest.raises(NotImplementedError):
        volume_base.load_metadata()

    with pytest.raises(NotImplementedError):
        volume_base.load()

    with pytest.raises(NotImplementedError):
        volume_base.browse_data_files()

    with pytest.raises(NotImplementedError):
        volume_base.browse_metadata_files()

    with pytest.raises(NotImplementedError):
        volume_base.browse_data_urls()

    volume_base.position = (0, 1, 2)
    assert isinstance(volume_base.position, tuple)
    assert volume_base.position == (0, 1, 2)

    volume_base.voxel_size = (12.3, 2.5, 6.9)
    assert volume_base.voxel_size == (12.3, 2.5, 6.9)
    assert type(volume_base.voxel_size[0]) is float
