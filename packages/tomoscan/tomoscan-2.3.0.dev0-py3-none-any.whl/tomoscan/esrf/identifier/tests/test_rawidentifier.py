# coding: utf-8

from tomoscan.esrf.identifier.rawidentifier import RawVolumeIdentifier


def test_vol_identifier():
    """insure identifier is working for .vol files"""
    from tomoscan.esrf.volume.rawvolume import RawVolume

    identifier = RawVolumeIdentifier(
        object=RawVolume,
        file_path="/dsad/test.vol",
    )
    assert str(identifier).startswith(f"raw:{RawVolumeIdentifier.TOMO_TYPE}:")
