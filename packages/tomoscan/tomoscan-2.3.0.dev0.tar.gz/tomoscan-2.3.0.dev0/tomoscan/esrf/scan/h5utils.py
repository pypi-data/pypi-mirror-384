import numpy as np
from silx.io.utils import open as hdf5_open

__all__ = [
    "get_first_hdf5_entry",
    "get_h5_value",
    "get_h5obj_value",
    "get_hdf5_dataset_shape",
]


def get_first_hdf5_entry(fname):
    with hdf5_open(fname) as fid:
        entry = list(fid.keys())[0]
    return entry


def get_h5_value(fname, h5_path, default_ret=None):
    with hdf5_open(fname) as fid:
        try:
            val_ptr = fid[h5_path][()]
            # TODO: look at silx.io.utils.h5py_read_dataset might replace it
        except KeyError:
            val_ptr = default_ret
    return val_ptr


def get_h5obj_value(h5_obj, name, default=None):
    if name in h5_obj:
        return h5_obj[name][()]
    return default


def _get_3D_subregion(sub_region):
    if sub_region is None:
        xmin, xmax, ymin, ymax, zmin, zmax = None, None, None, None, None, None
    elif len(sub_region) == 3:
        first_part, second_part, third_part = sub_region
        xmin, xmax = first_part
        ymin, ymax = second_part
        zmin, zmax = third_part
    elif len(sub_region) == 6:
        xmin, xmax, ymin, ymax, zmin, zmax = sub_region
    else:
        raise ValueError(
            "Expected parameter in the form (xmin, xmax, ymin, ymax, zmin, zmax) or ((xmin, xmax), (ymin, ymax), (zmin, zmax))"
        )
    return xmin, xmax, ymin, ymax, zmin, zmax


def get_hdf5_dataset_shape(fname, h5_data_path, sub_region=None):
    zmin, zmax, ymin, ymax, xmin, xmax = _get_3D_subregion(sub_region)
    with hdf5_open(fname) as f:
        d_ptr = f[h5_data_path]
        shape = d_ptr.shape
    n_z, n_y, n_x = shape
    # perhaps there is more elegant
    res_shape = []
    for n, bounds in zip([n_z, n_y, n_x], ((zmin, zmax), (ymin, ymax), (xmin, xmax))):
        res_shape.append(np.arange(n)[bounds[0] : bounds[1]].size)
    return tuple(res_shape)
