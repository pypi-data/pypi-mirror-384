from nxtomomill.utils.io import deprecated, deprecated_warning

from nxtomomill.models.utils import (
    remove_parenthesis_or_brackets as _remove_parenthesis_or_brackets,
)
from nxtomomill.models.utils import filter_str_def as _filter_str_def
from nxtomomill.models.utils import convert_str_to_tuple as _convert_str_to_tuple
from nxtomomill.models.utils import convert_str_to_bool as _convert_str_to_bool
from nxtomomill.models.utils import is_url_path as _is_url_path
from nxtomomill.models.utils import PathType as _PathType


@deprecated(
    replacement="nxtomomill.models.utils.remove_parenthesis_or_brackets",
    since_version="2.0",
    reason="moved",
)
def remove_parenthesis_or_brackets(*args, **kwargs):
    return _remove_parenthesis_or_brackets(*args, **kwargs)


@deprecated(
    replacement="nxtomomill.models.utils.filter_str_def",
    since_version="2.0",
    reason="moved",
)
def filter_str_def(*args, **kwargs):
    return _filter_str_def(*args, **kwargs)


@deprecated(
    replacement="nxtomomill.models.utils.convert_str_to_tuple",
    since_version="2.0",
    reason="moved",
)
def convert_str_to_tuple(*args, **kwargs):
    return _convert_str_to_tuple(*args, **kwargs)


@deprecated(
    replacement="nxtomomill.models.utils.convert_str_to_bool",
    since_version="2.0",
    reason="moved",
)
def convert_str_to_bool(*args, **kwargs):
    return _convert_str_to_bool(*args, **kwargs)


@deprecated(
    replacement="nxtomomill.models.utils.is_url_path",
    since_version="2.0",
    reason="moved",
)
def is_url_path(*args, **kwargs):
    return _is_url_path(*args, **kwargs)


class PathType(_PathType):
    def __init__(self, *args, **kwargs):
        deprecated_warning(
            type_="class",
            name="PathType",
            replacement="nxtomomill.models.utils.PathType",
            reason="moved to models module",
            since_version="2.0",
        )
        super().__init__(*args, **kwargs)
