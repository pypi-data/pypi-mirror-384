from __future__ import annotations

import numpy
import logging

from silx.io.url import DataUrl

from tomoscan.esrf.scan.utils import get_series_slice, get_n_series

from nxtomo.application.nxtomo import NXtomo
from nxtomo.nxobject.nxdetector import ImageKey
from nxtomo.paths.nxtomo import get_paths as get_nexus_paths

from nxtomomill.converter.hdf5.acquisition.baseacquisition import BaseAcquisition
from nxtomomill.utils.utils import add_dark_flat_nx_file

_logger = logging.getLogger(__name__)

__all__ = [
    "ZSeriesDarkFlatCopy",
]


class ZSeriesDarkFlatCopy:
    """
    z-series version 3 can require to reuse dark-flat from a bliss scan done at the start or at the end of the series.

    This class is an helper to do this processing.
    """

    def __init__(
        self,
        series: list[BaseAcquisition],
        acquisition_to_nxtomo: dict[BaseAcquisition, tuple | None],
    ) -> None:
        """
        :param series: list of acquisition part of the series. **warning**: we expect this list to be ordered.
        :param acquisition_to_nxtomo: for each acquisition in "series" this dict can provide the nxtomo created during conversion. The value is expected to the None if the conversion failed or (file_path, data_path)

        .. warning:: even if list contains BaseAcquisition; those are sub_acquisitions of ZSeriesBaseAcquisition
        """
        for elmt in series:
            if not isinstance(elmt, BaseAcquisition):
                raise TypeError(
                    f"elmt is expected to be an instance of {BaseAcquisition}. Got {type(elmt)}"
                )

        self.series = series
        self.acquisition_to_nxtomo = acquisition_to_nxtomo

    @property
    def first_acquisition(self) -> BaseAcquisition:
        return self.series[0]

    @property
    def last_acquisition(self) -> BaseAcquisition:
        return self.series[-1]

    def run(self) -> None:
        darks_start_urls, flats_start_urls, darks_end_urls, flats_end_urls = (
            self.build_mapping_to_dark_flat_source()
        )
        edition_to_do = self.build_edition_to_do(
            darks_start_urls=darks_start_urls,
            flats_start_urls=flats_start_urls,
            darks_end_urls=darks_end_urls,
            flats_end_urls=flats_end_urls,
        )
        self.process_edition(editions_to_do=edition_to_do)

    def build_mapping_to_dark_flat_source(
        self,
    ) -> dict[tuple, dict[ImageKey, list[DataUrl]]]:
        """
        Build the list of DataUrl that can be used for copy.

        Output looks like:
        {
            file_path_first_nxtomo, data_path_first_nxtomo: {
                ImageKey.DARK_FIELD: (DataUrlSeries1, DataUrlSeries2),
                ImageKey.FLAT_FIELD: (DataUrlSeries1, ...),
            },
            file_path_last_nxtomo, data_path_last_nxtomo: {
                ImageKey.DARK_FIELD: (DataUrlSeries1, DataUrlSeries2),
                ImageKey.FLAT_FIELD: (DataUrlSeries1, ...),
            },
        }
        """
        darks_start_urls = []
        flats_start_urls = []
        darks_end_urls = []
        flats_end_urls = []
        # create darks_start_url and flats_start_url if possible
        first_nxtomos_infos = self.acquisition_to_nxtomo[self.first_acquisition][0]
        last_nxtomos_infos = self.acquisition_to_nxtomo[self.last_acquisition][-1]

        url_mapping = {}
        if first_nxtomos_infos is not None:
            url_mapping[first_nxtomos_infos] = {
                ImageKey.DARK_FIELD: darks_start_urls,
                ImageKey.FLAT_FIELD: flats_start_urls,
            }
        if last_nxtomos_infos is not None:
            url_mapping[last_nxtomos_infos] = {
                ImageKey.DARK_FIELD: darks_end_urls,
                ImageKey.FLAT_FIELD: flats_end_urls,
            }

        # build darks / flats urls
        for (file_path, data_path), image_key_to_urls in url_mapping.items():
            nxtomo_source = NXtomo().load(
                file_path=file_path,
                data_path=data_path,
            )
            for image_key, urls in image_key_to_urls.items():
                n_series = get_n_series(
                    image_key_values=nxtomo_source.instrument.detector.image_key_control,
                    image_key_type=image_key,
                )
                for i_series in range(n_series):
                    slice_source = get_series_slice(
                        image_key_values=nxtomo_source.instrument.detector.image_key_control,
                        image_key_type=image_key,
                        series_index=i_series,
                    )
                    if slice_source is None:
                        continue
                    detector_dataset_path = get_nexus_paths(version=None)
                    detector_data_path = "/".join(
                        (
                            data_path,
                            nxtomo_source.instrument.detector.path,
                            detector_dataset_path.nx_detector_paths.DATA,
                        )
                    )
                    urls.append(
                        DataUrl(
                            file_path=file_path,
                            data_path=detector_data_path,
                            data_slice=slice_source,
                            scheme="silx",
                        )
                    )

        return (
            tuple(darks_start_urls),
            tuple(flats_start_urls),
            tuple(darks_end_urls),
            tuple(flats_end_urls),
        )

    def build_edition_to_do(
        self,
        darks_start_urls: tuple[DataUrl],
        flats_start_urls: tuple[DataUrl],
        darks_end_urls: tuple[DataUrl],
        flats_end_urls: tuple[DataUrl],
    ) -> dict[tuple, dict]:
        """
        build all the edition to do to complete the dark and flat copy according to z-series v3 configuration.
        """
        # for each (final) acquisition register the different operation (edition) that needs to be done.
        editions_to_do: {tuple, dict} = {}
        # for each new entry (as a tuple of file_path, data_path) list the operations to execute

        for acquisition in self.series:
            if acquisition is None:
                # if conversion failed
                continue

            if acquisition._dark_at_start and (
                acquisition is not self.first_acquisition
            ):
                concatenate_dict(
                    editions_to_do,
                    {
                        nx_tomo: {"darks_start": darks_start_urls}
                        for nx_tomo in self.acquisition_to_nxtomo[acquisition]
                    },
                )
            if acquisition._flat_at_start and (
                acquisition is not self.first_acquisition
            ):
                concatenate_dict(
                    editions_to_do,
                    {
                        nx_tomo: {"flats_start": flats_start_urls}
                        for nx_tomo in self.acquisition_to_nxtomo[acquisition]
                    },
                )
            if acquisition._dark_at_end and (acquisition is not self.last_acquisition):
                concatenate_dict(
                    editions_to_do,
                    {
                        nx_tomo: {"darks_end": darks_end_urls}
                        for nx_tomo in self.acquisition_to_nxtomo[acquisition]
                    },
                )
            if acquisition._flat_at_end and (acquisition is not self.last_acquisition):
                concatenate_dict(
                    editions_to_do,
                    {
                        nx_tomo: {"flats_end": flats_end_urls}
                        for nx_tomo in self.acquisition_to_nxtomo[acquisition]
                    },
                )
        return editions_to_do

    def process_edition(
        self, editions_to_do: dict[tuple, dict], embed_dark_flat: bool = True
    ):
        """
        do edition
        """
        for nxtomo_to_edit, params_to_urls in editions_to_do.items():
            for param_name, urls in params_to_urls.items():
                edited_nxtomo_file_path, edited_nxtomo_data_path = nxtomo_to_edit
                for url in urls:
                    # if the file already contains the dark / flat
                    if (
                        url.file_path() == edited_nxtomo_file_path
                        and url.data_path() == edited_nxtomo_data_path
                    ):
                        continue
                    add_dark_flat_nx_file(
                        **{
                            param_name: url,
                            "file_path": edited_nxtomo_file_path,
                            "entry": edited_nxtomo_data_path,
                            "embed_data": embed_dark_flat,
                            "logger": _logger,
                        }
                    )


def concatenate_dict(dict_1: dict, dict_2: dict) -> None:
    """
    concatenate two dicts into dict_1
    """
    assert isinstance(dict_1, dict)
    assert isinstance(dict_2, dict)
    for key in dict_2.keys():
        if key in dict_1.keys():
            if isinstance(dict_1[key], dict) and isinstance(dict_2[key], dict):
                concatenate_dict(dict_1=dict_1[key], dict_2=dict_2[key])
            else:
                dict_1[key] = numpy.concatenate((dict_1[key], dict_2[key]))
        else:
            dict_1[key] = dict_2[key]
