# coding: utf-8

from __future__ import annotations


from nxtomomill.utils.io import deprecated, deprecated_warning
from nxtomomill.models.edf2nx import EDF2nxModel as _TomoEDFConfig
from nxtomomill.models.edf2nx import (
    generate_default_edf_config as _generate_default_edf_config,
)


__all__ = ["TomoEDFConfig", "generate_default_edf_config"]


class TomoEDFConfig(_TomoEDFConfig):
    def __init__(self, *args, **kwargs):
        deprecated_warning(
            type_="class",
            name="TomoEDFConfig",
            replacement="nxtomomill.models.edf2nx.EDF2nxModel",
            reason="moved to models module",
            since_version="2.0",
        )
        super().__init__(*args, **kwargs)


@deprecated(reason="moved to from nxtomomill.models.edf2nx module", since_version="2.0")
def generate_default_edf_config(*args, **kwargs):
    return _generate_default_edf_config(*args, **kwargs)
