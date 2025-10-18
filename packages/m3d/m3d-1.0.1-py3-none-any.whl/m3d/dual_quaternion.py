from __future__ import annotations

import numpy as np
from numpy.typing import DTypeLike

from m3d.common import NumberType, float_eps
from m3d.transform import Transform
from m3d.quaternion import Quaternion


class DualQuaternion:
    __slots__ = ["_data"]

    def __init__(self, vector: np.ndarray, dtype: DTypeLike = np.float32, frozen: bool = False) -> None:
        self._data = vector.astype(dtype, copy=False)
        self._data.flags.writeable = not frozen

    @property
    def frozen(self) -> bool:
        return not self._data.flags.writeable

    @frozen.setter
    def frozen(self, val: bool) -> None:
        self._data.flags.writeable = not val

    def __str__(self) -> str:
        return f"DualQuaternion(\n{self._data[:4]}, \n{self._data[4:]})"

    __repr__ = __str__

    @property
    def data(self) -> np.ndarray:
        return self._data

    @property
    def q_rot(self) -> Quaternion:
        return Quaternion.from_data(self._data[:4])

    @property
    def q_trans(self) -> Quaternion:
        return Quaternion.from_data(self._data[4:])

    @classmethod
    def from_transformation(cls, trans: Transform) -> DualQuaternion:
        """
        Write the transformation as a dual quaternion. A dual quaternion can be
        written as q = r + epslion * d
        where the r quaternion is known as the real or rotational part and the
        d quaternion is known as the dual or displacement part. epsilon is the
        dual unit.
        We denote q_rot as the rotation part and q_trans as the displacement
        part.
        """

        q_rot = trans.orient.to_quaternion()
        q_trans = 0.5 * Quaternion(0, trans.pos.x, trans.pos.y, trans.pos.z) * q_rot
        return cls(np.array([*q_rot.data, *q_trans.data]))

    def __mul__(self, other: NumberType | DualQuaternion) -> DualQuaternion:
        if isinstance(other, DualQuaternion):
            q_rot = self.q_rot * other.q_rot
            q_trans = self.q_rot * other.q_trans + self.q_trans * other.q_rot
            return DualQuaternion(np.array([*q_rot.data, *q_trans.data]))

        return DualQuaternion(other * self._data)

    def __rmul__(self, other: object) -> DualQuaternion:
        if not isinstance(other, NumberType):
            raise ValueError()
        return DualQuaternion(self._data * other)

    @property
    def conjugate(self) -> DualQuaternion:
        return DualQuaternion(np.array([*self.q_rot.conjugate.data, *self.q_trans.conjugate.data]))

    @property
    def unity_condition(self) -> bool:
        """
        When working with rigid rotational and translational transformations
        the dual quaternion must fulfill the unit condition, i.e.
        it must be of unit length.
        """
        norm = np.linalg.norm((self * self.conjugate).data)
        return bool(abs(1 - norm) < float_eps)

    def __getstate__(self) -> list[float]:
        return self.data.tolist()

    def __setstate__(self, data: list[float]) -> None:
        self._data = np.array(data)
