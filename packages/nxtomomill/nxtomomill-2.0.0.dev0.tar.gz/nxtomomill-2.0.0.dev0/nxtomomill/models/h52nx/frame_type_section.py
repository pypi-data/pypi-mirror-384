from __future__ import annotations

import re
import logging

from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer
from nxtomomill.models.h52nx.FrameGroup import FrameGroup
from nxtomomill.models.utils import remove_parenthesis_or_brackets
from nxtomomill.utils.io import deprecated

_logger = logging.getLogger(__name__)


class FrameTypeSection(BaseModel):

    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    data_scans: tuple[FrameGroup, ...] = Field(
        default=tuple(),
        description="List of scans to be converted."
        "Frame type should be provided for each scan. Expected format is:"
        " * `frame_type` (mandatory): values can be `projection`, `flat`, `dark`, `alignment` or `init`."
        " * `entry` (mandatory): DataUrl with path to the scan to integrate. If the scan is contained in the input_file then you can only provide path/name of the scan."
        " * `copy` (optional): you can provide a different behavior for the this scan (should we duplicate data or not)",
    )
    default_data_copy: bool = Field(
        default=False,
        description="Duplicate data inside the input file or create a relative link",
    )

    @property
    @deprecated(reason="renamed", since_version="2.0", replacement="data_scans")
    def data_frame_grps(self):
        return self.data_scans

    @data_frame_grps.setter
    @deprecated(reason="renamed", since_version="2.0", replacement="data_scans")
    def data_frame_grps(self, values) -> None:
        self.data_scans = values

    @field_validator(
        "data_scans",
        mode="plain",
    )
    @classmethod
    def cast_to_data_scan(
        cls, value: str | tuple[FrameGroup, ...]
    ) -> tuple[FrameGroup, ...]:
        if isinstance(value, tuple):
            return value
        return convert_str_to_frame_grp(value)

    @field_serializer(
        "data_scans",
        when_used="always",
    )
    @classmethod
    def serialize_data_scans(cls, urls: tuple[FrameGroup, ...]) -> str:
        if len(urls) == 0:
            return ""
        else:
            urls_str = ",\n".join([f"{frame_group}" for frame_group in urls])
            return f"""(
{urls_str}
)
            """


def convert_str_to_frame_grp(input_str: str) -> tuple[FrameGroup, ...]:
    """
    Convert a list such as:

    .. code-block:: text

        urls = (
            (frame_type=dark, entry="silx:///file.h5?data_path=/dark", copy=True),
            (frame_type=flat, entry="silx:///file.h5?data_path=/flat"),
            (frame_type=projection, entry="silx:///file.h5?data_path=/flat"),
            (frame_type=projection, entry="silx:///file.h5?data_path=/flat"),
        )

    to a tuple of FrameGroup
    """
    result = []
    if not isinstance(input_str, str):
        raise TypeError(
            f"input_str should be an instance of str. Got {type(input_str)}"
        )
    # remove spaces at the beginning and at the end
    input_str = input_str.replace("\n", "")
    input_str = input_str.lstrip(" ").rstrip(" ")
    input_str = remove_parenthesis_or_brackets(input_str)
    # special case when the ")" is given in a line and ignored by configparser
    input_str = input_str.replace("((", "(")
    # split sub entries
    re_expr = r"\([^\)]*\)"
    frame_grp_str_list = re.findall(re_expr, input_str)
    for frame_grp_str in frame_grp_str_list:
        try:
            frame_grp = FrameGroup.frm_str(frame_grp_str)
        except Exception as e:
            _logger.error(
                f"Unable to create a valid entry from {frame_grp_str}. Error is {e}"
            )
        else:
            result.append(frame_grp)
    return tuple(result)
