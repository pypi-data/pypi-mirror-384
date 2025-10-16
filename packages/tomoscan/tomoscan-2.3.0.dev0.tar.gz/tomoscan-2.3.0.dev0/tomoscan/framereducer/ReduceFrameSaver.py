from __future__ import annotations

import os
import h5py
import numpy
import fabio
import pint

from silx.io.url import DataUrl

from tomoscan.framereducer.reducedframesinfos import ReducedFramesInfos

_ureg = pint.get_application_registry()


class ReduceFrameSaver:
    """
    Util function to save reduced frames to disk.
    """

    def __init__(
        self,
        frames: dict[int, numpy.ndarray],
        output_urls: tuple[DataUrl, ...],
        frames_metadata: ReducedFramesInfos | None,
        metadata_output_urls: tuple | None,
        overwrite: bool = False,
    ):
        """
        :param frames: Frames as a dict to be saved. Key is the index of the frame, value is the frame as a 2D numpy array.
        :param output_urls: A list of URLs specifying the locations where the frames will be saved.
            Each URL in the list can include specific keywords that the frame saver will dynamically replace.
            These keywords allow for customizable naming conventions for the saved frames. Supported keywords are:

            - '{index}': This keyword will be replaced by the index of the frame.
            - '{index_zfill4}': This keyword will be replaced by the index of the frame, zero-padded to four digits.
        :param frames_metadata: Metadata associated to the frames (like count time).
        :param metadata_output_urls: A list of URLs specifying the locations where the metadata of the reduced frames will be saved.
        :param overwrite: If True and if one of the output url already exists it will overwrite it. Else it will raise an Error.
        """
        if not isinstance(frames, dict):
            raise TypeError(
                f"inputs `frames` is expected to be a dict not {type(frames)}"
            )
        if not isinstance(output_urls, (list, tuple, set)):
            raise TypeError(
                f"output_urls is expected to be a tuple not a {type(output_urls)}"
            )

        if frames_metadata is not None:
            if not isinstance(frames_metadata, ReducedFramesInfos):
                raise TypeError(
                    f"darks_infos is a {type(frames_metadata)} when None or {ReducedFramesInfos} expected"
                )
            self._check_reduced_infos(reduced_frames=frames, infos=frames_metadata)

        self.frames = frames
        self.output_urls = output_urls
        self.frames_metadata = frames_metadata
        self.metadata_output_urls = metadata_output_urls
        self.overwrite = overwrite

    @staticmethod
    def _check_reduced_infos(reduced_frames, infos):
        incoherent_metadata_mess = "incoherent provided infos:"
        incoherent_metadata = False
        if len(infos.count_time) not in (0, len(reduced_frames)):
            incoherent_metadata = True
            incoherent_metadata_mess += f"\n - count_time gets {len(infos.count_time)} when 0 or {len(reduced_frames)} expected"
        if len(infos.machine_current) not in (0, len(reduced_frames)):
            incoherent_metadata = True
            incoherent_metadata_mess += f"\n - machine_current gets {len(infos.machine_current)} when 0 or {len(reduced_frames)} expected"
        if incoherent_metadata:
            raise ValueError(incoherent_metadata_mess)

    def clean_frame_group(self, url):
        """
        For HDF5 in order to avoid file size increase we need to overwrite dataset when possible.
        But the darks / flats groups can contain other datasets and pollute this group.
        This function will remove unused dataset (frame index) when necessary
        """
        file_path = self._format_file_path(
            url.file_path(), index=None, index_zfill4=None
        )
        if not (os.path.exists(file_path) and h5py.is_hdf5(file_path)):
            return

        group_path = "/".join(
            self._format_data_path(url.data_path(), index=0, index_zfill4="0000").split(
                "/"
            )[:-1]
        )
        used_datasets = []
        for idx, _ in self.frames.items():
            idx_zfill4 = str(idx).zfill(4)
            used_datasets.append(
                self._format_data_path(
                    url.data_path(), index=idx, index_zfill4=idx_zfill4
                ).split("/")[-1]
            )
        with h5py.File(file_path, mode="a") as h5s:
            if group_path in h5s:
                if not self.overwrite:
                    raise KeyError("group_path already exists")
                for key in h5s[group_path].keys():
                    if key not in used_datasets:
                        del h5s[group_path][key]

    def save(self):
        # save data
        for url in self.output_urls:
            self.clean_frame_group(url=url)
            # first delete keys that are no more used
            for i_frame, (idx, frame) in enumerate(self.frames.items()):
                if not isinstance(frame, numpy.ndarray):
                    raise TypeError("frames are expected to be 2D numpy.ndarray")
                elif frame.ndim == 3 and frame.shape[0] == 1:
                    frame = frame.reshape([frame.shape[1], frame.shape[2]])
                elif frame.ndim != 2:
                    raise ValueError("frames are expected to be 2D numpy.ndarray")
                idx_zfill4 = str(idx).zfill(4)
                data_path = self._format_data_path(
                    url.data_path(), index=idx, index_zfill4=idx_zfill4
                )

            # small hack to insure 'flats' or 'darks' group are cleaned when start to write in
            for i_frame, (idx, frame) in enumerate(self.frames.items()):
                if not isinstance(frame, numpy.ndarray):
                    raise TypeError("frames are expected to be 2D numpy.ndarray")
                elif frame.ndim == 3 and frame.shape[0] == 1:
                    frame = frame.reshape([frame.shape[1], frame.shape[2]])
                elif frame.ndim != 2:
                    raise ValueError("frames are expected to be 2D numpy.ndarray")
                idx_zfill4 = str(idx).zfill(4)
                data_path = self._format_data_path(
                    url.data_path(), index=idx, index_zfill4=idx_zfill4
                )

                file_path = self._format_file_path(
                    url.file_path(), index=idx, index_zfill4=idx_zfill4
                )
                scheme = url.scheme()

                if scheme == "fabio":
                    if data_path is not None:
                        raise ValueError("fabio does not handle data_path")
                    else:
                        # for edf: add metadata to the header if some, without taking into account the
                        # metadata_output_urls (too complicated for backward compatibility...)
                        header = {}
                        if (
                            self.frames_metadata is not None
                            and len(self.frames_metadata.machine_current) > 0
                        ):
                            header["SRCUR"] = self.frames_metadata.machine_current[
                                i_frame
                            ]
                        if (
                            self.frames_metadata is not None
                            and len(self.frames_metadata.count_time) > 0
                        ):
                            header["CountTime"] = self.frames_metadata.count_time[
                                i_frame
                            ]

                        edf_writer = fabio.edfimage.EdfImage(
                            data=frame,
                            header=header,
                        )
                        edf_writer.write(file_path)
                elif scheme in ("hdf5", "silx"):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with h5py.File(file_path, mode="a") as h5s:
                        if data_path in h5s:
                            h5s[data_path][()] = frame
                        else:
                            h5s[data_path] = frame
                        h5s[data_path].attrs["interpretation"] = "image"
                else:
                    raise ValueError(
                        f"scheme {scheme} is not handled for frames. Should be fabio, silx of hdf5"
                    )

        frames_indexes = [idx for idx, _ in self.frames.items()]
        if self.frames_metadata is not None:
            for url, idx in zip(self.metadata_output_urls, frames_indexes):
                idx_zfill4 = str(idx).zfill(4)
                metadata_grp_path = self._format_data_path(
                    url.data_path(), index=idx, index_zfill4=idx_zfill4
                )
                file_path = self._format_file_path(
                    url.file_path(),
                    index=idx,
                    index_zfill4=idx_zfill4,
                )
                scheme = url.scheme()
                for (
                    metadata_name,
                    metadata_values,
                ) in self.frames_metadata.to_dict().items():
                    # warning: for now we only handle list (of count_time and machine_current)
                    if len(metadata_values) == 0:
                        continue
                    else:
                        # save metadata
                        if scheme in ("hdf5", "silx"):
                            with h5py.File(file_path, mode="a") as h5s:
                                metadata_path = "/".join(
                                    [metadata_grp_path, metadata_name]
                                )
                                if metadata_path in h5s:
                                    del h5s[metadata_path]
                                h5s[metadata_path] = metadata_values
                                unit = None
                                if metadata_name == ReducedFramesInfos.COUNT_TIME_KEY:
                                    unit = _ureg.second
                                elif (
                                    metadata_name
                                    == ReducedFramesInfos.MACHINE_ELECT_CURRENT_KEY
                                ):
                                    unit = _ureg.ampere
                                if unit is not None:
                                    h5s[metadata_path].attrs["units"] = str(unit)

                        else:
                            raise ValueError(
                                f"scheme {scheme} is not handled for frames metadata. Should be silx of hdf5"
                            )

    @staticmethod
    def _format_file_path(file_path: str | None, index, index_zfill4):
        if file_path is None:
            return file_path
        if not os.path.isabs(file_path):
            raise ValueError("url should contain file_path as an absolute path")
        return file_path.format(
            index=str(index),
            index_zfill4=index_zfill4,
        )

    @staticmethod
    def _format_data_path(data_path: str | None, index, index_zfill4):
        if data_path is None:
            return data_path
        return data_path.format(
            index_zfill4=index_zfill4,
            index=index,
        )
