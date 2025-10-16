# coding: utf-8
"""
module to define a multi-tomo acquistion (also know as pco-tomo)
"""
from __future__ import annotations

import logging

from silx.io.url import DataUrl
from silx.utils.proxy import docstring
from silx.utils.deprecation import deprecated

from nxtomo.application.nxtomo import NXtomo

try:
    from nxtomo.utils.NXtomoSplitter import NXtomoSplitter
except ImportError:
    from nxtomo.utils.detectorsplitter import (
        NXtomoDetectorDataSplitter as NXtomoSplitter,
    )
from nxtomo.nxobject.nxdetector import ImageKey

from nxtomomill.converter.hdf5.acquisition.baseacquisition import EntryReader
from nxtomomill.converter.hdf5.acquisition.standardacquisition import (
    StandardAcquisition,
)
from nxtomomill.models.h52nx._acquisitionstep import AcquisitionStep
from nxtomomill.io.config import TomoHDF5Config

_logger = logging.getLogger(__name__)

__all__ = [
    "MultiTomoAcquisition",
]


class MultiTomoAcquisition(StandardAcquisition):
    """
    A multitomo is an acquisition that we want to split into several NXtomos.

    It is contain in a bliss scan and looks like the following at bliss side:

    * scan "description", title can be tomo:pcotomo ro tomo:multitomo for example
    * Optional scan dark
    * Optional scan flat
    * scan "projections"
    * Optional scan flat

    The scan "projections" contains several "tomo" with a parameter evolving with time like heat or pressure.
    The idea is that we want to split those into several NXtomo.
    Those NXtomo must duplicate dark and flat scans
    For example if scan "projections" contains nb_loop = 2 and nb_loop = 3 we must create nb_loop*nb_loop == 6 NXtomo as output.

    Split of those can are done in postprocessing on the to_NXtomos function
    """

    def __init__(
        self,
        root_url: DataUrl | None,
        configuration: TomoHDF5Config,
        detector_sel_callback,
        start_index,
    ):
        super().__init__(
            root_url=root_url,
            configuration=configuration,
            detector_sel_callback=detector_sel_callback,
            start_index=start_index,
        )
        self._nb_loop = None
        self._nb_tomo = None
        self._nb_turns = None
        self._entries_to_split = set()  # set of URL as str

    def _preprocess_registered_entries(self):
        # those must be defined before calling super because the super will call then `_preprocess_registered_entry`
        self._nb_loop = None
        self._nb_tomo = None
        self._nb_turns = None
        self._entries_to_split = set()
        super()._preprocess_registered_entries()

    def _read_nb_loop(self, entry_url: DataUrl):
        return self.get_nb_loop(entry_url) or self.get_nb_loop(self.root_url)

    def _read_nb_tomo(self, entry_url: DataUrl):
        return self.get_nb_tomo(entry_url) or self.get_nb_tomo(self.root_url)

    def _read_nb_turns(self, entry_url: DataUrl):
        return self.get_nb_turns(entry_url) or self.get_nb_turns(self.root_url)

    def _preprocess_registered_entry(self, entry_url, type_):
        super()._preprocess_registered_entry(entry_url=entry_url, type_=type_)
        if type_ is AcquisitionStep.PROJECTION:
            # nb loop parameter must be present only on projection entries
            nb_loop = self._read_nb_loop(entry_url=entry_url)
            if (
                nb_loop is not None
            ):  # at this moment 02/2022 nb_loop is only defined on projection type
                if self._nb_loop is None or self._nb_loop == nb_loop:
                    self._nb_loop = nb_loop
                    self._entries_to_split.add(entry_url.path())
                else:
                    _logger.error(
                        f"Found entries with a different number of nb_loop: {entry_url.path()}"
                    )

            nb_tomo = self._read_nb_tomo(entry_url=entry_url)
            if (
                nb_tomo is not None
            ):  # at this moment 02/2022 nb_loop is only defined on projection type
                if self._nb_tomo is None or self._nb_tomo == nb_tomo:
                    self._nb_tomo = nb_tomo
                    self._entries_to_split.add(entry_url.path())
                else:
                    _logger.error(
                        f"Found entries with a different number of _nb_tomo: {entry_url.path()}"
                    )

            nb_turns = self._read_nb_turns(entry_url=entry_url)
            if nb_turns is not None:
                if self._nb_turns is None or self._nb_turns == nb_turns:
                    self._nb_turns = nb_turns
                    self._entries_to_split.add(entry_url.path())
                else:
                    _logger.error(
                        f"Found entries with a different number of nb_turns: {entry_url.path()}"
                    )

    def get_nb_loop(self, url) -> int | None:
        with EntryReader(url) as entry:
            for path in self._NB_LOOP_PATH:
                if path in entry:
                    return entry[path][()]
        return None

    def get_nb_tomo(self, url) -> int | None:
        with EntryReader(url) as entry:
            for path in self._NB_TOMO_PATH:
                if path in entry:
                    return entry[path][()]
        return None

    def get_nb_turns(self, url) -> int | None:
        with EntryReader(url) as entry:
            for path in self._NB_TURNS_PATH:
                if path in entry:
                    return entry[path][()]
        return None

    def get_expected_nx_tomo(self):
        # the number of expected NXtomo is saved with projection
        # and not with the init title. This is why it but be computed later
        return 0

    @deprecated(
        replacement="get_multitomo_version",
        reason="rename pcotomo to multitomo",
        since_version="1.2",
    )
    def get_pcotomo_version(self, url: DataUrl):
        return self.get_multitomo_version(url=url)

    def get_multitomo_version(self, url: DataUrl):
        """
        return the multitomo version according to the provider version (aka bliss)
        """
        with EntryReader(
            url=DataUrl(file_path=url.file_path(), data_path="/", scheme=url.scheme())
        ) as entry:
            if "creator_version" in entry.attrs:
                creator_version = entry.attrs["creator_version"]
                try:
                    full_version = creator_version.split("-")[0].split("+")[0]
                    major, minor, _ = full_version.split(".")
                except Exception as e:
                    _logger.warning(
                        f"Fail to convert creator_version ({creator_version}) to a valid version number. Error is {e}"
                    )
                    return None
                else:
                    if major == "0" or (major == "1" and int(minor) < 9):
                        return 1
                    else:
                        return 2
        return None

    @docstring(StandardAcquisition)
    def to_NXtomos(
        self, request_input, input_callback, check_tomo_n: bool = True
    ) -> tuple:
        multitomo_version = self.get_multitomo_version(url=self.root_url)
        if multitomo_version is None:
            multitomo_version = 2
            _logger.warning(
                f"No multi-tomo (also know as pco-tomo) version found. Try to convert it using the latest version (v{multitomo_version})"
            )
        if multitomo_version == 1:
            return self.to_NXtomos_multitomo_v1(
                request_input=request_input,
                input_callback=input_callback,
                check_tomo_n=check_tomo_n,
            )
        elif multitomo_version == 2:
            return self.to_NXtomos_multitomo_v2(
                request_input=request_input,
                input_callback=input_callback,
                check_tomo_n=check_tomo_n,
            )
        else:
            raise ValueError(
                f"{multitomo_version} version of the multi-tomo found. No handling defined for it"
            )

    @deprecated(
        replacement="to_NXtomos_multitomo_v2",
        reason="rename pcotomo to multitomo",
        since_version="1.2",
    )
    def to_NXtomos_pcotomo_v2(
        self, request_input, input_callback, check_tomo_n: bool = True
    ) -> tuple:
        return self.to_NXtomos_multitomo_v2(
            request_input=request_input,
            input_callback=input_callback,
            check_tomo_n=check_tomo_n,
        )

    def to_NXtomos_multitomo_v2(
        self, request_input, input_callback, check_tomo_n: bool = True
    ) -> tuple:
        """
        The second version of 'to_NXtomos' for the second way of storing multi-tomo information.
        In this version we expect to have:
        * nb_turns: number of NXtomo to generate
        * proj_n: number of projections per NXtomo
        * scan_range: rotation angle scope

        """
        nx_tomos = super().to_NXtomos(request_input, input_callback, check_tomo_n=False)
        if len(nx_tomos) == 0:
            return nx_tomos

        if self._nb_turns is None:
            error_msg = "unable to find nb_turns information to split the NXtomo"
            _logger.error(error_msg)
            raise ValueError(error_msg)

        # if we want to split the NXtomo from `nb_tomo` and `nb_loop`
        _logger.info(
            "apply split from `nb_turns` and `scan_range`. `start_angle_offset`, `angle_interval` and `n_tomo` will be ignored"
        )

        results = []
        for nx_tomo in nx_tomos:
            splitter = NXtomoSplitter(nx_tomo)
            projections_slices = self._get_projections_slices(nx_tomo)
            if len(projections_slices) > 1:
                # insure projections are contiguous otherwise we don't know how to split it.
                # not defined on the current design from bliss. should never happen
                raise ValueError("Expect all projections to be contiguous")
            elif len(projections_slices) == 0:
                raise ValueError("No projection found")
            else:
                results.extend(
                    splitter.split(
                        projections_slices[0],
                        nb_part=int(self._nb_turns),
                        tomo_n=self._get_tomo_n(),
                    )
                )

        if check_tomo_n:
            # if angle offset provided there is an hight probably this will mess up with the tomo_n, which is expected...
            self.check_tomo_n()

        return tuple(results)

    @deprecated(
        replacement="to_NXtomos_multitomo_v1",
        reason="rename pcotomo to multitomo",
        since_version="1.2",
    )
    def to_NXtomos_pcotomo_v1(
        self, request_input, input_callback, check_tomo_n: bool = True
    ) -> tuple:
        return self.to_NXtomos_multitomo_v1(
            request_input=request_input,
            input_callback=input_callback,
            check_tomo_n=check_tomo_n,
        )

    def to_NXtomos_multitomo_v1(
        self, request_input, input_callback, check_tomo_n: bool = True
    ) -> tuple:
        """
        The first version of 'to_NXtomos' for the first way of storing multitomo information.
        In this version we expect to have:
        * `nb_loop`: define the number of turn
        * `nb_tomo`: define the number of 'sequence' per turn. One sequence will generate one NXtomo

        """

        nx_tomos = super().to_NXtomos(request_input, input_callback, check_tomo_n=False)
        if len(nx_tomos) == 0:
            return nx_tomos

        # apply multitomo tomo_n, angle_interval and start_angle_offset
        # this will select if necessary a subset of the NXtomo to apply user requested offset
        angle_offset = self.configuration.multitomo_start_angle_offset
        scan_range = self.configuration.multitomo_scan_range
        if scan_range not in (180, 360):
            _logger.warning(
                f"strange angle_interval provided: {scan_range} when 180 or 360 expected"
            )
        results = []
        if angle_offset is not None:
            # if we want to split the NXtomo from angles and settings provided by the user:
            _logger.info(
                "apply filtering from `start_angle_offset`, `angle_interval` and `n_tomo`. `nb_tomo` and `nb_loop` will be ignored"
            )
            for nx_tomo in nx_tomos:
                for i_part in range(self.configuration.multitomo_n_nxtomo):
                    start_angle_offset = (angle_offset or 0) + (i_part * scan_range)
                    results.append(
                        NXtomo.sub_select_from_angle_offset(
                            nx_tomo=nx_tomo,
                            start_angle_offset=start_angle_offset,
                            angle_interval=scan_range,
                            shift_angles=False,
                            copy=True,
                        )
                    )
        else:
            # if we want to split the NXtomo from `nb_tomo` and `nb_loop`
            _logger.info(
                "apply split from `nb_tomo` and `nb_loop`. `start_angle_offset`, `angle_interval` and `n_tomo` will be ignored"
            )

            for nx_tomo in nx_tomos:
                splitter = NXtomoSplitter(nx_tomo)
                projections_slices = self._get_projections_slices(nx_tomo)
                if len(projections_slices) > 1:
                    # insure projections are contiguous otherwise we don't know how to split it.
                    # not defined on the current design from bliss. should never happen
                    raise ValueError("Expect all projections to be contiguous")
                elif len(projections_slices) == 0:
                    raise ValueError("No projection found")
                else:
                    results.extend(
                        splitter.split(
                            projections_slices[0],
                            nb_part=int(self._nb_loop * self._nb_tomo),
                        )
                    )

        if self.configuration.multitomo_shift_angles:
            _logger.info(f"will shift angle to 0-{scan_range}")
            results = [
                NXtomo.clamp_angles(
                    nx_tomo,
                    angle_range=scan_range,
                    offset=angle_offset or 0,
                    copy=False,
                    image_keys=(ImageKey.PROJECTION, ImageKey.ALIGNMENT),
                )
                for nx_tomo in results
            ]

        if angle_offset is not None and check_tomo_n:
            # if angle offset provided there is an hight probably this will mess up with the tomo_n, which is expected...
            self.check_tomo_n()

        return tuple(results)

    @staticmethod
    def _get_projections_slices(nx_tomo: NXtomo) -> tuple:
        """Return a tuple of slices for each group of contiguous projections"""
        if nx_tomo.instrument.detector.image_key_control is None:
            return ()

        res = []
        start_pos = -1
        browsing_projection = False
        for i_frame, image_key in enumerate(
            nx_tomo.instrument.detector.image_key_control
        ):
            image_key_value = ImageKey(image_key)
            if image_key_value is ImageKey.PROJECTION and not browsing_projection:
                browsing_projection = True
                start_pos = i_frame
            elif browsing_projection and image_key_value is not ImageKey.PROJECTION:
                res.append(slice(start_pos, i_frame, 1))
                start_pos = -1
                browsing_projection = False
        else:
            if browsing_projection is True:
                res.append(slice(start_pos, i_frame + 1, 1))
        return tuple(res)
