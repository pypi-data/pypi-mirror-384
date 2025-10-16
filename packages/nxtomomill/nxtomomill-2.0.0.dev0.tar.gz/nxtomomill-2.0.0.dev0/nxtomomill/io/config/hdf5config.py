# coding: utf-8

from __future__ import annotations


from nxtomomill.utils.io import deprecated, deprecated_warning
from nxtomomill.models.h52nx import H52nxModel as _TomoHDF5Config
from nxtomomill.models.h52nx import (
    generate_default_h5_config as _generate_default_h5_config,
)


__all__ = [
    "TomoHDF5Config",
    "generate_default_h5_config",
]


class TomoHDF5Config(_TomoHDF5Config):
    def __init__(self, *args, **kwargs):
        deprecated_warning(
            type_="class",
            name="TomoHDF5Config",
            replacement="nxtomomill.models.dx2nx.H52nxModel",
            reason="moved to models module",
            since_version="2.0",
        )
        super().__init__(*args, **kwargs)


@deprecated(reason="moved to from nxtomomill.models.h52nx module", since_version="2.0")
def generate_default_h5_config(*args, **kwargs):
    return _generate_default_h5_config(*args, **kwargs)
