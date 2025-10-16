import contextlib
from os import path
import h5py
from silx.io.url import DataUrl
from silx.io.utils import open as hdf5_open


class _BaseReader(contextlib.AbstractContextManager):
    def __init__(self, url: DataUrl):
        if not isinstance(url, DataUrl):
            raise TypeError(f"url should be an instance of DataUrl. Not {type(url)}")
        if url.scheme() not in ("silx", "h5py"):
            raise ValueError("Valid scheme are silx and h5py")
        if url.data_slice() is not None:
            raise ValueError(
                "Data slices are not managed. Data path should "
                "point to a bliss node (h5py.Group)"
            )
        self._url = url
        self._file_handler = None

    def __exit__(self, *exc):
        return self._file_handler.close()


class DatasetReader(_BaseReader):
    """Context manager used to read a bliss node"""

    def __enter__(self):
        self._file_handler = hdf5_open(filename=self._url.file_path())
        entry = self._file_handler[self._url.data_path()]
        if not isinstance(entry, h5py.Dataset):
            raise ValueError(
                f"Data path ({self._url.path()}) should point to a dataset (h5py.Dataset)"
            )
        return entry


def get_data_sources(fname: str, data_path: str, recursive=True) -> dict:
    """
    Return the nested dict of data_sources.
     Key are (source) file path and keys are identical dict or data_path to the source

    :param recursive: If True then go trhough all linked files else won't 'solve' link
    """
    with hdf5_open(fname) as f:
        if data_path not in f:
            return None
        dptr = f[data_path]
        if not dptr.is_virtual:
            return {fname: data_path}
        sources = {}
        for vsource in dptr.virtual_sources():
            vsource_fname = path.normpath(
                path.join(path.dirname(dptr.file.filename), vsource.file_name)
            )
            if not path.isfile(vsource_fname):
                sources[vsource_fname] = None
            if recursive:
                sources[path.normpath(vsource_fname)] = get_data_sources(
                    vsource_fname, vsource.dset_name
                )
            else:
                sources[path.normpath(vsource_fname)] = vsource.dset_name

    return sources
