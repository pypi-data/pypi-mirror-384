"""mapper functions to convert from raw data fields (like nabu reconstructed volume metadata) to drac / icat fields"""

from __future__ import annotations

import numpy
from .recons_vol_mapping import DRAC_NABU_MAPPING, DracRawDataMapping


__all__ = [
    "flatten_vol_metadata",
    "map_nabu_keys_to_drac",
]


def flatten_vol_metadata(metadata: dict, parent_key: str = "", sep="/") -> dict:
    """
    Flatten a nested dictionary (expected to come from nabu volume metadata) and converting arrays to lists
    and numpy types to serializable types. The resulting dictionary is JSON-serializable.

    :param metadata: The dictionary to flatten.
    :param parent_key: The base key string used for recursive calls.
    :param sep: The separator used between parent and child keys.

    :return: The flattened and type-converted dictionary.
    """
    # Exclusion list
    items = []
    for k, v in metadata.items():

        # Construct the new key
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_vol_metadata(v, new_key, sep=sep).items())
        else:
            # Convert numpy arrays to lists
            if isinstance(v, numpy.ndarray):
                v = v.tolist()
            # Convert numpy boolean to native boolean
            elif isinstance(v, numpy.bool_):
                v = bool(v)
            # Convert numpy integers to native int
            elif isinstance(v, (numpy.int64, numpy.int32)):
                v = int(v)
            # Convert numpy floats to native float
            elif isinstance(v, (numpy.float64, numpy.float32)):
                v = float(v)

            items.append((new_key, v))

    return dict(items)


def map_nabu_keys_to_drac(flatten_dict: dict) -> dict:
    """
    map a set of **nabu** keys to drac 'TOMOReconstruction' definition (https://gitlab.esrf.fr/icat/hdf5-master-config/-/blob/master/hdf5_cfg.xml)
    """
    drac_dict = {}
    for map in DRAC_NABU_MAPPING:
        assert isinstance(
            map, DracRawDataMapping
        ), f"map should be an instance of {DracRawDataMapping}. Got {type(map)}"
        if map.raw_data_key in flatten_dict:
            raw_data = flatten_dict[map.raw_data_key]
            drac_value = map.to_drac(raw_data)
            drac_dict[map.drac_key] = drac_value

    return drac_dict
