from __future__ import annotations

from nxtomomill.utils.io import deprecated
from .ConfigBase import ConfigBase


class FrmFlatToNestedBase(ConfigBase):
    """
    Base class defining behavior for models needing to be dumped with sections.

    Internally they are represented as 'flat' but externally they are represented as nested to ease user
    setting values.
    This is the historical design. Maybe in the future we will use nested models internally as well.
    """

    def to_cfg_file(self, file_path: str, filter_sections: tuple[str] = tuple()):
        nested_model = self.to_nested_model()
        nested_model.to_cfg_file(
            file_path=file_path,
            filter_sections=filter_sections,
        )

    def to_nested_model(self):
        raise NotImplementedError

    @deprecated(
        reason="Replaced by pydantic function 'model_dump'", since_version="2.0"
    )
    def to_dict(self) -> dict:
        config = self.to_nested_model()
        return {key.upper(): value for key, value in config.model_dump().items()}
