from __future__ import annotations
from typing import TypeVar

import numpy as np
from numpy.typing import DTypeLike

from m3d.vector import Vector
from m3d.orientation import Orientation
from m3d.common import NumberType, float_eps


T = TypeVar("T", Vector, "Transform", np.ndarray)


class Transform:
    """
    Rmq:
    When accessing/modifying the Orientation or Vector object you are
    modifying a view of the matrix data
    """

    __slots__ = ["data"]

    def __init__(
        self,
        orientation: Orientation | None = None,
        pos: Vector | None = None,
        dtype: DTypeLike = np.float32,
        frozen: bool = False,
    ) -> None:
        self.data = np.identity(4, dtype=dtype)

        if orientation is not None:
            self.data[:3, :3] = orientation.data

        if pos is not None:
            self.data[:3, 3] = pos.data

        self.data.flags.writeable = not frozen

    @classmethod
    def from_data(cls, data: np.ndarray) -> Transform:
        res = cls.__new__(cls)
        res.data = data
        return res

    @classmethod
    def identity(cls, dtype: DTypeLike = np.float32) -> Transform:
        return cls.from_data(np.identity(4, dtype=dtype))

    def is_valid(self) -> bool:
        """
        Check if a transform is valid
        """
        if abs(self.data[3, 3] - 1) > float_eps:
            return False
        if not (abs(self.data[3, 0:3]) < float_eps).all():
            return False
        if np.isnan(self.data.sum()):
            return False
        return self.orient.is_valid()

    def validate(self) -> Transform:
        if not self.is_valid():
            raise ValueError("Given args gives an invalid Transform")
        return self

    @property
    def frozen(self) -> bool:
        return not self.data.flags.writeable

    @frozen.setter
    def frozen(self, val: bool) -> None:
        self.data.flags.writeable = not val

    def __str__(self) -> str:
        return f"Transform(\n{self.orient},\n{self.pos}\n)"

    __repr__ = __str__

    @property
    def pos(self) -> Vector:
        """
        Access the position part of the matrix through a Vector object
        """
        return Vector.from_data(self.data[:3, 3])

    @pos.setter
    def pos(self, vector: Vector) -> None:
        self.data[:3, 3] = vector.data

    @property
    def orient(self) -> Orientation:
        """
        Access the orientation part of the matrix through an Orientation object
        """
        return Orientation.from_data(self.data[:3, :3])

    @orient.setter
    def orient(self, orient: Orientation) -> None:
        self.data[:3, :3] = orient.data

    def inverse(self) -> Transform:
        """
        Return inverse of Transform
        """
        t = self.copy()
        t.invert()
        return t

    def invert(self) -> None:
        """
        In-place inverse the matrix
        """
        if self.frozen:
            raise ValueError("This Transform is frozen")
        self.data[:3, :3] = self.data[:3, :3].T
        self.data[:3, 3:] = -self.data[:3, :3] @ self.data[:3, 3:]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transform):
            return False
        return self.similar(other)

    def __mul__(self, other: T) -> T:
        if isinstance(other, Vector):
            data = self.orient.data @ other.data + self.pos.data
            return Vector.from_data(data)
        if isinstance(other, Transform):
            return Transform.from_data(self.data @ other.data)
        if isinstance(other, np.ndarray):
            # This make it easy to support several format of point clouds but might be mathematically wrong
            if other.shape[1] == 3:
                return (self.orient.data @ other.T).T + self.pos.data
            if other.shape[0] == 3:
                return (self.orient.data @ other) + self.pos.data.reshape(3, 1)
            raise ValueError("Array shape must be 3, x or x, 3")
        return NotImplemented

    __matmul__ = __mul__

    @property
    def pose_vector(self) -> np.ndarray:
        return self.to_pose_vector()

    def to_pose_vector(self) -> np.ndarray:
        """
        Return a representation of transformation as 6 numbers array
        3 for position, and 3 for rotation vector
        """
        v = self.orient.to_rotation_vector()
        return np.array([self.pos.x, self.pos.y, self.pos.z, v.x, v.y, v.z])

    @classmethod
    def from_pose_vector(
        cls, x: NumberType, y: NumberType, z: NumberType, r1: NumberType, r2: NumberType, r3: NumberType
    ) -> Transform:
        o = Orientation.from_rotation_vector(Vector(r1, r2, r3))
        return cls(o, Vector(x, y, z)).validate()

    def as_adjoint(self) -> np.ndarray:
        """
        Returns the 6x6 adjoint representation of the transform,
        that can be used to transform any 6-vector twist
        https://en.wikipedia.org/wiki/Adjoint_representation
        """
        return np.vstack(
            [
                np.hstack([self.orient.data, np.zeros((3, 3))]),
                np.hstack([np.dot(self.pos.as_so3(), self.orient.data), self.orient.data]),
            ]
        )

    @classmethod
    def from_corresponding_points(cls, fixed: np.ndarray, moving: np.ndarray) -> Transform:
        """
        Given a set of points and another set of points
        representing matching points of those in another coordinate
        system, compute a least squares transform between them using
        SVD

        """
        if fixed.shape != moving.shape:
            raise ValueError("input point clouds must be same length")

        if np.allclose(fixed, moving):
            return cls()

        centroid_f = np.mean(fixed, axis=0)
        centroid_m = np.mean(moving, axis=0)

        f_centered = fixed - centroid_f
        m_centered = moving - centroid_m

        B = f_centered.T @ m_centered

        # find rotation
        U, D, V = np.linalg.svd(B)
        R = V.T @ U.T

        # special reflection case
        if np.linalg.det(R) < 0:
            V[2, :] *= -1
            R = V.T @ U.T

        t = -R @ centroid_f + centroid_m

        return cls(Orientation(R), Vector(t[0], t[1], t[2])).validate()

    def copy(self) -> Transform:
        return Transform.from_data(self.data.copy())

    def dist(self, other: Transform) -> float:
        """
        Return distance equivalent between this matrix and a second one
        """
        return self.pos.dist(other.pos) + self.orient.ang_dist(other.orient)

    def similar(self, other: Transform, tol: NumberType = float_eps) -> bool:
        """
        Return True if distance to other transform is less than tol
        return False otherwise
        """
        return bool(self.dist(other) <= tol)

    @staticmethod
    def mean(*transforms: Transform) -> Transform:
        return Transform(
            Orientation.mean(*(trf.orient for trf in transforms)), Vector.mean(*(trf.pos for trf in transforms))
        )

    def rotated_xb(self, angle: float) -> Transform:
        return Transform(Orientation.from_x_rotation(angle)) * self

    def rotated_yb(self, angle: float) -> Transform:
        return Transform(Orientation.from_y_rotation(angle)) * self

    def rotated_zb(self, angle: float) -> Transform:
        return Transform(Orientation.from_z_rotation(angle)) * self

    def rotated_xt(self, angle: float) -> Transform:
        return self * Transform(Orientation.from_x_rotation(angle))

    def rotated_yt(self, angle: float) -> Transform:
        return self * Transform(Orientation.from_y_rotation(angle))

    def rotated_zt(self, angle: float) -> Transform:
        return self * Transform(Orientation.from_z_rotation(angle))

    def translated_xb(self, dist: float) -> Transform:
        return Transform(pos=Vector(x=dist)) * self

    def translated_yb(self, dist: float) -> Transform:
        return Transform(pos=Vector(y=dist)) * self

    def translated_zb(self, dist: float) -> Transform:
        return Transform(pos=Vector(z=dist)) * self

    def translated_xt(self, dist: float) -> Transform:
        return self * Transform(pos=Vector(x=dist))

    def translated_yt(self, dist: float) -> Transform:
        return self * Transform(pos=Vector(y=dist))

    def translated_zt(self, dist: float) -> Transform:
        return self * Transform(pos=Vector(z=dist))

    def __getstate__(self) -> list[list[float]]:
        return self.data.tolist()

    def __setstate__(self, data: list[list[float]]) -> None:
        self.data = np.array(data)
