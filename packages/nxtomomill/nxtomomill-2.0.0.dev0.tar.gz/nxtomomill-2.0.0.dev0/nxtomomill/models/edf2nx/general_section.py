from __future__ import annotations

from nxtomomill.models.utils import convert_str_to_tuple, convert_str_to_bool
from nxtomomill.settings import Tomo
from nxtomomill.models.utils import PathType
from nxtomomill.models.utils import filter_str_def

from ..base.general_section import GeneralSection as _GeneralSectionBase

from pydantic import Field, field_validator, ConfigDict, field_serializer


class GeneralSection(_GeneralSectionBase):
    model_config: ConfigDict = ConfigDict(
        validate_assignment=True,
        validate_by_name=True,
    )

    input_folder: str | None = Field(
        default=None,
        description="Path to the folder containing .edf files (mandatory)",
    )
    delete_edf_source_files: bool = Field(
        default=False,
        description="Remove EDF source files after successful conversion. This operation is conditional and will only execute if the 'duplicate_data' flag is set to True. By default, 'duplicate_data' is set to True, allowing this cleanup operation to proceed",
        alias="delete_edf_source_file",
    )
    output_checks: tuple[str, ...] = Field(
        default=tuple(),
        description="Perform validation checks post-conversion to ensure data integrity and accuracy."
        "This function accepts a list of specified tests to validate the conversion process."
        "Currently supported test:\n"
        "- 'compare-output-volume': Compares the volume of the output data to ensure it matches expected values.",
    )
    dataset_basename: str | None = Field(
        default=None,
        description="Prefix for dataset files used to identify associated projection and info files."
        "If this prefix is not explicitly provided, the system will default to using the name of the input folder as the prefix."
        "This ensures that all related files can be accurately linked and processed to",
    )
    dataset_info_file: str | None = Field(
        default=None,
        description="Path to the .info file containing metadata about the dataset, such as Energy, ScanRange, and TOMO_N."
        "If this path is not provided, the system will attempt to deduce it automatically using the dataset_basename."
        "This ensures that necessary metadata is accessible for further processing and analysis.",
    )
    title: str | None = Field(default=None, description="NXtomo title")
    patterns_to_ignores: tuple[str, ...] = Field(
        default=Tomo.EDF.TO_IGNORE,
        description="Specifies file patterns that determine which files should be ignored during processing."
        "Files matching these patterns will be excluded from operations. "
        "This is particularly useful for filtering out unnecessary or intermediate files, such as reconstructed slice files.",
    )
    duplicate_data: bool = Field(
        default=True,
        description="Determines if we can create files with external links or not."
        "If False then will create embed all the data into a single file avoiding external link to other file. "
        "If True then the detector data will point to original tif files. In this case you must be cautious to keep relative paths valid. Warning: to read external dataset you nust be at the hdf5 file working directory. See external link resolution details: https://support.hdfgroup.org/documentation/hdf5/latest/group___h5_l.html#title5",
    )
    external_link_type: PathType = Field(
        default=PathType.RELATIVE,
        description="Specifies the type of file path to use for linking to original files when 'duplicate_data' is set to False."
        "When 'duplicate_data' is False, you can choose how file paths are referenced:"
        "\n- 'relative': Uses relative paths for linking to the original files."
        "\n- 'absolute': Uses absolute paths for linking to the original files.",
        alias="external_link_path",
    )

    @field_validator(
        "input_folder",
        "dataset_basename",
        "dataset_info_file",
        "title",
        mode="plain",
    )
    @classmethod
    def cast_to_str(cls, value: str | None) -> tuple | None:
        return filter_str_def(value)

    @field_validator(
        "patterns_to_ignores",
        "output_checks",
        mode="plain",
    )
    @classmethod
    def cast_to_tuple(cls, value: tuple[str, ...] | str | None) -> tuple[str]:
        if isinstance(value, tuple):
            return value
        value = filter_str_def(value)
        return convert_str_to_tuple(value) or ()

    @field_validator(
        "external_link_type",
    )
    @classmethod
    def cast_to_path_type(cls, value: str | PathType) -> PathType:
        if isinstance(value, str):
            value = filter_str_def(value).lower()
        return PathType(value)

    @field_serializer(
        "external_link_type",
    )
    @classmethod
    def serialize_external_link_type(cls, value: PathType):
        return value.value

    @field_validator(
        "delete_edf_source_files",
        mode="plain",
    )
    @classmethod
    def cast_to_bool(cls, value: bool | str) -> bool:
        if isinstance(value, str):
            value = filter_str_def(value)
        return convert_str_to_bool(value)
