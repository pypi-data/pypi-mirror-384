from __future__ import annotations

import numpy
import h5py
from silx.io.utils import h5py_read_dataset
from nxtomomill.models.utils import convert_str_to_tuple, convert_str_to_bool

__all__ = [
    "TomoConfig",
]


class TomoConfig:
    """
    hold motor used for tomography acquisition according to https://tomo.gitlab-pages.esrf.fr/bliss-tomo/master/modelization_sample_stage.html convension
    """

    def __init__(self) -> None:
        self._rotation: None | tuple[str, ...] = None
        self._sample_u: None | tuple[str, ...] = None
        self._sample_v: None | tuple[str, ...] = None
        self._sample_x: None | tuple[str, ...] = None
        self._sample_y: None | tuple[str, ...] = None
        self._translation_x: None | tuple[str, ...] = None
        self._translation_y: None | tuple[str, ...] = None
        self._translation_z: None | tuple[str, ...] = None
        self._tomo_detector: None | tuple[str, ...] = None
        self._rotation_is_clockwise: None | bool = None

    @property
    def rotation(self) -> tuple[str, ...] | None:
        return self._rotation

    @rotation.setter
    def rotation(self, motor: tuple[str, ...] | None):
        self._rotation = motor

    @property
    def sample_u(self) -> tuple[str, ...] | None:
        return self._sample_u

    @sample_u.setter
    def sample_u(self, motor: tuple[str, ...] | None):
        self._sample_u = motor

    @property
    def sample_v(self) -> tuple[str, ...] | None:
        return self._sample_v

    @sample_v.setter
    def sample_v(self, motor: tuple[str, ...] | None):
        self._sample_v = motor

    @property
    def sample_x(self) -> tuple[str, ...] | None:
        return self._sample_x

    @sample_x.setter
    def sample_x(self, motor: tuple[str, ...] | None):
        self._sample_x = motor

    @property
    def sample_y(self) -> tuple[str, ...] | None:
        return self._sample_y

    @sample_y.setter
    def sample_y(self, motor: tuple[str, ...] | None):
        self._sample_y = motor

    @property
    def translation_x(self) -> tuple[str, ...] | None:
        return self._translation_x

    @translation_x.setter
    def translation_x(self, motor: tuple[str, ...] | None):
        self._translation_x = motor

    @property
    def translation_y(self) -> tuple[str, ...] | None:
        return self._translation_y

    @translation_y.setter
    def translation_y(self, motor: tuple[str, ...] | None):
        self._translation_y = motor

    @property
    def translation_z(self) -> tuple[str, ...] | None:
        return self._translation_z

    @translation_z.setter
    def translation_z(self, motor: tuple[str, ...] | None):
        self._translation_z = motor

    @property
    def tomo_detector(self) -> tuple[str, ...] | None:
        return self._tomo_detector

    @tomo_detector.setter
    def tomo_detector(self, detector_name: tuple[str, ...]):
        self._tomo_detector = detector_name

    @property
    def rotation_is_clockwise(self) -> bool | None:
        return self._rotation_is_clockwise

    @rotation_is_clockwise.setter
    def rotation_is_clockwise(self, is_clockwise: bool | None) -> None:
        if is_clockwise is None:
            self._rotation_is_clockwise = is_clockwise
        elif isinstance(is_clockwise, (bool, numpy.bool_)):
            self._rotation_is_clockwise = bool(is_clockwise)
        else:
            raise TypeError(
                f"'is_clockwise' should be a bool or Not. Got {type(is_clockwise)}"
            )

    def __str__(self) -> str:
        return "tomo_config:" + " ; ".join(
            [
                f"rotation={', '.join(self.rotation)}",
                f"rotation_is_clockwise={self.rotation_is_clockwise}",
                f"sample_u={', '.join(self.sample_u)}",
                f"sample_v={', '.join(self.sample_v)}",
                f"sample_x={', '.join(self.sample_x)}",
                f"sample_y={', '.join(self.sample_y)}",
                f"tomo_detector={', '.join(self.tomo_detector)}",
                f"translation_x={', '.join(self.translation_x)}",
                f"translation_y={', '.join(self.translation_y)}",
                f"translation_z={', '.join(self.translation_z)}",
            ]
        )

    @staticmethod
    def from_technique_group(technique_group: h5py.Group):
        """
        get rotation motor and thinks like this from the 'tomoconfig'.
        This can retrieve one or several dataset name or a single one.
        In the case of several dataset name we get (real_motor_name, bliss_alias)

        If the motor moves then this is pretty simple the real motor_name dataset exists.
        But if the motors does not move during the bliss scan (scalar value) then the real_motor_name dataset doesn't exists and
        the bliss alias does. This is why we need to keep both and check both during the 'standard process'...
        """
        if not isinstance(technique_group, h5py.Group):
            raise TypeError(
                f"instrument_group is expected to be an instance of {h5py.Group}. {type(technique_group)} provided"
            )
        if "tomoconfig" not in technique_group:
            raise KeyError("could find 'tomoconfig' key")
        else:
            tomo_config_group = technique_group.get("tomoconfig")

        def get_dataset(group, dataset_name, default, dtype=tuple):
            if dataset_name not in group:
                return default
            dataset = h5py_read_dataset(group[dataset_name])
            # note: the dataset are read as string '["detector"]' and must be converted to dtype
            if dtype is tuple:
                return convert_str_to_tuple(tuple(dataset))
            elif dtype is bool:
                return convert_str_to_bool(dataset)
            else:
                raise TypeError(f"invalid dtype: {dtype}")

        tomo_config = TomoConfig()
        tomo_config.rotation = get_dataset(tomo_config_group, "rotation", None)
        tomo_config.rotation_is_clockwise = get_dataset(
            tomo_config_group, "rotation_is_clockwise", default=None, dtype=bool
        )
        tomo_config.sample_u = get_dataset(tomo_config_group, "sample_u", None)
        tomo_config.sample_v = get_dataset(tomo_config_group, "sample_v", None)
        tomo_config.sample_x = get_dataset(tomo_config_group, "sample_x", None)
        tomo_config.sample_y = get_dataset(tomo_config_group, "sample_y", None)
        tomo_config.tomo_detector = get_dataset(tomo_config_group, "detector", None)

        # translation x == sample_u
        tomo_config.translation_x = get_dataset(
            tomo_config_group, "sample_u", None
        )  # Needs translation X mapping
        tomo_config.translation_y = get_dataset(
            tomo_config_group, "translation_y", None
        )
        tomo_config.translation_z = get_dataset(
            tomo_config_group, "translation_z", None
        )

        return tomo_config
