# coding: utf-8

"""
contains the FrameGroup
"""

from enum import Enum as _Enum
from nxtomo.nxobject.nxdetector import ImageKey

__all__ = [
    "AcquisitionStep",
]


class AcquisitionStep(_Enum):
    # Warning: order of acquisition step should be same as H5ScanTitles
    INITIALIZATION = "initialization"
    DARK = "darks"
    FLAT = "flats"
    PROJECTION = "projections"
    ALIGNMENT = "alignment projections"

    @classmethod
    def from_value(cls, value):
        if isinstance(value, str):
            value = value.lower()
            if value in ("init", "initialization"):
                value = AcquisitionStep.INITIALIZATION
            elif value in ("dark", "darks"):
                value = AcquisitionStep.DARK
            elif value in ("reference", "flat", "flats", "ref", "refs", "references"):
                value = AcquisitionStep.FLAT
            elif value in ("proj", "projection", "projs", "projections"):
                value = AcquisitionStep.PROJECTION
            elif value in (
                "alignment",
                "alignments",
                "alignment projection",
                "alignment projections",
            ):
                value = AcquisitionStep.ALIGNMENT

        return AcquisitionStep(value)

    def to_image_key(self):
        if self is AcquisitionStep.PROJECTION:
            return ImageKey.PROJECTION
        elif self is AcquisitionStep.ALIGNMENT:
            return ImageKey.PROJECTION
        elif self is AcquisitionStep.DARK:
            return ImageKey.DARK_FIELD
        elif self is AcquisitionStep.FLAT:
            return ImageKey.FLAT_FIELD
        else:
            raise ValueError(f"The step {self.value} does not fit any AcquisitionStep")

    def to_image_key_control(self):
        if self is AcquisitionStep.PROJECTION:
            return ImageKey.PROJECTION
        elif self is AcquisitionStep.ALIGNMENT:
            return ImageKey.ALIGNMENT
        elif self is AcquisitionStep.DARK:
            return ImageKey.DARK_FIELD
        elif self is AcquisitionStep.FLAT:
            return ImageKey.FLAT_FIELD
        else:
            raise ValueError(f"The step {self.value} does not fit any AcquisitionStep")
