from __future__ import annotations

from nxtomomill.settings import Tomo
from nxtomomill.models.utils import convert_str_to_tuple

from pydantic import BaseModel, Field, field_validator, ConfigDict


class KeysSection(BaseModel):

    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    motor_position_keys: tuple[str, ...] = Field(
        default=Tomo.EDF.MOTOR_POS,
        description="Motor position key",
        alias="motor_position_key",
    )
    motor_mne_keys: tuple[str, ...] = Field(
        default=Tomo.EDF.MOTOR_MNE,
        description="key to used for reading indices of each motor",
        alias="motor_mne_key",
    )
    rotation_angle_keys: tuple[str, ...] = Field(
        default=Tomo.EDF.ROT_ANGLE,
        description="Keys to be used for reading rotation angle",
        alias="rot_angle_key",
    )
    x_translation_keys: tuple[str, ...] = Field(
        default=Tomo.EDF.X_TRANS,
        description="Keys to be used for reading x translation",
        alias="x_translation_key",
    )
    y_translation_keys: tuple[str, ...] = Field(
        default=Tomo.EDF.Y_TRANS,
        description="Keys to be used for reading y translation",
        alias="y_translation_key",
    )
    z_translation_keys: tuple[str, ...] = Field(
        default=Tomo.EDF.Z_TRANS,
        description="Keys to be used for reading z translation",
        alias="z_translation_key",
    )
    machine_current_keys: tuple[str, ...] = Field(
        default=Tomo.EDF.MACHINE_CURRENT,
        description="Keys to be used for reading the machine current",
    )

    @field_validator(
        "motor_position_keys",
        "motor_mne_keys",
        "rotation_angle_keys",
        "x_translation_keys",
        "y_translation_keys",
        "z_translation_keys",
        "machine_current_keys",
        mode="plain",
    )
    @classmethod
    def cast_to_tuple(cls, value: str | tuple[str, ...]) -> tuple[str,]:
        if isinstance(value, tuple):
            return value
        return convert_str_to_tuple(value) or ()
