from __future__ import annotations

from nxtomomill.models.utils import convert_str_to_tuple, filter_str_def

from ..base.general_section import GeneralSection as _GeneralSectionBase

from pydantic import Field, field_validator, ConfigDict


class GeneralSection(_GeneralSectionBase):

    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    input_folder: str | None = Field(
        default=None,
        description="Path to the folder containing the raw data folder and the fluofit/ subfolder. if not provided from the configuration file must be provided from the command line",
    )
    dimension: int = Field(
        default=3,
        description="Dimension of the experiment. 2 for 2D XRFCT, 3 for 3D XRFCT. Default is 3.",
    )
    detector_names: tuple[str, ...] = Field(
        default=tuple(),
        description="Define a list of (real or virtual) detector names used for the exp (space separated values - no comma). E.g. 'falcon xmap'. If not specified, all detectors are processed.",
    )
    dataset_basename: str | None = Field(
        default=None,
        description="In 2D, the exact full name of the folder. In 3D, the folder name prefix (the program will search for folders named <prefix>_XXX where XXX is a nmber.) If not provided will take the name of input_folder",
    )
    dataset_info_file: str | None = Field(
        default=None,
        description="Path to .info file containing dataset information (Energy, ScanRange, TOMO_N...). If not will deduce it from dataset_basename",
    )
    patterns_to_ignores: tuple[str, ...] = Field(
        default=("_slice_",),
        description="Some file pattern leading to ignoring the file. Like reconstructed slice files.",
    )
    duplicate_data: bool = Field(
        default=True,
        description="If False then will create embed all the data into a single file avoiding external link to other file. If True then the decetor data will point to original tif files. In this case you must be carreful to keep relative paths valid. Warning: to read external dataset you nust be at the hdf5 file working directory. See external link resolution details: https://support.hdfgroup.org/documentation/hdf5/latest/group___h5_l.html#title5",
    )

    @field_validator(
        "detector_names",
        "patterns_to_ignores",
        mode="before",
    )
    @classmethod
    def cast_to_tuple(cls, value: str | None) -> tuple[str]:
        return convert_str_to_tuple(value) or ()

    @field_validator(
        "input_folder",
        "dataset_basename",
        "dataset_info_file",
        mode="plain",
    )
    @classmethod
    def cast_to_str(cls, value: str | None) -> tuple | None:
        return filter_str_def(value)
