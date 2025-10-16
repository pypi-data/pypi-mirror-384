# coding: utf-8

"""
Utils related to bliss-HDF5
"""

from __future__ import annotations
from typing import Iterable

import h5py
import numpy
from silx.io.url import DataUrl
from silx.io.utils import h5py_read_dataset
from silx.io.utils import open as open_hdf5

from nxtomo.nxobject.nxdetector import ImageKey
from nxtomomill.models.h52nx._acquisitionstep import AcquisitionStep
from nxtomomill.io.config import TomoHDF5Config

try:
    import hdf5plugin  # noqa F401
except ImportError:
    pass
import logging

_logger = logging.getLogger(__name__)


__all__ = [
    "has_valid_detector",
    "get_entry_type",
    "get_nx_detectors",
    "guess_nx_detector",
    "deduce_machine_current",
    "split_timestamps",
]


def has_valid_detector(node, detectors_names):
    """
    :return True if the node looks like a valid nx detector
    """
    for key in node.keys():
        if (
            "NX_class" in node[key].attrs
            and node[key].attrs["NX_class"] == "NXdetector"
        ):
            if detectors_names is None or key in detectors_names:
                return True
    return False


def get_entry_type(
    url: DataUrl, configuration: TomoHDF5Config
) -> AcquisitionStep | None:
    """
    :param url: bliss scan url to type
    :return: return the step of the acquisition or None if cannot find it.
    """
    if not isinstance(url, DataUrl):
        raise TypeError(f"DataUrl is expected. Not {type(url)}")
    if url.data_slice() is not None:
        raise ValueError(
            "url expect to provide a link to bliss scan. Slice " "are not handled"
        )

    def _get_entry_type_from_title(entry: h5py.Group):
        """
        try to determine the entry type from the title
        """
        try:
            title = h5py_read_dataset(entry["title"])
        except Exception:
            _logger.error(f"fail to find title for {entry.name}, skip this group")
            return None
        else:
            init_titles = list(configuration.init_titles)
            init_titles.extend(configuration.zseries_init_titles)
            init_titles.extend(configuration.multitomo_init_titles)
            init_titles.extend(configuration.back_and_forth_init_titles)

            step_titles = {
                AcquisitionStep.INITIALIZATION: init_titles,
                AcquisitionStep.DARK: configuration.dark_titles,
                AcquisitionStep.FLAT: configuration.flat_titles,
                AcquisitionStep.PROJECTION: configuration.projection_titles,
                AcquisitionStep.ALIGNMENT: configuration.alignment_titles,
            }

            for step, titles in step_titles.items():
                for title_start in titles:
                    if title.startswith(title_start):
                        return step
            return None

    def _get_entry_type_from_technique_img_key(entry: h5py.Group):
        """
        try to determine entry type from the scan/technique sub groups.
        If this is a flat then we expect to have a "flat" group. If this is a set of projection we expect to have a "proj" group.
        For now alignment / return are unfilled
        """
        group_technique = entry.get("technique", dict())
        if "image_key" not in group_technique:
            return None

        image_key = h5py_read_dataset(group_technique["image_key"])
        if image_key is None:
            return None
        else:
            try:
                image_key = ImageKey(image_key)
            except ValueError:
                _logger.error(f"unrecognized image key: '{image_key}'")
                return None
            else:
                connections = {
                    ImageKey.DARK_FIELD: AcquisitionStep.DARK,
                    ImageKey.FLAT_FIELD: AcquisitionStep.FLAT,
                    ImageKey.PROJECTION: AcquisitionStep.PROJECTION,
                    ImageKey.ALIGNMENT: AcquisitionStep.ALIGNMENT,
                }
                return connections.get(image_key, None)

    with open_hdf5(url.file_path()) as h5f:
        if url.data_path() not in h5f:
            raise ValueError(f"Provided path does not exists: {url}")
        entry = h5f[url.data_path()]
        if not isinstance(entry, h5py.Group):
            raise ValueError(
                f"Expected path is not related to a h5py.Group ({entry}) when expect to target a bliss entry."
            )
        return _get_entry_type_from_technique_img_key(
            entry
        ) or _get_entry_type_from_title(entry)


def get_nx_detectors(node: h5py.Group) -> tuple:
    """

    :param node: node to inspect
    :return: tuple of NXdetector (h5py.Group) contained in `node`
             (expected to be the `instrument` group)
    """
    if not isinstance(node, h5py.Group):
        raise TypeError("node should be an instance of h5py.Group")
    nx_detectors = []
    for _, subnode in node.items():
        if isinstance(subnode, h5py.Group) and "NX_class" in subnode.attrs:
            if subnode.attrs["NX_class"] == "NXdetector":
                if "data" in subnode and hasattr(subnode["data"], "ndim"):
                    if subnode["data"].ndim == 3:
                        nx_detectors.append(subnode)
    nx_detectors = sorted(nx_detectors, key=lambda det: det.name)
    return tuple(nx_detectors)


def guess_nx_detector(node: h5py.Group) -> tuple:
    """
    Try to guess what can be an nx_detector without using the "NXdetector"
    NX_class attribute. Expect to find a 3D dataset named 'data' under
    a subnode
    """
    if not isinstance(node, h5py.Group):
        raise TypeError("node should be an instance of h5py.Group")
    nx_detectors = []
    for _, subnode in node.items():
        if isinstance(subnode, h5py.Group) and "data" in subnode:
            if isinstance(subnode["data"], h5py.Dataset) and subnode["data"].ndim == 3:
                nx_detectors.append(subnode)

    nx_detectors = sorted(nx_detectors, key=lambda det: det.name)
    return tuple(nx_detectors)


def deduce_machine_current(timestamps: tuple, known_machine_current: dict) -> tuple:
    """
    :param known_machine_current: keys are timestamp. Value is machine current
    :param timestamps: timestamp for which we want to get machine current
    """
    if not isinstance(known_machine_current, dict):
        raise TypeError("known_machine_current is expected to be a dict")
    for elmt in timestamps:
        if not isinstance(elmt, numpy.datetime64):
            raise TypeError(
                f"Elements of timestamps are expected to be {numpy.datetime64} and not {type(elmt)}"
            )
    if len(known_machine_current) == 0:
        raise ValueError("known_machine_current should contain at least one element")
    for key, value in known_machine_current.items():
        if not isinstance(key, numpy.datetime64):
            raise TypeError(
                f"known_machine_current keys are expected to be instances of {numpy.datetime64} and not {type(key)}"
            )
        if not isinstance(value, (float, numpy.number)):
            raise TypeError(
                "known_machine_current values are expected to be instances of float"
            )

    # 1. Order **known** machine current by time stamps (key)
    known_machine_current = dict(sorted(known_machine_current.items()))
    known_timestamps = numpy.fromiter(
        known_machine_current.keys(),
        dtype="datetime64[ns]",
        count=len(known_machine_current),
    )
    known_machine_current_values = numpy.fromiter(
        known_machine_current.values(),
        dtype="float64",
        count=len(known_machine_current),
    )

    # 2. Sort the supplied timestamps
    timestamp_input_ordering = numpy.argsort(numpy.array(timestamps))
    timestamps_sorted = numpy.take_along_axis(
        numpy.array(timestamps), indices=timestamp_input_ordering, axis=0
    )

    timestamps_sorted = numpy.sort(numpy.array(timestamps, dtype="datetime64[ns]"))

    # 3. Convert to float for numpy.interp
    known_timestamps_float = known_timestamps.astype("float64")
    timestamps_float = timestamps_sorted.astype("float64")

    # 4. Interpolate the values
    interpolated_values = numpy.interp(
        timestamps_float, known_timestamps_float, known_machine_current_values
    )

    # 5. Reorder interpolated values to match the order of original timestamps
    ordered_interpolated_values = numpy.zeros_like(interpolated_values)
    for i, o_pos in enumerate(timestamp_input_ordering):
        ordered_interpolated_values[o_pos] = interpolated_values[i]
    return tuple(ordered_interpolated_values)


def split_timestamps(my_array: Iterable, n_part: int):
    """
    split given array into n_part (as equal as possible)
    :param Iterable my_array:
    """
    array_size = len(my_array)
    if array_size < n_part:
        yield my_array
    else:
        start = 0
        for _ in range(n_part):
            end = max(start + int(array_size / n_part) + 1, array_size)
            yield my_array[start:end]
            start = end


def group_series(acquisition, list_of_series: list) -> list:
    """
    :param ZSeriesBaseAcquisition acquisition:
    z-series version 2 and 3 are all defined in a separate sequence.
    So we need to aggregate for post processing based on there names.
    post-processing can be dark / flat copy to others NXtomo
    """
    for series in list_of_series:
        if series[0].is_part_of_same_series(acquisition):
            series.append(acquisition)
            return list_of_series
    list_of_series.append(
        [
            acquisition,
        ]
    )
    return list_of_series
