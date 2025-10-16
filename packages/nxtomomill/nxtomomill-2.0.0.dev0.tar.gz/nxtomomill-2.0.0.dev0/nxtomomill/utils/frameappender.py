# coding: utf-8

from __future__ import annotations

import os

import h5py
import h5py._hl.selections as selection
import numpy
from h5py import h5s as h5py_h5s
from silx.io.url import DataUrl
from silx.io.utils import get_data, h5py_read_dataset
from tomoscan.esrf.scan.utils import cwd_context
from tomoscan.io import HDF5File
from silx.io.utils import open as open_hdf5

from nxtomo.io import to_target_rel_path
from nxtomomill.utils.h5pyutils import from_data_url_to_virtual_source
from nxtomomill.utils.hdf5 import DatasetReader


__all__ = [
    "FrameAppender",
]


class FrameAppender:
    """
    Class to insert 2D frame(s) to an existing dataset
    """

    def __init__(
        self,
        data: numpy.ndarray | DataUrl,
        file_path,
        data_path,
        where,
        logger=None,
    ):
        if where not in ("start", "end"):
            raise ValueError("`where` should be `start` or `end`")

        if not isinstance(
            data, (DataUrl, numpy.ndarray, list, tuple, h5py.VirtualSource)
        ):
            raise TypeError(
                f"data should be an instance of DataUrl or a numpy array not {type(data)}"
            )

        self.data = data
        self.file_path = os.path.abspath(file_path)
        self.data_path = data_path
        self.where = where
        self.logger = logger

    def process(self) -> None:
        """
        main function. Will start the insertion of frame(s)
        """
        with HDF5File(self.file_path, mode="a") as h5s:
            if self.data_path in h5s:
                self._add_to_existing_dataset(h5s)
            else:
                self._create_new_dataset(h5s)
            if self.logger:
                self.logger.info(f"data added to {self.data_path}@{self.file_path}")

    def _add_to_existing_virtual_dataset(self, h5s):
        if (
            h5py.version.hdf5_version_tuple[0] <= 1
            and h5py.version.hdf5_version_tuple[1] < 12
        ):
            if self.logger:
                self.logger.warning(
                    "You are working on virtual dataset"
                    "with a hdf5 version < 12. Frame "
                    "you want to change might be "
                    "modified depending on the working "
                    "directory without notifying."
                    "See https://github.com/silx-kit/silx/issues/3277"
                )
        if isinstance(self.data, h5py.VirtualSource):
            self.__insert_virtual_source_in_vds(h5s=h5s, new_virtual_source=self.data)

        elif isinstance(self.data, DataUrl):
            if self.logger is not None:
                self.logger.debug(
                    f"Update virtual dataset: {self.data_path}@{self.file_path}"
                )
            # store DataUrl in the current virtual dataset
            url = self.data

            def check_dataset(dataset_frm_url):
                data_need_reshape = False
                """check if the dataset is valid or might need a reshape"""
                if dataset_frm_url.ndim not in (2, 3):
                    raise ValueError(f"{url.path()} should point to 2D or 3D dataset ")
                if dataset_frm_url.ndim == 2:
                    new_shape = 1, dataset_frm_url.shape[0], dataset_frm_url.shape[1]
                    if self.logger is not None:
                        self.logger.info(
                            f"reshape provided data to 3D (from {dataset_frm_url.shape} to {new_shape})"
                        )
                    data_need_reshape = True
                return data_need_reshape

            loaded_dataset = None
            if url.data_slice() is None:
                # case we can avoid to load the data in memory
                with DatasetReader(url) as data_frm_url:
                    data_need_reshape = check_dataset(data_frm_url)
                # FIXME: avoid keeping some file open. not clear why this is needed
                data_frm_url = None
            else:
                data_frm_url = get_data(url)
                data_need_reshape = check_dataset(data_frm_url)
                loaded_dataset = data_frm_url

            if url.data_slice() is None and not data_need_reshape:
                # case we can avoid to load the data in memory
                with DatasetReader(self.data) as data_frm_url:
                    self.__insert_url_in_vds(h5s, url, data_frm_url)
                # FIXME: avoid keeping some file open. not clear why this is needed
                data_frm_url = None
            else:
                if loaded_dataset is None:
                    data_frm_url = get_data(url)
                else:
                    data_frm_url = loaded_dataset
                self.__insert_url_in_vds(h5s, url, data_frm_url)
        else:
            raise TypeError(
                "Provided data is a numpy array when given"
                "dataset path is a virtual dataset. "
                "You must store the data somewhere else "
                "and provide a DataUrl"
            )

    def __insert_url_in_vds(self, h5s, url, data_frm_url):
        if data_frm_url.ndim == 2:
            dim_2, dim_1 = data_frm_url.shape
            data_frm_url = data_frm_url.reshape(1, dim_2, dim_1)
        elif data_frm_url.ndim == 3:
            _, dim_2, dim_1 = data_frm_url.shape
        else:
            raise ValueError("data to had is expected to be 2 or 3 d")

        new_virtual_source = h5py.VirtualSource(
            path_or_dataset=url.file_path(),
            name=url.data_path(),
            shape=data_frm_url.shape,
        )

        if url.data_slice() is not None:
            # in the case we have to process to a FancySelection
            with open_hdf5(os.path.abspath(url.file_path())) as h5sd:
                dst = h5sd[url.data_path()]
                sel = selection.select(
                    h5sd[url.data_path()].shape, url.data_slice(), dst
                )
                new_virtual_source.sel = sel
        self.__insert_virtual_source_in_vds(
            h5s=h5s, new_virtual_source=new_virtual_source, relative_path=True
        )

    def __insert_virtual_source_in_vds(
        self, h5s, new_virtual_source: h5py.VirtualSource, relative_path=True
    ):
        if not isinstance(new_virtual_source, h5py.VirtualSource):
            raise TypeError(
                f"{new_virtual_source} is expected to be an instance of h5py.VirtualSource and not {type(new_virtual_source)}"
            )
        if not len(new_virtual_source.shape) == 3:
            raise ValueError(
                f"virtual source shape is expected to be 3D and not {len(new_virtual_source.shape)}D."
            )
        # preprocess virtualSource to insure having a relative path
        if relative_path:
            vds_file_path = to_target_rel_path(new_virtual_source.path, self.file_path)
            new_virtual_source_sel = new_virtual_source.sel
            new_virtual_source = h5py.VirtualSource(
                path_or_dataset=vds_file_path,
                name=new_virtual_source.name,
                shape=new_virtual_source.shape,
                dtype=new_virtual_source.dtype,
            )
            new_virtual_source.sel = new_virtual_source_sel

        virtual_sources_len = []
        virtual_sources = []
        # we need to recreate the VirtualSource they are not
        # store or available from the API
        for vs_info in h5s[self.data_path].virtual_sources():
            length, vs = self._recreate_vs(vs_info=vs_info, vds_file=self.file_path)
            virtual_sources.append(vs)
            virtual_sources_len.append(length)

        n_frames = h5s[self.data_path].shape[0] + new_virtual_source.shape[0]
        data_type = h5s[self.data_path].dtype

        if self.where == "start":
            virtual_sources.insert(0, new_virtual_source)
            virtual_sources_len.insert(0, new_virtual_source.shape[0])
        else:
            virtual_sources.append(new_virtual_source)
            virtual_sources_len.append(new_virtual_source.shape[0])

        # create the new virtual dataset
        layout = h5py.VirtualLayout(
            shape=(
                n_frames,
                new_virtual_source.shape[-2],
                new_virtual_source.shape[-1],
            ),
            dtype=data_type,
        )
        last = 0
        for v_source, vs_len in zip(virtual_sources, virtual_sources_len):
            layout[last : vs_len + last] = v_source
            last += vs_len
        if self.data_path in h5s:
            del h5s[self.data_path]
        h5s.create_virtual_dataset(self.data_path, layout)

    def _add_to_existing_none_virtual_dataset(self, h5s):
        """
        for now when we want to add data *to a none virtual dataset*
        we always duplicate data if provided from a DataUrl.
        We could create a virtual dataset as well but seems to complicated for
        a use case that we don't really have at the moment.

        :param h5s:
        """
        if self.logger is not None:
            self.logger.debug("Update dataset: {entry}@{file_path}")
        if isinstance(self.data, (numpy.ndarray, list, tuple)):
            new_data = self.data
        else:
            url = self.data
            new_data = get_data(url)

        if isinstance(new_data, numpy.ndarray):
            if not new_data.shape[1:] == h5s[self.data_path].shape[1:]:
                raise ValueError(
                    f"Data shapes are incoherent: {new_data.shape} vs {h5s[self.data_path].shape}"
                )

            new_shape = (
                new_data.shape[0] + h5s[self.data_path].shape[0],
                new_data.shape[1],
                new_data.shape[2],
            )
            data_to_store = numpy.empty(new_shape)
            if self.where == "start":
                data_to_store[: new_data.shape[0]] = new_data
                data_to_store[new_data.shape[0] :] = h5py_read_dataset(
                    h5s[self.data_path]
                )
            else:
                data_to_store[: h5s[self.data_path].shape[0]] = h5py_read_dataset(
                    h5s[self.data_path]
                )
                data_to_store[h5s[self.data_path].shape[0] :] = new_data
        else:
            assert isinstance(
                self.data, (list, tuple)
            ), f"Unmanaged data type {type(self.data)}"
            o_data = h5s[self.data_path]
            o_data = list(h5py_read_dataset(o_data))
            if self.where == "start":
                new_data.extend(o_data)
                data_to_store = numpy.asarray(new_data)
            else:
                o_data.extend(new_data)
                data_to_store = numpy.asarray(o_data)

        del h5s[self.data_path]
        h5s[self.data_path] = data_to_store

    def _add_to_existing_dataset(self, h5s):
        """Add the frame to an existing dataset"""
        if h5s[self.data_path].is_virtual:
            self._add_to_existing_virtual_dataset(h5s=h5s)
        else:
            self._add_to_existing_none_virtual_dataset(h5s=h5s)

    def _create_new_dataset(self, h5s):
        """
        needs to create a new dataset. In this case the policy is:
           - if a DataUrl is provided then we create a virtual dataset
           - if a numpy array is provided then we create a 'standard' dataset
        """

        if isinstance(self.data, DataUrl):
            url = self.data

            url_file_path = to_target_rel_path(url.file_path(), self.file_path)
            url = DataUrl(
                file_path=url_file_path,
                data_path=url.data_path(),
                scheme=url.scheme(),
                data_slice=url.data_slice(),
            )

            with cwd_context(os.path.dirname(self.file_path)):
                vs, vs_shape, data_type = from_data_url_to_virtual_source(url)
                layout = h5py.VirtualLayout(shape=vs_shape, dtype=data_type)
                layout[:] = vs
                h5s.create_virtual_dataset(self.data_path, layout)

        elif isinstance(self.data, h5py.VirtualSource):
            virtual_source = self.data
            layout = h5py.VirtualLayout(
                shape=virtual_source.shape,
                dtype=virtual_source.dtype,
            )

            vds_file_path = to_target_rel_path(virtual_source.path, self.file_path)
            virtual_source_rel_path = h5py.VirtualSource(
                path_or_dataset=vds_file_path,
                name=virtual_source.name,
                shape=virtual_source.shape,
                dtype=virtual_source.dtype,
            )
            virtual_source_rel_path.sel = virtual_source.sel
            layout[:] = virtual_source_rel_path
            # convert path to relative
            h5s.create_virtual_dataset(self.data_path, layout)
        elif not isinstance(self.data, numpy.ndarray):
            raise TypeError(
                f"self.data should be an instance of DataUrl, a numpy array or a VirtualSource. Not {type(self.data)}"
            )
        else:
            h5s[self.data_path] = self.data

    @staticmethod
    def _recreate_vs(vs_info, vds_file):
        """Simple util to retrieve a h5py.VirtualSource from virtual source
        information.

        to understand clearly this function you might first have a look at
        the use case exposed in issue:
        https://gitlab.esrf.fr/tomotools/nxtomomill/-/issues/40
        """
        with cwd_context(os.path.dirname(vds_file)):
            dataset_file_path = vs_info.file_name
            # in case the virtual source is in the same file
            if dataset_file_path == ".":
                dataset_file_path = vds_file

            with open_hdf5(dataset_file_path) as vs_node:
                dataset = vs_node[vs_info.dset_name]
                select_bounds = vs_info.vspace.get_select_bounds()
                left_bound = select_bounds[0]
                right_bound = select_bounds[1]
                length = right_bound[0] - left_bound[0] + 1
                # warning: for now step is not managed with virtual
                # dataset

                virtual_source = h5py.VirtualSource(
                    vs_info.file_name,
                    vs_info.dset_name,
                    shape=dataset.shape,
                )
                # here we could provide dataset but we won't to
                # insure file path will be relative.
                type_code = vs_info.src_space.get_select_type()
                # check for unlimited selections in case where selection is regular
                # hyperslab, which is the only allowed case for h5s.UNLIMITED to be
                # in the selection
                if (
                    type_code == h5py_h5s.SEL_HYPERSLABS
                    and vs_info.src_space.is_regular_hyperslab()
                ):
                    (
                        source_start,
                        stride,
                        count,
                        block,
                    ) = vs_info.src_space.get_regular_hyperslab()
                    source_end = source_start[0] + length

                    sel = selection.select(
                        dataset.shape,
                        slice(source_start[0], source_end),
                        dataset=dataset,
                    )
                    virtual_source.sel = sel

                return (
                    length,
                    virtual_source,
                )
