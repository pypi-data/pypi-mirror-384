"""module with helper ot save single frame"""

from __future__ import annotations

from tomoscan.esrf.volume.singleframebase import VolumeSingleFrameBase


class SingleFrameSaverHelper:
    """
    Allow to save to a single file per frame structure along any axis. The volume is expected to be 3D.

    .. note:: This is not part of the VolumeSingleFrameBase API because we want to make it clear that way of saving is very particular
              and might comes with some botlnecks
    """

    def __init__(
        self,
        volume: VolumeSingleFrameBase,
        data_shape: tuple,
        dtype,
        cache_size: int | None = None,
    ) -> None:
        """
        :param volume: volume to save data for
        :param shape: final data shape
        :param dtype: data type (as a numpy data type)
        :param cache_size: cache of the size (in bytes). Once this size is reached then the data will be dump to disk...
        """
        if not isinstance(volume, VolumeSingleFrameBase):
            raise TypeError(
                f"volume is expected to be an instance of VolumeSingleFrameBase. Get {type(volume)}"
            )
        if not isinstance(data_shape, tuple):
            raise TypeError(
                f"shape is expected to be an instance of tuple. Get {type(data_shape)}"
            )

        self._volume = volume
        self._shape = data_shape
        self._dtype = dtype
        self._frame_index_to_file = None
        self._initialized = False

    def init_saver(self):
        self._frame_index_to_file = {}
        for i, frame_dumper in enumerate(
            self._volume.data_file_saver_generator(
                n_frames=self._shape[0],
                data_url=self._volume.data_url,
                overwrite=self._volume.overwrite,
            ),
        ):
            self._frame_index_to_file[i] = frame_dumper
        self._initialized = True

        for i in range(len(self._frame_index_to_file) - 1):
            assert self._frame_index_to_file[i] != self._frame_index_to_file[i + 1]

    def __setitem__(self, index, value):
        if not self._initialized:
            raise RuntimeError(
                "the helper should be initialized first. Freezing the shape. Please call 'init_saver' before dumping any data to it"
            )
        if isinstance(index, slice):
            # in case we are saving the full frame there is no need for any cache mecanism
            self._frame_index_to_file[index.start, index.stop, index.step][:] = value
        elif isinstance(index, (int, tuple)):
            # in case we are saving the full frame there is no need for any cache mecanism
            self._frame_index_to_file[index][:] = value
        else:
            raise NotImplementedError(
                f"index is expected to be an instance of int or a tuple of int. Got {type(index)}"
            )
