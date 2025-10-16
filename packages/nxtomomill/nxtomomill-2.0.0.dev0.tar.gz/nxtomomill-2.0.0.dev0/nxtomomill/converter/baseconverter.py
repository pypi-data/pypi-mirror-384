"""Contain base class of a converter"""


class BaseConverter:
    """
    Interface of a converter
    """

    def convert(self) -> tuple:
        raise NotImplementedError("Base class")
