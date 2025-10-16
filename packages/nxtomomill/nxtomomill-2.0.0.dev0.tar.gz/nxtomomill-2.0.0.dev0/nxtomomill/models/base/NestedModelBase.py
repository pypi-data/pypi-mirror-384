from __future__ import annotations

import logging
from configparser import ConfigParser
from pydantic import BaseModel

_logger = logging.getLogger(__name__)


class NestedModelBase:

    @staticmethod
    def cast_value_to_str(value) -> str:
        if value in (None, tuple()):
            return ""
        else:
            return str(value)

    def to_cfg_file(self, file_path: str, filter_sections: tuple[str] = tuple()):
        """
        Dump the model to a cfg_file.
        In this case the model is expected to be composed of a set of sub-model.
        The sub-models are expected to only contain Fields.
        """
        if not file_path.lower().endswith((".cfg", ".config", ".conf")):
            _logger.warning("add a valid extension to the output file")
            file_path += ".cfg"
        config = ConfigParser(allow_no_value=True)
        config.optionxform = str
        for section_name in self.__class__.model_fields:  # pylint: disable=E1101
            if section_name in filter_sections:
                continue
            section_name_upper = section_name.upper()
            config.add_section(section_name_upper)
            config.set(section_name_upper, "")

            section: BaseModel = getattr(self, section_name)
            dump_model = section.model_dump(mode="python")

            for field_name, field_value in dump_model.items():
                field_info = section.model_fields[field_name]
                config.set(section_name_upper, "# " + field_info.description)
                config.set(
                    section_name_upper,
                    field_name,
                    self.cast_value_to_str(field_value),
                )

        with open(file_path, "w") as config_file:
            config.write(config_file)
