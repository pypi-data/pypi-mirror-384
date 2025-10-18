from __future__ import annotations
import math
from typing import TypeVar

import numpy as np
from numpy.typing import DTypeLike

from m3d.vector import Vector
from m3d.common import float_eps
from m3d.quaternion import Quaternion


T = TypeVar("T", Vector, "Orientation", np.ndarray)
UNIT_EIGENVECTOR_THRESHOLD = 1e-4


class Orientation:
    __slots__ = ["_data"]

    def __init__(
        self,
        data: np.ndarray | None = None,
        dtype: DTypeLike = np.float32,
        frozen: bool = False,
    ) -> None:
        if data is None:
            self._data = np.identity(3, dtype=dtype)
        elif data.shape == (3, 3):
            self._data = data.astype(dtype, copy=False)
        else:
            raise ValueError(f"A numpy array of size (3, 3) is expected not {data.shape}")
        self._data.flags.writeable = not frozen

    @classmethod
    def from_data(cls, data: np.ndarray) -> Orientation:
        res = cls.__new__(cls)
        res.data = data
        return res

    @classmethod
    def identity(cls, dtype: DTypeLike = np.float32) -> Orientation:
        return cls.from_data(np.identity(3, dtype=dtype))

    @property
    def frozen(self) -> bool:
        return not self._data.flags.writeable

    @frozen.setter
    def frozen(self, val: bool) -> None:
        self._data.flags.writeable = not val

    def is_valid(self) -> bool:
        """
        A real orthogonal matrix with det(R) = 1 provides a matrix representation of a proper
        rotation. Furthermore, a real orthogonal matrix with det (R) = -1 provides a matrix
        representation of an improper rotation.
        """
        if not np.allclose(self._data.T @ self._data, np.eye(3), float_eps, float_eps):
            return False
        if not (1 - np.linalg.det(self._data)) < float_eps:
            return False
        return True

    def validate(self) -> Orientation:
        if not self.is_valid():
            raise ValueError("Given args gives an invalid Orientation")
        return self

    def rotate_xb(self, val: float) -> None:
        o = Orientation.from_x_rotation(val)
        self._data[:] = o.data @ self._data

    def rotate_yb(self, val: float) -> None:
        o = Orientation.from_y_rotation(val)
        self._data[:] = o.data @ self._data

    def rotate_zb(self, val: float) -> None:
        o = Orientation.from_z_rotation(val)
        self._data[:] = o.data @ self._data

    def rotate_xt(self, val: float) -> None:
        o = Orientation.from_x_rotation(val)
        self._data[:] = self._data @ o.data

    def rotate_yt(self, val: float) -> None:
        o = Orientation.from_y_rotation(val)
        self._data[:] = self._data @ o.data

    def rotate_zt(self, val: float) -> None:
        o = Orientation.from_z_rotation(val)
        self._data[:] = self._data @ o.data

    def rotated_xb(self, val: float) -> Orientation:
        return Orientation.from_x_rotation(val) * self

    def rotated_yb(self, val: float) -> Orientation:
        return Orientation.from_y_rotation(val) * self

    def rotated_zb(self, val: float) -> Orientation:
        return Orientation.from_z_rotation(val) * self

    def rotated_xt(self, val: float) -> Orientation:
        return self * Orientation.from_x_rotation(val)

    def rotated_yt(self, val: float) -> Orientation:
        return self * Orientation.from_y_rotation(val)

    def rotated_zt(self, val: float) -> Orientation:
        return self * Orientation.from_z_rotation(val)

    @classmethod
    def from_x_rotation(cls, angle: float) -> Orientation:
        return cls(
            np.array(
                [
                    [1, 0, 0],
                    [0, np.cos(angle), -np.sin(angle)],
                    [0, np.sin(angle), np.cos(angle)],
                ]
            )
        )

    @classmethod
    def from_y_rotation(cls, angle: float) -> Orientation:
        return cls(
            np.array(
                [
                    [np.cos(angle), 0, np.sin(angle)],
                    [0, 1, 0],
                    [-np.sin(angle), 0, np.cos(angle)],
                ]
            )
        )

    @classmethod
    def from_z_rotation(cls, angle: float) -> Orientation:
        return cls(
            np.array(
                [
                    [np.cos(angle), -np.sin(angle), 0],
                    [np.sin(angle), np.cos(angle), 0],
                    [0, 0, 1],
                ]
            )
        )

    def __str__(self) -> str:
        data = np.array2string(self.data, separator=", ")
        return f"Orientation(\n{data}\n)"

    __repr__ = __str__

    def inverse(self) -> Orientation:
        return Orientation.from_data(np.linalg.inv(self.data))

    def ang_dist(self, other: Orientation) -> float:
        r = self * other.inverse()
        trace_r = r.data[0, 0] + r.data[1, 1] + r.data[2, 2]
        cos_val = (trace_r - 1) / 2
        cos_val = np.clip(cos_val, -1.0, 1.0)  # might happen with approximations/rouding
        return np.arccos(cos_val)

    @property
    def data(self) -> np.ndarray:
        return self._data

    @data.setter
    def data(self, matrix: np.ndarray) -> None:
        self._data = matrix

    @property
    def array(self) -> np.ndarray:
        return self._data

    def __mul__(self, other: T) -> T:
        if isinstance(other, Vector):
            return Vector.from_data(self._data @ other.data)
        if isinstance(other, Orientation):
            return Orientation.from_data(self._data @ other.data)
        if isinstance(other, np.ndarray):
            if other.shape[0] == 3:
                return self.data @ other
            if other.shape[1] == 3:
                return (self.data @ other.T).T
            raise ValueError("Array shape must be 3,x or x,3")
        return NotImplemented

    __matmul__ = __mul__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Orientation):
            return False
        return self.similar(other)

    def to_quaternion(self) -> Quaternion:
        """
        Returns w, x, y, z
        adapted from
        https://github.com/matthew-brett/transforms3d/blob/master/transforms3d/quaternions.py
        """

        Qxx, Qyx, Qzx, Qxy, Qyy, Qzy, Qxz, Qyz, Qzz = self._data.flat
        # Fill only lower half of symmetric matrix
        K = (
            np.array(
                [
                    [Qxx - Qyy - Qzz, 0, 0, 0],
                    [Qyx + Qxy, Qyy - Qxx - Qzz, 0, 0],
                    [Qzx + Qxz, Qzy + Qyz, Qzz - Qxx - Qyy, 0],
                    [Qyz - Qzy, Qzx - Qxz, Qxy - Qyx, Qxx + Qyy + Qzz],
                ]
            )
            / 3.0
        )
        # Use Hermitian eigenvectors, values for speed
        vals, vecs = np.linalg.eigh(K)
        # Select largest eigenvector, reorder to w,x,y,z quaternion
        q = vecs[[3, 0, 1, 2], np.argmax(vals)]
        # Prefer quaternion with positive w
        # (q * -1 corresponds to same rotation as q)
        if q[0] < 0:
            q *= -1
        return Quaternion(q[0], q[1], q[2], q[3])

    @classmethod
    def from_quaternion(cls, quaternion: Quaternion) -> Orientation:
        # adapted from
        # https://github.com/matthew-brett/transforms3d/blob/master/transforms3d/quaternions.py
        w, x, y, z = quaternion.data
        Nq = w * w + x * x + y * y + z * z
        if Nq < float_eps:
            return Orientation()
        s = 2.0 / Nq
        X = x * s
        Y = y * s
        Z = z * s
        wX = w * X
        wY = w * Y
        wZ = w * Z
        xX = x * X
        xY = x * Y
        xZ = x * Z
        yY = y * Y
        yZ = y * Z
        zZ = z * Z
        return cls(
            np.array(
                [
                    [1.0 - (yY + zZ), xY - wZ, xZ + wY],
                    [xY + wZ, 1.0 - (xX + zZ), yZ - wX],
                    [xZ - wY, yZ + wX, 1.0 - (xX + yY)],
                ]
            )
        ).validate()

    @classmethod
    def from_axis_angle(cls, axis: Vector, angle: float, is_normalized: bool = False) -> Orientation:
        # adapted from
        # https://github.com/matthew-brett/transforms3d/blob/master/transforms3d/quaternions.py
        if not is_normalized:
            axis.normalize()
        x, y, z = axis.x, axis.y, axis.z
        c = math.cos(angle)
        s = math.sin(angle)
        C = 1 - c
        xs = x * s
        ys = y * s
        zs = z * s
        xC = x * C
        yC = y * C
        zC = z * C
        xyC = x * yC
        yzC = y * zC
        zxC = z * xC
        return cls(
            np.array(
                [
                    [x * xC + c, xyC - zs, zxC + ys],
                    [xyC + zs, y * yC + c, yzC - xs],
                    [zxC - ys, yzC + xs, z * zC + c],
                ]
            )
        ).validate()

    @classmethod
    def from_xy(cls, x_vec: Vector, y_vec: Vector) -> Orientation:
        """
        Generate a new Orientation from two vectors using x as reference
        """
        x_vec.normalize()
        y_vec.normalize()
        orient = cls()
        orient.data[:, 0] = x_vec.data
        orient.data[:, 2] = x_vec.cross(y_vec).normalized().data
        orient.data[:, 1] = Vector.from_data(np.cross(orient.data[:, 2], x_vec.data)).normalized().data
        return orient.validate()

    @classmethod
    def from_yz(cls, y_vec: Vector, z_vec: Vector) -> Orientation:
        """
        Generate a new Orientation from two vectors using y as reference
        """
        y_vec.normalize()
        z_vec.normalize()
        orient = cls()
        orient.data[:, 1] = y_vec.data
        orient.data[:, 0] = y_vec.cross(z_vec).normalized().data
        orient.data[:, 2] = Vector.from_data(np.cross(orient.data[:, 0], y_vec.data)).normalized().data
        return orient.validate()

    @classmethod
    def from_xz(cls, x_vec: Vector, z_vec: Vector, ref: str = "x") -> Orientation:
        """
        Generate a new Orientation from two vectors using x as reference
        """
        x_vec.normalize()
        z_vec.normalize()
        orient = cls()
        orient.data[:, 1] = z_vec.cross(x_vec).normalized().data

        if ref == "x":
            orient.data[:, 0] = x_vec.data
            orient.data[:, 2] = Vector.from_data(np.cross(x_vec.data, orient.data[:, 1])).normalized().data
        elif ref == "z":
            orient.data[:, 2] = z_vec.data
            orient.data[:, 0] = Vector.from_data(np.cross(orient.data[:, 1], z_vec.data)).normalized().data
        else:
            raise ValueError("Value of ref can only be x or z")

        return orient.validate()

    def to_axis_angle(self, unit_thresh: float = UNIT_EIGENVECTOR_THRESHOLD) -> tuple[Vector, float]:
        # adapted from
        # https://github.com/matthew-brett/transforms3d/blob/master/transforms3d/quaternions.py
        M = np.asarray(self._data, dtype=np.float32)
        # direction: unit eigenvector of R33 corresponding to eigenvalue of 1
        L, W = np.linalg.eig(M.T)
        i = np.where(np.abs(L - 1.0) < unit_thresh)[0]
        if i.size == 0:
            raise ValueError("no unit eigenvector corresponding to eigenvalue 1")
        direction = np.real(W[:, i[-1]]).squeeze()
        # rotation angle depending on direction
        cosa = (np.trace(M) - 1.0) / 2.0
        if abs(direction[2]) > 1e-8:
            sina = (M[1, 0] + (cosa - 1.0) * direction[0] * direction[1]) / direction[2]
        elif abs(direction[1]) > 1e-8:
            sina = (M[0, 2] + (cosa - 1.0) * direction[0] * direction[2]) / direction[1]
        else:
            sina = (M[2, 1] + (cosa - 1.0) * direction[1] * direction[2]) / direction[0]
        angle = math.atan2(sina, cosa)
        return Vector.from_data(direction), angle

    def to_rotation_vector(self, unit_thresh: float = UNIT_EIGENVECTOR_THRESHOLD) -> Vector:
        v, a = self.to_axis_angle(unit_thresh)
        return v * a

    @classmethod
    def from_rotation_vector(cls, v: Vector) -> Orientation:
        if v.length == 0:
            return cls()
        u = v.normalized()
        idx = (u.data != 0).argmax()
        return cls.from_axis_angle(u, v[idx] / u[idx], True).validate()

    def copy(self) -> Orientation:
        return Orientation(self.data.copy())

    def similar(self, other: Orientation, tol: float = float_eps) -> bool:
        """
        Return True if angular distance to other Orientation is less than tol
        return False otherwise
        """
        return bool(self.ang_dist(other) <= tol)

    @property
    def vec_x(self) -> Vector:
        return Vector.from_data(self._data[:, 0])

    @property
    def vec_y(self) -> Vector:
        return Vector.from_data(self._data[:, 1])

    @property
    def vec_z(self) -> Vector:
        return Vector.from_data(self._data[:, 2])

    @staticmethod
    def mean(*orientations: Orientation) -> Orientation:
        """
        Averaging quaternions
        https://ntrs.nasa.gov/api/citations/20070017872/downloads/20070017872.pdf
        """
        try:
            from scipy.optimize import minimize, NonlinearConstraint
        except ImportError:
            raise Exception("scipy must be installed to use this method")
        arit_mean = np.mean([ori.to_rotation_vector().data for ori in orientations], axis=0)
        arit_mean_ori = Orientation.from_rotation_vector(Vector.from_data(arit_mean))
        x0 = arit_mean_ori.to_quaternion().data

        quats = [ori.to_quaternion() for ori in orientations]
        ans = minimize(
            func_error_matrix,
            x0.astype(np.float64),
            args=(quats),
            method="SLSQP",
            constraints=NonlinearConstraint(np.linalg.norm, 1 - 1e-20, 1 + 1e-20),
        )

        return Orientation.from_quaternion(Quaternion.from_data(ans.x))

    def __getstate__(self) -> list[list[float]]:
        return self.data.tolist()

    def __setstate__(self, data: list[list[float]]) -> None:
        self.data = np.array(data)


def func_error_matrix(x0: np.ndarray, quats: list[Quaternion]) -> float:
    total_error: float = 0.0
    for q in quats:
        vec = q.vec
        scal = q.scalar
        I3 = np.eye(3)
        qX = np.array(
            [
                [0, -vec[2], vec[1]],
                [vec[2], 0, -vec[0]],
                [-vec[1], vec[0], 0],
            ]
        )

        err_mtx = np.vstack((scal * I3 + qX, -vec.T))

        w, x, y, z = x0
        total_error += float(np.linalg.norm(np.matmul(err_mtx.T, np.array([x, y, z, w]))) ** 2)

    return total_error
