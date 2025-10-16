from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, ConfigDict
from nxtomomill.settings import Tomo
from nxtomomill.models.utils import convert_str_to_tuple, is_url_path, filter_str_def


from silx.io.url import DataUrl


class EntriesAndTitlesSection(BaseModel):

    model_config = ConfigDict(
        validate_assignment=True, arbitrary_types_allowed=True, validate_by_name=True
    )

    entries: tuple[DataUrl, ...] = Field(
        default=tuple(), description="List of root/init entries to convert"
    )
    sub_entries_to_ignore: tuple[DataUrl, ...] = Field(
        default=tuple(), description="List of sub entries to ignore"
    )
    init_titles: tuple[str, ...] = Field(
        default=Tomo.H5.INIT_TITLES, description="Titles for initialization"
    )
    zseries_init_titles: tuple[str, ...] = Field(
        default=Tomo.H5.ZSERIE_INIT_TITLES,
        description="Titles for z-serie initialization",
        alias="zserie_init_titles",
    )
    multitomo_init_titles: tuple[str, ...] = Field(
        default=Tomo.H5.MULTITOMO_INIT_TITLES,
        description="Titles for multi-tomo initialization",
    )
    back_and_forth_init_titles: tuple[str, ...] = Field(
        default=Tomo.H5.BACK_AND_FORTH_INIT_TITLES,
        description="Titles for back-and-forth initialization",
    )
    dark_titles: tuple[str, ...] = Field(
        default=Tomo.H5.DARK_TITLES,
        description="Titles to determine if the bliss scan is a set of dark",
    )
    flat_titles: tuple[str, ...] = Field(
        default=Tomo.H5.FLAT_TITLES,
        description="Titles to determine if the bliss scan is a set of flat",
    )
    projection_titles: tuple[str, ...] = Field(
        default=Tomo.H5.PROJ_TITLES,
        description="Titles to determine if the bliss scan is a set of projection",
        alias="proj_titles",
    )
    alignment_titles: tuple[str, ...] = Field(
        default=Tomo.H5.ALIGNMENT_TITLES,
        description="Titles to determine if the bliss scan is a set of alignment projection",
    )

    @field_validator(
        "init_titles",
        "zseries_init_titles",
        "multitomo_init_titles",
        "back_and_forth_init_titles",
        "dark_titles",
        "flat_titles",
        "projection_titles",
        "alignment_titles",
        mode="plain",
    )
    @classmethod
    def cast_to_tuple(cls, value: str | tuple[str]) -> tuple[str, ...]:
        if isinstance(value, str):
            value = filter_str_def(value)
        return convert_str_to_tuple(value) or ()

    @field_validator(
        "entries",
        "sub_entries_to_ignore",
        mode="before",
    )
    @classmethod
    def cast_to_tuple_of_url(
        cls, value: str | tuple[DataUrl | str, ...]
    ) -> tuple[DataUrl, ...]:
        """The entries are first converted from a string to a list of string.
        Then this list of string will be processed later to create a list of DataUrl with relative link and with a context
        """
        if isinstance(value, str):
            value = filter_str_def(value)
            value = convert_str_to_tuple(value)
        entries = EntriesAndTitlesSection.parse_frame_urls(value)
        return tuple(
            [EntriesAndTitlesSection.fix_entry_name(entry) for entry in entries]
        )

    @staticmethod
    def parse_frame_urls(urls: tuple[str | DataUrl, ...]):
        """
        Insure urls is None or a list of valid DataUrl
        """
        if urls in ("", None):
            return tuple()
        res = []
        for i_url, url in enumerate(urls):
            if isinstance(url, str):
                if url == "":
                    continue
                elif is_url_path(url):
                    url = DataUrl(path=url)
                else:
                    url = DataUrl(data_path=url, scheme="silx")
            if not isinstance(url, DataUrl):
                raise ValueError(
                    "urls tuple should contains DataUrl. "
                    f"Not {type(url)} at index {i_url}"
                )
            else:
                res.append(url)
        return tuple(res)

    @staticmethod
    def fix_entry_name(entry: DataUrl):
        """simple util function to insure the entry start by a "/"""
        if not isinstance(entry, DataUrl):
            raise TypeError("entry is expected to be a DataUrl")
        if not entry.data_path().startswith("/"):
            entry = DataUrl(
                scheme=entry.scheme(),
                data_slice=entry.data_slice(),
                file_path=entry.file_path(),
                data_path="/" + entry.data_path(),
            )
        return entry
