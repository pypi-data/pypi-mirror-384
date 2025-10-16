# coding: utf-8

from __future__ import annotations


from nxtomomill.utils.io import deprecated_warning
from nxtomomill.models.base.ConfigBase import ConfigBase as _ConfigBase


__all__ = ["ConfigBase"]


class ConfigBase(_ConfigBase):
    def __init__(self, *args, **kwargs):
        deprecated_warning(
            type_="class",
            name="ConfigBase",
            replacement="nxtomomill.models.base.ConfigBase",
            reason="moved to models module",
            since_version="2.0",
        )
        super().__init__(*args, **kwargs)
