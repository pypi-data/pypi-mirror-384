from __future__ import annotations
from collections.abc import Sequence

import numpy as np
from numpy.typing import DTypeLike

from m3d.common import NumberType, float_eps


class Vector:
    __slots__ = ["_data"]

    def __init__(
        self,
        x: NumberType = 0.0,
        y: NumberType = 0.0,
        z: NumberType = 0.0,
        dtype: DTypeLike = np.float32,
        frozen: bool = False,
    ) -> None:
        self._data = np.array([float(x), float(y), float(z)], dtype=dtype)
        self._data.flags.writeable = not frozen

    @staticmethod
    def from_data(data: np.ndarray) -> Vector:
        res = Vector.__new__(Vector)
        res.data = data
        return res

    def __getitem__(self, idx: int) -> float:
        return self._data[idx]

    def __setitem__(self, idx: int, val: float) -> None:
        self._data[idx] = val

    @property
    def frozen(self) -> bool:
        return not self._data.flags.writeable

    @frozen.setter
    def frozen(self, val: bool) -> None:
        self._data.flags.writeable = not val

    def copy(self) -> Vector:
        return Vector.from_data(self._data.copy())

    @property
    def x(self) -> float:
        return float(self._data[0])

    @x.setter
    def x(self, val: float) -> None:
        self._data[0] = val

    @property
    def y(self) -> float:
        return float(self._data[1])

    @y.setter
    def y(self, val: float) -> None:
        self._data[1] = val

    @property
    def z(self) -> float:
        return float(self._data[2])

    @z.setter
    def z(self, val: float) -> None:
        self._data[2] = val

    def __str__(self) -> str:
        return f"Vector({self.x}, {self.y}, {self.z})"

    def __sub__(self, other: Vector) -> Vector:
        return Vector.from_data(self._data - other.data)

    def __add__(self, other: Vector) -> Vector:
        return Vector.from_data(self._data + other.data)

    def __neg__(self) -> Vector:
        return Vector.from_data(-self._data)

    __repr__ = __str__

    @property
    def data(self) -> np.ndarray:
        return self._data

    @data.setter
    def data(self, vector: np.ndarray) -> None:
        self._data = vector

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        return self.similar(other)

    def __mul__(self, other: NumberType) -> Vector:
        return Vector.from_data(self._data * other)

    __rmul__ = __mul__

    def __truediv__(self, other: NumberType) -> Vector:
        return Vector.from_data(self._data / other)

    def __itruediv__(self, other: NumberType) -> Vector:
        self._data /= other
        return self

    def __imul__(self, other: NumberType) -> Vector:
        self._data *= other
        return self

    @property
    def length(self) -> float:
        return float(np.linalg.norm(self._data))

    def dist(self, other: Vector) -> float:
        """
        return abolute distance to another vector
        """
        v = self - other
        return v.length

    def similar(self, other: Vector, tol: NumberType = float_eps) -> bool:
        """
        Return True if distance to other Vector is less than tol
        return False otherwise
        """
        return bool(self.dist(other) <= tol)

    def normalize(self) -> None:
        """
        Normalize in place vector
        """
        if self.length == 0:
            return
        self._data /= self.length

    def normalized(self) -> Vector:
        """
        Return a normalized copy of vector
        """
        if self.length == 0:
            return Vector.from_data(self._data)
        return Vector.from_data(self._data / self.length)

    def cross(self, other: Vector) -> Vector:
        return Vector.from_data(np.cross(self._data, other.data))

    def dot(self, other: Vector) -> float:
        return np.dot(self._data, other.data)

    __matmul__ = dot

    def project(self, other: Vector) -> Vector:
        other = other.normalized()
        return self.dot(other) * other

    def angle(self, other: Vector, normal_vector: Vector | None = None) -> float:
        """
        If provided, normal_vector is a vector defining the reference plane to be used to compute sign of angle.
        Otherwise, returned angle is between 0 and pi.
        """
        cos = self.dot(other) / (self.length * other.length)
        angle = np.arccos(np.clip(cos, -1, 1))
        if normal_vector is not None:
            angle = angle * np.sign(normal_vector.dot(self.cross(other)))
        return angle

    def as_so3(self) -> np.ndarray:
        """
        Returns the skew symetric (so3) representation of the vector
        https://en.wikipedia.org/wiki/Skew-symmetric_matrix
        """
        return np.array(
            [
                [0, -self.z, self.y],
                [self.z, 0, -self.x],
                [-self.y, self.x, 0],
            ]
        )

    @staticmethod
    def mean(*vectors: Vector, weights: Sequence[float] | np.ndarray | None = None) -> Vector:
        if weights is None:
            weights = np.ones(len(vectors))

        if len(vectors) != len(weights):
            raise ValueError("The number of weights needs to correspond to the number of vectors to average")
        if abs(sum(weights)) < float_eps:
            raise ValueError("Can not have all weights 0 or close to 0")

        return Vector(*np.average([vec.data for vec in vectors], axis=0, weights=weights))

    def __getstate__(self) -> tuple[float, float, float]:
        return self.x, self.y, self.z

    def __setstate__(self, data: tuple[float, float, float]) -> None:
        self.data = np.array(data)


# some units vectors
e0 = ex = Vector(1, 0, 0)
e1 = ey = Vector(0, 1, 0)
e2 = ez = Vector(0, 0, 1)
