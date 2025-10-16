# coding: utf-8

"""An :class:`.Enum` class with additional features."""

from __future__ import annotations
import logging
import os
from datetime import datetime

import numpy
from silx.io.url import DataUrl
from silx.io.utils import get_data
from silx.io.utils import open as open_hdf5
from silx.utils.deprecation import deprecated
from silx.utils.enum import Enum as _Enum
from tomoscan.esrf.scan.utils import cwd_context
from tomoscan.io import HDF5File

from nxtomo.nxobject.nxdetector import ImageKey
from nxtomo.utils.frameappender import FrameAppender
from nxtomo.application.nxtomo import NXtomo

try:
    import hdf5plugin  # noqa F401
except ImportError:
    pass
import uuid
from typing import Iterable

from silx.io.utils import h5py_read_dataset


__all__ = [
    "embed_url",
    "FileExtension",
    "get_file_name",
    "get_tuple_of_keys_from_cmd",
    "is_nx_tomo_entry",
    "add_dark_flat_nx_file",
    "change_image_key_control",
    "str_datetime_to_numpy_datetime64",
    "strip_extension",
]


def embed_url(url: DataUrl, output_file: str) -> DataUrl:
    """
    Create a dataset under duplicate_data and with a random name
    to store it

    :param DataUrl url: dataset to be copied
    :param output_file: where to store the dataset
    :param expected_type: some metadata to put in copied dataset attributes
    :param data: data loaded from url is already loaded
    """
    if not isinstance(url, DataUrl):
        return url
    elif url.file_path() == output_file:
        return url
    else:
        embed_data_path = "/".join(("/duplicate_data", str(uuid.uuid1())))
        with cwd_context(os.path.dirname(os.path.abspath(output_file))):
            with HDF5File(output_file, "a") as h5s:
                h5s[embed_data_path] = get_data(url)
                h5s[embed_data_path].attrs["original_url"] = url.path()
            return DataUrl(
                file_path=output_file, data_path=embed_data_path, scheme="silx"
            )


class FileExtension(_Enum):
    H5 = ".h5"
    HDF5 = ".hdf5"
    NX = ".nx"
    NXS = ".nxs"


def get_file_name(file_name, extension, check=True):
    """
    set the given extension

    :param file_name: name of the file
    :param extension: extension to give
    :param check: if check, already check if the file as one of the
                       '_FileExtension'
    """
    if isinstance(extension, str):
        extension = FileExtension(extension.lower())
    assert isinstance(extension, FileExtension)
    if check:
        for item in FileExtension:
            if file_name.lower().endswith(item.value):
                return file_name
    return file_name + extension.value


def get_tuple_of_keys_from_cmd(cmd_value: str) -> tuple:
    """Return a tuple"""
    return tuple(cmd_value.split(","))


def is_nx_tomo_entry(file_path, entry):
    """

    :param file_path: hdf5 file path
    :param entry: entry to check
    :return: True if the entry is an NXTomo entry
    """
    if not os.path.exists(file_path):
        return False
    else:
        with open_hdf5(file_path) as h5s:
            if entry not in h5s:
                return False
            node = h5s[entry]
            return NXtomo.node_is_nxtomo(node)


def add_dark_flat_nx_file(
    file_path: str,
    entry: str,
    darks_start: numpy.ndarray | DataUrl | None = None,
    flats_start: numpy.ndarray | DataUrl | None = None,
    darks_end: numpy.ndarray | DataUrl | None = None,
    flats_end: numpy.ndarray | DataUrl | None = None,
    extras: dict | None = None,
    logger: None | logging.Logger = None,
    embed_data: bool = False,
):
    """
    This will get all data from entry@input_file and patch them with provided
    dark and / or flat(s).
    We consider the sequence as: dark, start_flat, projections, end_flat.

    Behavior regarding data type and target dataset:

    * if dataset at `entry` already exists:
        * if dataset at `entry` is a 'standard' dataset:
            * data will be loaded if necessary and `enrty` will be updated
        * if dataset at `entry` is a virtual dataset:
            * if `data` is a numpy array then we raise an error: the data should
              already be saved somewhere and you should provide a DataUrl
            * if `data` is a DataUrl then the virtual dataset is updated and
              a virtual source pointing to the
              DataUrl.file_path()@DataUrl.data_path() is added to the layout
    * if a new dataset `entry` need to be added:
        * if `data` is a numpy array then we create a new 'standard' Dataset
        * if `data` is a DataUrl then a new virtual dataset will be created

    note: Datasets `image_key`, `image_key_control`, `rotation_angle` and
    `count_time` will be copied each time.

    :param file_path: NXTomo file containing data to be patched
    :param entry: entry to be patched
    :param darks_start: (3D) numpy array containing the first dark serie if any
    :param flats_start: (3D) numpy array containing the first flat if any
    :param darks_end: (3D) numpy array containing dark the second dark serie if
                      any
    :param flats_end: (3D) numpy array containing the second flat if any
    :param extras: dictionary to specify some parameters for flats and dark
                   like rotation angle.
                   valid keys: 'start_dark', 'end_dark', 'start_flag',
                   'end_flag'.
                   Values should be a dictionary of 'NXTomo' keys with
                   values to be set instead of 'default values'.
                   Possible values are:
                   * `count_time`
                   * `rotation_angle`
    :param logger: object for logs
    :param embed_data: if True then each external data will be copy
                            under a 'duplicate_data' folder
    """
    if extras is None:
        extras = {}
    else:
        for key in extras:
            valid_extra_keys = ("darks_start", "darks_end", "flats_start", "flats_end")
            if key not in valid_extra_keys:
                raise ValueError(
                    f"{key} is not recognized. Valid values are {valid_extra_keys}"
                )

    if embed_data is True:
        darks_start = embed_url(darks_start, output_file=file_path)
        darks_end = embed_url(darks_end, output_file=file_path)
        flats_start = embed_url(flats_start, output_file=file_path)
        flats_end = embed_url(flats_end, output_file=file_path)
    else:
        for url in (darks_start, darks_end, flats_start, flats_end):
            if url is not None and isinstance(url, DataUrl):
                if isinstance(url.data_slice(), slice):
                    if url.data_slice().step not in (None, 1):
                        raise ValueError(
                            "When data is not embed slice `step`"
                            "must be None or 1. Other values are"
                            f"not handled. Failing url is {url}"
                        )

    # !!! warning: order of dark / flat treatments import
    data_names = "flats_start", "darks_end", "flats_end", "darks_start"
    datas = flats_start, darks_end, flats_end, darks_start
    keys_value = (
        ImageKey.FLAT_FIELD.value,
        ImageKey.DARK_FIELD.value,
        ImageKey.FLAT_FIELD.value,
        ImageKey.DARK_FIELD.value,
    )
    wheres = "start", "end", "end", "start"  # warning: order import

    for d_n, data, key, where in zip(data_names, datas, keys_value, wheres):
        if data is None:
            continue
        n_frames_to_insert = 1
        if isinstance(data, str):
            data = DataUrl(path=data)
        if isinstance(data, numpy.ndarray) and data.ndim == 3:
            n_frames_to_insert = data.shape[0]
        elif isinstance(data, DataUrl):
            with open_hdf5(data.file_path()) as h5s:
                if data.data_path() not in h5s:
                    raise KeyError(
                        f"Path given ({data.data_path()}) is not in {data.file_path}"
                    )
            data_node = get_data(data)
            if data_node.ndim == 3:
                n_frames_to_insert = data_node.shape[0]
        else:
            raise TypeError(f"{type(data)} as input is not managed")

        if logger is not None:
            logger.info(f"insert {type(data)} frame of type {key} at the {where}")
        # update 'data' dataset
        data_path = os.path.join(entry, "instrument", "detector", "data")
        FrameAppender(
            data, file_path, data_path=data_path, where=where, logger=logger
        ).process()
        # update image-key and image_key_control (we are not managing the
        # 'alignment projection here so values are identical')
        ik_path = os.path.join(entry, "instrument", "detector", "image_key")
        ikc_path = os.path.join(entry, "instrument", "detector", "image_key_control")
        for path in (ik_path, ikc_path):
            FrameAppender(
                [key] * n_frames_to_insert,
                file_path,
                data_path=path,
                where=where,
                logger=logger,
            ).process()

        # add 'other' necessaries key:
        count_time_path = os.path.join(
            entry,
            "instrument",
            "detector",
            "count_time",
        )
        rotation_angle_path = os.path.join(entry, "sample", "rotation_angle")
        x_translation_path = os.path.join(entry, "sample", "x_translation")
        translation_y_path = os.path.join(entry, "sample", "translation_y")
        translation_z_path = os.path.join(entry, "sample", "translation_z")
        control_data_path = os.path.join(entry, "control", "data")
        data_key_paths = (
            count_time_path,
            rotation_angle_path,
            x_translation_path,
            translation_y_path,
            translation_z_path,
            control_data_path,
        )
        mandatory_keys = (
            "count_time",
            "rotation_angle",
        )
        optional_keys = (
            "x_translation",
            "translation_y",
            "translation_z",
            "control/data",
        )

        data_keys = tuple(list(mandatory_keys) + list(optional_keys))

        for data_key, data_key_path in zip(data_keys, data_key_paths):
            data_to_insert = None
            if d_n in extras and data_key in extras[d_n]:
                provided_value = extras[d_n][data_key]
                if isinstance(provided_value, Iterable):
                    if len(provided_value) != n_frames_to_insert:
                        raise ValueError(
                            "Given value to store from extras has"
                            f" incoherent length({len(provided_value)}) compare to "
                            f"the number of frame to save ({n_frames_to_insert})"
                        )
                    else:
                        data_to_insert = provided_value
                else:
                    try:
                        data_to_insert = [provided_value] * n_frames_to_insert
                    except Exception as e:
                        logger.error(f"Fail to create data to insert. Error is {e}")
                        return
            else:
                # get default values
                def get_default_value(location, where_):
                    with open_hdf5(file_path) as h5s:
                        if location not in h5s:
                            return None
                        existing_data = h5s[location]
                        if where_ == "start":
                            return existing_data[0]
                        else:
                            return existing_data[-1]

                try:
                    default_value = get_default_value(data_key_path, where)
                except Exception:
                    default_value = None
                if default_value is None:
                    msg = f"Unable to define a default value for {data_key_path}. Location empty in {file_path}"
                    if data_key in mandatory_keys:
                        raise ValueError(msg)
                    elif logger:
                        logger.warning(msg)
                    continue
                elif logger:
                    logger.debug(
                        f"No value(s) provided for {data_key_path}. Extract some default value ({default_value})."
                    )
                data_to_insert = [default_value] * n_frames_to_insert

            if data_to_insert is not None:
                FrameAppender(
                    data_to_insert,
                    file_path,
                    data_path=data_key_path,
                    where=where,
                    logger=logger,
                ).process()


@deprecated(replacement="_FrameAppender", since_version="0.5.0")
def _insert_frame_data(data, file_path, data_path, where, logger=None):
    """
    This function is used to insert some frame(s) (numpy 2D or 3D to an
    existing dataset. Before the existing array or After.

    :param data:
    :param file_path:
    :param data_path: If the path point to a virtual dataset them this one
                      will be updated but data should be a DataUrl. Of the
                      same shape. Else we will update the data_path by
                      extending the dataset.
    :param where:
    :raises TypeError: In the case the data type and existing data_path are
                       incompatible.
    """
    fa = FrameAppender(
        data=data, file_path=file_path, data_path=data_path, where=where, logger=logger
    )
    return fa.process()


def change_image_key_control(
    file_path: str,
    entry: str,
    frames_indexes: slice | Iterable,
    image_key_control_value: int | ImageKey,
    logger=None,
):
    """
    Will modify image_key and image_key_control values for the requested
    frames.

    :param file_path: path the nexus file
    :param entry: name of the entry to modify
    :param frames_indexes: index of the frame for which we want to modify
                           the image key
    :param image_key_control_value:
    :param logging.Logger logger: logger
    """
    if not isinstance(frames_indexes, (Iterable, slice)):
        raise TypeError("`frame_indexes` should be an instance of Iterable slice")
    if logger:
        logger.info(
            "Update frames {frames_indexes} to"
            "{image_key_control_value} of {entry}@{file_path}"
            "".format(
                frames_indexes=frames_indexes,
                image_key_control_value=image_key_control_value,
                entry=entry,
                file_path=file_path,
            )
        )

    image_key_control_value = ImageKey(image_key_control_value)
    with HDF5File(file_path, mode="a") as h5s:
        node = h5s[entry]
        image_keys_path = "/".join(("instrument", "detector", "image_key"))
        image_keys = h5py_read_dataset(node[image_keys_path])
        image_keys_control_path = "/".join(
            ("instrument", "detector", "image_key_control")
        )
        image_keys_control = h5py_read_dataset(node[image_keys_control_path])
        # filter frame indexes
        if isinstance(frames_indexes, slice):
            step = frames_indexes.step
            if step is None:
                step = 1
            stop = frames_indexes.stop
            if stop in (None, -1):
                stop = len(image_keys)
            frames_indexes = list(range(frames_indexes.start, stop, step))
        frames_indexes = list(
            filter(lambda x: 0 <= x <= len(image_keys_control), frames_indexes)
        )
        # manage image_key_control
        image_keys_control[frames_indexes] = image_key_control_value.value
        node[image_keys_control_path][:] = image_keys_control
        # manage image_key. In this case we should get rid of Alignment values
        # and replace it by Projection values
        image_key_value = image_key_control_value
        if image_key_value is ImageKey.ALIGNMENT:
            image_key_value = ImageKey.PROJECTION
        image_keys[frames_indexes] = image_key_value.value
        node[image_keys_path][:] = image_keys


def str_datetime_to_numpy_datetime64(my_datetime: str | datetime) -> numpy.datetime64:
    # numpy deprecates time zone awarness conversion to numpy.datetime64.
    # so we remove the time zone info.
    if isinstance(my_datetime, str):
        datetime_as_datetime = datetime.fromisoformat(my_datetime)
    elif isinstance(my_datetime, datetime):
        datetime_as_datetime = my_datetime
    else:
        raise TypeError(
            f"my_datetime is expected to be a str or an instance of datetime. Not {type(my_datetime)}"
        )

    datetime_as_utc_datetime = datetime_as_datetime.astimezone(None)
    tz_free_datetime_as_datetime = datetime_as_utc_datetime.replace(tzinfo=None)
    return numpy.datetime64(tz_free_datetime_as_datetime).astype("<M8[ms]")


def strip_extension(filename, logger=None):
    if filename.endswith((".nx", ".h5")):
        return filename[:-3]
    elif filename.endswith(".hdf5"):
        return filename[:-5]
    else:
        if logger is not None:
            logger.warning(f"Unusual file name {filename} has no known postfix")
        return filename
