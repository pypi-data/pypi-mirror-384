from __future__ import annotations

from nxtomomill.utils.io import deprecated


class ConfigBase:
    """
    Base class for models that can produce a configuration file (.cfg) to be provided to one of the converter.

    The configuration is setting inputs for the different conversion functions / classes.
    We expect config classes / models to inherit from this class and from a pydantic model.
    """

    def to_cfg_file(self, file_path: str, filter_sections: tuple[str] = tuple()):
        raise NotImplementedError

    @classmethod
    def from_cfg_file(cls, file_path: str) -> ConfigBase:
        raise NotImplementedError

    @deprecated(
        reason="Replaced by pydantic function 'model_dump'", since_version="2.0"
    )
    def to_dict(self) -> dict:
        return self.model_dump()  # pylint: disable=E1101

    @staticmethod
    def from_dict(dict_: dict) -> None:
        """.. warning:: deprecated since 2.0"""
        raise NotImplementedError
