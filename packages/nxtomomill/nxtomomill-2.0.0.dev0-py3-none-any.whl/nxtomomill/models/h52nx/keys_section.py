from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator
from nxtomomill.models.utils import convert_str_to_tuple
from nxtomomill.settings import Tomo


class KeysSection(BaseModel):

    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    valid_camera_names: tuple[str, ...] = Field(
        default=tuple(), description="Valid camera names."
    )
    rotation_angle_keys: tuple[str, ...] = Field(
        default=Tomo.H5.ROT_ANGLE_KEYS,
        description="Keys for rotation angle.",
    )
    sample_x_keys: tuple[str, ...] = Field(
        default=Tomo.H5.SAMPLE_X_KEYS,
        description="Keys for sample x translation.",
    )
    sample_y_keys: tuple[str, ...] = Field(
        default=Tomo.H5.SAMPLE_Y_KEYS,
        description="Keys for sample y translation.",
    )
    translation_z_keys: tuple[str, ...] = Field(
        default=Tomo.H5.TRANSLATION_Z_KEYS,
        description="Keys for translation in z.",
    )
    translation_y_keys: tuple[str, ...] = Field(
        default=Tomo.H5.TRANSLATION_Y_KEYS,
        description="Keys for estimated center of rotation for half acquisition.",
    )
    diode_keys: tuple[str] = Field(
        default=Tomo.H5.DIODE_KEYS, description="Keys for diode."
    )
    exposure_time_keys: tuple[str, ...] = Field(
        default=Tomo.H5.ACQ_EXPO_TIME_KEYS, description="Keys for exposure time."
    )
    sample_x_pixel_size_keys: tuple[str, ...] = Field(
        default=Tomo.H5.SAMPLE_X_PIXEL_SIZE_KEYS,
        description="Keys for sample x pixel size.",
    )
    sample_y_pixel_size_keys: tuple[str, ...] = Field(
        default=Tomo.H5.SAMPLE_Y_PIXEL_SIZE_KEYS,
        description="Keys for sample y pixel size.",
    )
    detector_x_pixel_size_keys: tuple[str, ...] = Field(
        default=Tomo.H5.DETECTOR_X_PIXEL_SIZE_KEYS,
        description="Keys for detector x pixel size.",
    )
    detector_y_pixel_size_keys: tuple[str, ...] = Field(
        default=Tomo.H5.DETECTOR_Y_PIXEL_SIZE_KEYS,
        description="Keys for detector y pixel size.",
    )
    sample_detector_distance_keys: tuple[str, ...] = Field(
        default=Tomo.H5.SAMPLE_DETECTOR_DISTANCE_KEYS,
        description="Keys for sample to detector distance.",
        alias="sample_detector_distance",
    )
    source_sample_distance_keys: tuple[str, ...] = Field(
        default=Tomo.H5.SOURCE_SAMPLE_DISTANCE_KEYS,
        description="Keys for source to sample distance.",
        alias="source_sample_distance",
    )
    machine_current_keys: tuple[str, ...] = Field(
        default=Tomo.H5.MACHINE_CURRENT_KEYS,
        description="Keys for machine current.",
    )

    @field_validator(
        "valid_camera_names",
        "rotation_angle_keys",
        "sample_x_keys",
        "sample_y_keys",
        "translation_z_keys",
        "translation_y_keys",
        "diode_keys",
        "exposure_time_keys",
        "sample_x_pixel_size_keys",
        "sample_y_pixel_size_keys",
        "detector_x_pixel_size_keys",
        "detector_y_pixel_size_keys",
        "sample_detector_distance_keys",
        "source_sample_distance_keys",
        "machine_current_keys",
        mode="plain",
    )
    @classmethod
    def cast_to_tuple(cls, value: str) -> tuple[str, ...]:
        return convert_str_to_tuple(value) or ()
