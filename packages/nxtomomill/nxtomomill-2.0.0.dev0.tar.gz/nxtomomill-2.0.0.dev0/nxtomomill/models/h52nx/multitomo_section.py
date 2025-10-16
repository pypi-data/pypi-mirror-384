from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, ConfigDict


class MultiTomoSection(BaseModel):

    model_config: ConfigDict = ConfigDict(
        validate_assignment=True, validate_by_name=True
    )

    start_angle_offset_in_degree: float | None = Field(
        default=None, description="Start angle offset in degree."
    )
    n_nxtomo: int = Field(default=-1, description="Number of NXtomo to create.")
    angle_interval_in_degree: int = Field(
        default=360, description="Angle interval to create."
    )
    shift_angles: bool = Field(
        default=False, description="Shift all angle NXtomo angle."
    )

    @field_validator(
        "start_angle_offset_in_degree",
        mode="plain",
    )
    @classmethod
    def cast_to_float(cls, value: str) -> float | None:
        if value in (None, "None", ""):
            return None
        return float(value)

    # field aliases

    @property
    def multitomo_start_angle_offset(self):
        return self.start_angle_offset_in_degree

    @multitomo_start_angle_offset.setter
    def multitomo_start_angle_offset(self, value):
        self.start_angle_offset_in_degree = value

    @property
    def multitomo_scan_range(self):
        return self.angle_interval_in_degree

    @multitomo_scan_range.setter
    def multitomo_scan_range(self, value):
        self.angle_interval_in_degree = value

    @property
    def multitomo_shift_angles(self):
        return self.shift_angles

    @multitomo_shift_angles.setter
    def multitomo_shift_angles(self, value):
        self.shift_angles = value

    @property
    def multitomo_n_nxtomo(self):
        return self.n_nxtomo

    @multitomo_n_nxtomo.setter
    def multitomo_n_nxtomo(self, value):
        self.n_nxtomo = value
