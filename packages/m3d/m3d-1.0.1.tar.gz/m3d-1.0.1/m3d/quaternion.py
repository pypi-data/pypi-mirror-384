from __future__ import annotations

import numpy as np
from numpy.typing import DTypeLike

from m3d.common import NumberType


class Quaternion:
    __slots__ = ["_data"]

    def __init__(
        self,
        w: NumberType = 0.0,
        x: NumberType = 0.0,
        y: NumberType = 0.0,
        z: NumberType = 0.0,
        dtype: DTypeLike = np.float32,
        frozen: bool = False,
    ) -> None:
        self._data = np.array([w, x, y, z], dtype=dtype)
        self._data.flags.writeable = not frozen

    @classmethod
    def from_data(cls, data: np.ndarray) -> Quaternion:
        res = cls.__new__(cls)
        res.data = data
        return res

    @property
    def frozen(self) -> bool:
        return not self._data.flags.writeable

    @frozen.setter
    def frozen(self, val: bool) -> None:
        self._data.flags.writeable = not val

    def __str__(self) -> str:
        return f"Quaternion({self._data})"

    __repr__ = __str__

    @property
    def data(self) -> np.ndarray:
        """
        Access the numpy array used by Quaternion
        """
        return self._data

    @data.setter
    def data(self, quat: np.ndarray) -> None:
        self._data = quat

    @property
    def scalar(self) -> float:
        return self._data[0]

    @property
    def vec(self) -> np.ndarray:
        return self._data[1:]

    def __add__(self, other: Quaternion) -> Quaternion:
        return Quaternion.from_data(self.data + other.data)

    def __rmul__(self, other: object) -> Quaternion:
        if not isinstance(other, NumberType):
            raise ValueError()
        return Quaternion.from_data(self._data * other)

    def __mul__(self, other: NumberType | Quaternion) -> Quaternion:
        if isinstance(other, Quaternion):
            s1 = self._data[0]
            s2 = other._data[0]
            q1 = self._data[1:]
            q2 = other._data[1:]
            scalar_part = np.asarray([s1 * s2 - np.dot(q1, q2)])
            imag_part = np.asarray(s1 * q2 + s2 * q1 + np.cross(q1, q2))
            return Quaternion.from_data(np.hstack((scalar_part, imag_part)))

        return Quaternion.from_data(other * self._data)

    @property
    def conjugate(self) -> Quaternion:
        return Quaternion(self._data[0], -self._data[1], -self.data[2], -self.data[3])

    def copy(self) -> Quaternion:
        return Quaternion.from_data(self._data.copy())

    def __getstate__(self) -> list[float]:
        return self.data.tolist()

    def __setstate__(self, data: list[float]) -> None:
        self.data = np.array(data)
