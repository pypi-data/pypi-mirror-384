from __future__ import annotations

from enum import Enum

from pydantic import (
    BaseModel,
    field_validator,
    field_serializer,
    ConfigDict,
    Field,
)

from silx.io.url import DataUrl

from ._acquisitionstep import AcquisitionStep

from nxtomomill.models.utils import filter_str_def
from nxtomomill.models.utils import (
    remove_parenthesis_or_brackets,
    convert_str_to_bool,
)


class FrameGroup(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, validate_by_name=True
    )

    url: DataUrl | None = None
    frame_type: AcquisitionStep = AcquisitionStep.PROJECTION
    copy_data: bool | None = Field(
        default=None,
        description="Should the frame dataset be copied or not. If not set will fallback on the 'frame_type_section.default_data_copy'",
    )

    class Info(Enum):
        URL_ENTRY = "entry"
        FRAME_TYPE = "frame_type"
        COPY = "copy"

    @field_validator(
        "frame_type",
        mode="plain",
    )
    @classmethod
    def cast_to_AcquisitionStep(cls, value: str | AcquisitionStep) -> AcquisitionStep:
        return AcquisitionStep.from_value(value)

    @field_validator(
        "copy_data",
        mode="plain",
    )
    @classmethod
    def cast_to_copy_data(cls, value: bool | None) -> bool | None:
        if value in (None, "", "None"):
            return None
        else:
            return convert_str_to_bool(value)

    @field_validator(
        "url",
        mode="plain",
    )
    @classmethod
    def cast_to_url(cls, value: str | DataUrl | None) -> DataUrl:
        if value is None:
            return value
        elif isinstance(value, DataUrl):
            return value
        else:
            if "path=" not in value:
                # by default we expect the user to only give an entry on the file. So only the dataset path
                return DataUrl(data_path=value)
            else:
                return DataUrl(path=value)

    @field_serializer(
        "url",
        when_used="always",
    )
    @classmethod
    def serialize_data_url(cls, value: DataUrl | None) -> str:
        if value is None:
            return ""
        elif value.file_path() is None:
            return value.data_path()
        else:
            return value.path()

    @staticmethod
    def frm_str(input_str: str) -> FrameGroup:
        """
        Create an instance of FrameGroup from it string representation.
        """
        if not isinstance(input_str, str):
            raise TypeError(f"{input_str} should be a string")

        input_str = remove_parenthesis_or_brackets(input_str)
        elmts = input_str.split(",")
        elmts = filter(None, [elmt.lstrip(" ").rstrip(" ") for elmt in elmts])

        cst_inputs = {}

        for elmt in elmts:
            try:
                info_type, value = FrameGroup._treat_elmt(elmt)
            except ValueError:
                url_example = DataUrl(
                    file_path="/path/to/my/file/file.h5",
                    data_path="/data/path",
                    scheme="h5py",
                )
                _example_frame = FrameGroup(
                    url=url_example, copy_data=True, frame_type="projection"
                )
                err_msg = (
                    f"Unable to interpret string ('{elmt}'). Please insure this is a "
                    "either a frame type, a boolean for copy or an entry "
                    "(DataUrl).\n "
                    "Please prefix the value by the information type like: "
                    f"{_example_frame}. Invalid element is {input_str}"
                )
                raise ValueError(err_msg)
            else:
                cst_inputs[info_type] = value

        inputs = {}
        if FrameGroup.Info.FRAME_TYPE not in cst_inputs:
            raise ValueError(f"Unable to find frame type from {input_str}")
        else:
            inputs["frame_type"] = cst_inputs[FrameGroup.Info.FRAME_TYPE]
        if FrameGroup.Info.URL_ENTRY not in cst_inputs:
            raise ValueError(f"Unable to find entry from {input_str}")
        else:
            inputs["url"] = cst_inputs[FrameGroup.Info.URL_ENTRY]
        if FrameGroup.Info.COPY in cst_inputs:
            inputs["copy_data"] = cst_inputs[FrameGroup.Info.COPY]

        if "copy_data" in inputs:
            inputs["copy_data"] = inputs["copy_data"]

        return FrameGroup(**inputs)

    @staticmethod
    def _treat_elmt(elmt: str) -> tuple[str, str]:
        assert isinstance(elmt, str)
        # try to interpret it as a Frame group info
        for info in FrameGroup.Info:
            key = f"{info.value}="
            if elmt.startswith(key):
                return info, filter_str_def(elmt.replace(key, "", 1))

        # try to interpret it as an acquisition step
        elmt = filter_str_def(elmt)
        try:
            acquisition_step = AcquisitionStep.from_value(elmt)
        except ValueError:
            pass
        else:
            return FrameGroup.Info.FRAME_TYPE, acquisition_step

        # try to interpret it as a boolean
        # is this a copy element
        if elmt.startswith(("copy=", "copy_data=")):
            return FrameGroup.Info.COPY, elmt.split("=")[1]

        if elmt in ("True", "true"):
            return FrameGroup.Info.COPY, True
        if elmt in ("False", "false"):
            return FrameGroup.Info.COPY, False

        try:
            elmt = filter_str_def(elmt)
            DataUrl(path=elmt)
        except ValueError:
            pass
        else:
            return FrameGroup.Info.URL_ENTRY, elmt

        raise ValueError

    def __str__(self) -> str:
        return self.str_representation(
            only_data_path=False, with_copy=True, with_prefix_key=True
        )

    def str_representation(
        self, only_data_path: bool, with_copy: bool, with_prefix_key: bool
    ) -> str:
        """
        Util function to print the possible input string for this FrameGroup.

        :param only_data_path: if True consider the input file frame group is
                               contained in the input file and the string
                               representing the url can be only the data path
        :param with_copy: if true display the copy information
        :param with_prefix_key: if true provide the string with the keys as
                                prefix (frame_type=XXX, copy=...)
        """
        if self.url is None:
            url_str = ""
        elif only_data_path or self.url.file_path() is None:
            url_str = self.url.data_path()
        else:
            url_str = self.url.path()
        if with_prefix_key:
            if with_copy:
                return "({ft_key}={frame_type}, {url_key}={url}, {copy_key}={copy})".format(
                    ft_key=self.Info.FRAME_TYPE.value,
                    frame_type=self.frame_type.value,
                    url_key=self.Info.URL_ENTRY.value,
                    url=url_str,
                    copy_key=self.Info.COPY.value,
                    copy=self.copy_data,
                )
            else:
                return "({ft_key}={frame_type}, {url_key}={url})".format(
                    ft_key=self.Info.FRAME_TYPE.value,
                    frame_type=self.frame_type.value,
                    url_key=self.Info.URL_ENTRY.value,
                    url=url_str,
                )
        else:
            if with_copy:
                return "({frame_type}, {url}, {copy})".format(
                    frame_type=self.frame_type.value,
                    url=url_str,
                    copy=self.copy_data,
                )
            else:
                return "({frame_type}, {url})".format(
                    frame_type=self.frame_type.value,
                    url=url_str,
                )


def filter_acqui_frame_type(
    init: FrameGroup, sequences: tuple, frame_type: AcquisitionStep
) -> tuple:
    """compute the list of urls representing projections
    from init until the next Initialization step

    :param init: frame group creating the beginning of the
                            acquisition sequence
    :param sequences: list of FrameGroup representing the sequence
    :param frame_type: type of frame to filer (cannot be Initialization step)
    """
    frame_type = AcquisitionStep.from_value(frame_type)
    if frame_type is AcquisitionStep.INITIALIZATION:
        raise ValueError(f"{AcquisitionStep.INITIALIZATION.value} is not handled")
    if init not in sequences:
        raise ValueError(f"{init} cannot be find in the provided sequence")

    frame_types = [frm_grp.frame_type for frm_grp in sequences]
    current_acqui_idx = sequences.index(init)
    if len(sequences) == current_acqui_idx - 1:
        # in case the initialization sequence is the last element of the
        # sequence (if people make strange stuff...)
        return ()
    sequence_target = sequences[current_acqui_idx + 1 :]
    frame_types = frame_types[current_acqui_idx + 1 :]
    try:
        next_acqui = frame_types.index(AcquisitionStep.INITIALIZATION) - 1
    except ValueError:
        next_acqui = -1
    sequence_target = sequence_target[:next_acqui]
    filter_fct = lambda a: a.frame_type is frame_type
    return tuple(filter(filter_fct, sequence_target))
