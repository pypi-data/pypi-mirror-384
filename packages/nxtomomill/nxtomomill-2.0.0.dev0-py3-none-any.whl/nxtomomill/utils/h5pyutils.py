# coding: utf-8

"""
module to define some converter utils function
"""


import h5py
import h5py._hl.selections as selection
from silx.io.url import DataUrl
from silx.io.utils import open as open_hdf5

__all__ = ["from_data_url_to_virtual_source", "from_virtual_source_to_data_url"]


def from_data_url_to_virtual_source(url: DataUrl) -> tuple:
    """
    :param url: url to be converted to a virtual source. It must target a 2D detector
    :return: (h5py.VirtualSource, tuple(shape of the virtual source), numpy.drype: type of the dataset associated with the virtual source)
    """
    if not isinstance(url, DataUrl):
        raise TypeError(
            f"url is expected to be an instance of DataUrl and not {type(url)}"
        )

    with open_hdf5(url.file_path()) as o_h5s:
        original_data_shape = o_h5s[url.data_path()].shape
        data_type = o_h5s[url.data_path()].dtype
        if len(original_data_shape) == 2:
            original_data_shape = (
                1,
                original_data_shape[0],
                original_data_shape[1],
            )

        vs_shape = original_data_shape
        if url.data_slice() is not None:
            vs_shape = (
                url.data_slice().stop - url.data_slice().start,
                original_data_shape[-2],
                original_data_shape[-1],
            )

    vs = h5py.VirtualSource(
        url.file_path(), url.data_path(), shape=vs_shape, dtype=data_type
    )

    if url.data_slice() is not None:
        vs.sel = selection.select(original_data_shape, url.data_slice())
    return vs, vs_shape, data_type


def from_virtual_source_to_data_url(vs: h5py.VirtualSource) -> DataUrl:
    if not isinstance(vs, h5py.VirtualSource):
        raise TypeError(
            f"vs is expected to be an instance of h5py.VirtualSorce and not {type(vs)}"
        )
    url = DataUrl(file_path=vs.path, data_path=vs.name, scheme="silx")
    return url
