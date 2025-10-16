import logging
import os
from collections.abc import Mapping

import h5py
import numpy

from tomoscan.esrf.volume import HDF5Volume
from tomoscan.utils.hdf5 import DatasetReader
from tomoscan.volumebase import VolumeBase

_logger = logging.getLogger(__name__)


def concatenate(output_volume: VolumeBase, volumes: tuple, axis: int) -> None:
    """
    Function to do 'raw' concatenation on volumes.

    This is agnostic of any metadata. So if you want to ensure about coherence of metadata (and data) you must do it yourself

    data will be concatenate in the order volumes are provided. Volumes data must be 3D. Concatenate data will be 3D and concatenation will be done
    over the axis `axis`

    concatenation will be done with a virtual dataset if input volumes and output_volume are HDF5Volume instances.

    warning: concatenation enforce writing data and metadata to disk

    :param output_volume VolumeBase: volume to create
    :param tuple volumes: tuple of VolumeBase instances
    :param axis: axis to use for doing the concatenation. must be in 0, 1, 2
    """
    # 0. do some check
    if not isinstance(output_volume, VolumeBase):
        raise TypeError(
            f"output_volume is expected to be an instance of {VolumeBase}. {type(output_volume)} provided"
        )
    if not isinstance(axis, int):
        raise TypeError(f"axis must be an int. {type(axis)} provided")
    elif axis not in (0, 1, 2):
        raise ValueError(f"axis must be in (0, 1, 2). {axis} provided")
    if not isinstance(volumes, tuple):
        raise TypeError(f"volumes must be a tuple. {type(volumes)} provided")
    else:
        is_invalid = lambda y: not isinstance(y, VolumeBase)
        invalids = tuple(filter(is_invalid, volumes))
        if len(invalids) > 0:
            raise ValueError(f"Several non-volumes found. ({invalids})")

    from tomoscan.esrf.volume.jp2kvolume import JP2KVolume  # avoid cyclic import

    if isinstance(output_volume, JP2KVolume) and output_volume.rescale_data is True:
        _logger.warning(
            "concatenation will rescale data frame. If you want to avoid this please set output volume 'rescale_data' to False"
        )

    # 1. compute final shape
    def get_volume_shape():
        if axis == 0:
            new_shape = [0, None, None]
        elif axis == 1:
            new_shape = [None, 0, None]
        else:
            new_shape = [None, None, 0]

        for vol in volumes:
            vol_shape = vol.get_volume_shape()
            if vol_shape is None:
                raise ValueError(
                    f"Unable to find shape for volume {vol.get_identifier().to_str()}"
                )
            new_shape[axis] += vol_shape[axis]
            if axis == 0:
                if new_shape[1] is None:
                    new_shape[1], new_shape[2] = vol_shape[1], vol_shape[2]
                elif new_shape[1] != vol_shape[1] or new_shape[2] != vol_shape[2]:
                    raise ValueError("Found incoherent shapes. Unable to concatenate")
            elif axis == 1:
                if new_shape[0] is None:
                    new_shape[0], new_shape[2] = vol_shape[0], vol_shape[2]
                elif new_shape[0] != vol_shape[0] or new_shape[2] != vol_shape[2]:
                    raise ValueError("Found incoherent shapes. Unable to concatenate")
            else:
                if new_shape[0] is None:
                    new_shape[0], new_shape[1] = vol_shape[0], vol_shape[1]
                elif new_shape[0] != vol_shape[0] or new_shape[1] != vol_shape[1]:
                    raise ValueError("Found incoherent shapes. Unable to concatenate")
        return tuple(new_shape)

    final_shape = get_volume_shape()
    if final_shape is None:
        # should never be raised. Other error type is expected to be raised first
        raise RuntimeError("Unable to get final volume shape")

    # 2. Handle volume data (concatenation)

    if isinstance(output_volume, HDF5Volume) and numpy.all(
        [isinstance(vol, HDF5Volume)] for vol in volumes
    ):
        # 2.1 in the case of HDF5 we can short cut this by creating a virtual dataset. Would highly speed up processing avoid copy
        # note: in theory this could be done for any input_volume type using external dataset but we don't want to spend ages on
        # this use case for now. Some work around this (using EDf) has been done in nxtomomill for information. See https://gitlab.esrf.fr/tomotools/nxtomomill/-/merge_requests/115
        _logger.info("start creation of external dataset")
        with DatasetReader(volumes[0].data_url) as dataset:
            data_type = dataset.dtype
        # FIXME: avoid keeping some file open. not clear why this is needed
        dataset = None

        with h5py.File(output_volume.data_url.file_path(), mode="a") as h5s:
            # 2.1.1 check data path
            if output_volume.data_url.data_path() in h5s:
                if output_volume.overwrite:
                    del h5s[output_volume.data_url.data_path()]
                else:
                    raise OSError(
                        f"Unable to save data to {output_volume.data_url.data_path()}. This path already exists in {output_volume.data_url.file_path()}. If you want you can ask to overwrite it (from the output volume)."
                    )
            # 2.1.2 create virtual layout
            v_layout = h5py.VirtualLayout(
                shape=final_shape,
                dtype=data_type,
            )

            # 2.1.3 create virtual source
            start_index = 0
            for volume in volumes:
                # provide relative path
                rel_file_path = os.path.relpath(
                    volume.data_url.file_path(),
                    os.path.dirname(output_volume.data_url.file_path()),
                )
                rel_file_path = "./" + rel_file_path
                data_path = volume.data_url.data_path()
                vol_shape = volume.get_volume_shape()
                vs = h5py.VirtualSource(
                    rel_file_path,
                    name=data_path,
                    shape=vol_shape,
                )
                stop_index = start_index + vol_shape[axis]
                if axis == 0:
                    v_layout[start_index:stop_index] = vs
                elif axis == 1:
                    v_layout[:, start_index:stop_index, :] = vs
                elif axis == 2:
                    v_layout[:, :, start_index:stop_index] = vs
                start_index = stop_index

            # 2.1.4 create virtual dataset
            h5s.create_virtual_dataset(
                name=output_volume.data_url.data_path(), layout=v_layout
            )

    else:
        # 2.1 default case (duplicate all input data slice by slice)
        # 2.1.1 special case of the concatenation other axis 0
        if axis == 0:

            def iter_input():
                for vol in volumes:
                    for data_slice in vol.browse_slices():
                        yield data_slice

            for frame_dumper, input_slice in zip(
                output_volume.data_file_saver_generator(
                    n_frames=final_shape[0],
                    data_url=output_volume.data_url,
                    overwrite=output_volume.overwrite,
                ),
                iter_input(),
            ):
                frame_dumper[:] = input_slice
        else:
            # 2.1.2 concatenation with data duplication over axis 1 or 2
            for i_z, frame_dumper in enumerate(
                output_volume.data_file_saver_generator(
                    n_frames=final_shape[0],
                    data_url=output_volume.data_url,
                    overwrite=output_volume.overwrite,
                )
            ):
                if axis == 1:
                    frame_dumper[:] = numpy.concatenate(
                        [vol.get_slice(axis=0, index=i_z) for vol in volumes],
                        axis=0,
                    )
                elif axis == 2:
                    frame_dumper[:] = numpy.concatenate(
                        [vol.get_slice(axis=0, index=i_z) for vol in volumes],
                        axis=1,
                    )
                else:
                    raise RuntimeError

    # 3. handle metadata
    for vol in volumes:
        if vol.metadata is None:
            try:
                vol.load_metadata(store=True)
            except Exception as e:
                _logger.error(f"fail to load metadata for {vol}. Error is {e}")
    output_volume.metadata = {}

    [update_metadata(output_volume.metadata, vol.metadata) for vol in volumes]
    output_volume.save_metadata()


def update_metadata(ddict_1: dict, ddict_2: dict) -> dict:
    """
    update metadata ddict_1 from ddict_2

    metadata are dict. And those dicts
    warning: will modify ddict_1
    """
    if not isinstance(ddict_1, dict) or not isinstance(ddict_2, dict):
        raise TypeError(f"ddict_1 and ddict_2 are expected to be instances of {dict}")
    for key, value in ddict_2.items():
        if isinstance(value, Mapping):
            ddict_1[key] = update_metadata(ddict_1.get(key, {}), value)
        else:
            ddict_1[key] = value
    return ddict_1


def rescale_data(data, new_min, new_max, data_min=None, data_max=None):
    if data_min is None:
        data_min = numpy.min(data)
    if data_max is None:
        data_max = numpy.max(data)
    return (new_max - new_min) / (data_max - data_min) * (data - data_min) + new_min
