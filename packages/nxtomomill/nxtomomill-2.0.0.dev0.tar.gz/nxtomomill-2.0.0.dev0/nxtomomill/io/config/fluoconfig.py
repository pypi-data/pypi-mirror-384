# coding: utf-8

from __future__ import annotations


from nxtomomill.utils.io import deprecated, deprecated_warning
from nxtomomill.models.fluo2nx import Fluo2nxModel as _TomoFluoConfig
from nxtomomill.models.fluo2nx import (
    generate_default_fluo_config as _generate_default_fluo_config,
)


__all__ = ["TomoFluoConfig", "generate_default_fluo_config"]


class TomoFluoConfig(_TomoFluoConfig):
    def __init__(self, *args, **kwargs):
        deprecated_warning(
            type_="class",
            name="TomoFluoConfig",
            replacement="nxtomomill.models.fluo2nx.Fluo2nxModel",
            reason="moved to models module",
            since_version="2.0",
        )
        super().__init__(*args, **kwargs)


@deprecated(
    reason="moved to from nxtomomill.models.fluo2nx module", since_version="2.0"
)
def generate_default_fluo_config(*args, **kwargs):
    return _generate_default_fluo_config(*args, **kwargs)
