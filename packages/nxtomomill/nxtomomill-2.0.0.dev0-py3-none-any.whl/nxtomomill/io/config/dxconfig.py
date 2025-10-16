# coding: utf-8

from __future__ import annotations


from nxtomomill.utils.io import deprecated_warning
from nxtomomill.models.dx2nx import DX2nxModel as _DXFileConfiguration


__all__ = ["DXFileConfiguration"]


class DXFileConfiguration(_DXFileConfiguration):
    def __init__(self, *args, **kwargs):
        deprecated_warning(
            type_="class",
            name="DXFileConfiguration",
            replacement="nxtomomill.models.dx2nx.DX2nxModel",
            reason="moved to models module",
            since_version="2.0",
        )
        super().__init__(*args, **kwargs)
