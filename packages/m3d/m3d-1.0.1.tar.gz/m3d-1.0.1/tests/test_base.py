import pickle

import numpy as np

import pytest
import m3d

# when exporting and reimporting a transform to another expression we must accept a higher error then eps
CONVERTION_ERROR = 1000 * m3d.float_eps


def _are_equals(
    m1: float | np.ndarray | m3d.Vector | m3d.Orientation | m3d.Transform,
    m2: float | np.ndarray | m3d.Vector | m3d.Orientation | m3d.Transform,
    eps: float = m3d.float_eps,
) -> bool:
    """
    to test equality of two objects with a tolerance
    """
    if isinstance(m1, float | np.float32) and isinstance(m2, float | np.float32):
        return abs(m1 - m2) < eps

    m1 = _to_np(m1)
    m2 = _to_np(m2)

    return (abs(m1 - m2) <= eps).all()


def _to_np(obj: float | np.ndarray | m3d.Vector | m3d.Orientation | m3d.Transform) -> np.ndarray:
    if isinstance(obj, np.ndarray):
        return obj
    if isinstance(obj, m3d.Vector | m3d.Orientation | m3d.Transform):
        return obj.data
    raise ValueError("Could not convert obj to numpy array", obj, type(obj))


def test_init() -> None:
    t = m3d.Transform()
    assert t.pos.x == 0
    assert t.pos.y == 0
    t.pos.x = 2
    assert t.pos.x == 2

    i = t.inverse()
    assert m3d.Vector(-2, 0, 0) == i.pos
    assert m3d.Orientation() == i.orient


def test_transform_init() -> None:
    v = m3d.Vector(1, 2, 3)
    o = m3d.Orientation()
    o.rotate_zb(1)
    t = m3d.Transform(o, v)
    assert t.pos == v
    assert t.orient == o
    I4 = np.eye(4)
    I4[:3, :3] = o.data
    I4[:3, 3] = v.data
    t2 = m3d.Transform.from_data(I4)
    assert t2.pos == v
    assert t2.orient == o
    assert t == t2


def test_transform_init_ref() -> None:
    v = m3d.Vector(1, 2, 3)
    o = m3d.Orientation()
    o.rotate_zb(1)
    t = m3d.Transform(o, v)
    assert t.orient == o
    o.rotate_xb(1)
    assert t.orient != o


def test_rotation() -> None:
    t = m3d.Transform()
    t.pos.x = 1
    t.orient.rotate_yb(1)
    res = m3d.Transform(
        m3d.Orientation(
            np.array(
                [
                    [0.54030228, 0, 0.84147096],
                    [0.0, 1, 0.0],
                    [-0.84147096, 0.0, 0.54030228],
                ]
            )
        ),
        m3d.Vector(1, 0, 0),
    )
    assert _are_equals(res.data, t.data)


def test_multiplication_orient() -> None:
    o = m3d.Orientation()
    o.rotate_zb(np.pi / 2)
    v = m3d.Vector(1, 0, 0)
    r = o * v
    assert r == m3d.Vector(0, 1, 0)
    o.rotate_zb(-np.pi)
    v = m3d.Vector(2, 0, 0)
    r = o * v
    assert r == m3d.Vector(0, -2, 0)


def test_transform() -> None:
    t = m3d.Transform()
    t.orient.rotate_zb(np.pi / 2)
    t.pos.y = 2
    v = m3d.Vector(1, 0, 0)
    r = t * v
    assert r == m3d.Vector(0, 3, 0)


def test_pose_vector() -> None:
    t = m3d.Transform()
    t.pos.x = 1
    t.pos.z = 2
    t.orient.rotate_yb(1)
    v = t.to_pose_vector()
    t2 = t.from_pose_vector(*v)
    assert t == t2


def test_rotation_vector() -> None:
    o = m3d.Orientation()
    o.rotate_yb(1)
    o.rotate_zb(1)
    v = o.to_rotation_vector()
    o2 = m3d.Orientation.from_rotation_vector(v)
    assert o.similar(o2, CONVERTION_ERROR)


def test_rotation_vector_2() -> None:
    o = m3d.Orientation()
    o.rotate_yb(1.1)
    v = o.to_rotation_vector()
    assert _are_equals(v[1], 1.1)
    o = m3d.Orientation()
    o.rotate_zb(1.1)
    v = o.to_rotation_vector()
    assert _are_equals(v[2], 1.1)
    o = m3d.Orientation()
    o.rotate_xb(1.1)
    v = o.to_rotation_vector()
    assert _are_equals(v[0], 1.1)


def test_vec_eq() -> None:
    a = m3d.Vector(-1.0000001192092896, -1.9999998807907104, -3.0)
    b = m3d.Vector(-1.0, -2.0, -3.0)
    assert a == b


def test_mult_trans() -> None:
    t1 = m3d.Transform()
    t1.orient.rotate_xb(np.pi / 2)
    t1.pos.x = 1

    t2 = m3d.Transform()
    t2.orient.rotate_xb(np.pi / 2)
    t2.pos.x = 2

    v = m3d.Vector(0, 0, 3)

    tr = m3d.Transform()
    tr.orient.rotate_xb(np.pi)
    tr.pos.x = 3

    assert t1 * t2 * v == tr * v
    assert t1 @ t2 @ v == tr @ v


def test_equal() -> None:
    t1 = m3d.Transform()
    t1.orient.rotate_xb(np.pi / 2)
    t1.pos.x = 1

    t2 = m3d.Transform()
    t2.orient.rotate_xb(np.pi / 2)
    t2.pos.x = 2

    tr = m3d.Transform()
    tr.orient.rotate_xb(np.pi)
    tr.pos.x = 3

    assert t1 != t2
    assert t1 != tr
    assert t1 * t2 == tr
    assert t2 * t1 == tr


def test_inverse_orient() -> None:
    o = m3d.Orientation()
    o.rotate_xb(3)
    o.rotate_yb(1)
    o.rotate_xb(1)
    v = m3d.Vector(-1, -2, -3)
    assert o * v != v
    assert o.inverse() * o * v == v
    assert o * o.inverse() * v == v
    assert o * o.inverse() * o == o


def test_inverse_trans() -> None:
    t = m3d.Transform()
    t.pos.x = 1
    t.orient.rotate_zb(np.pi / 2)
    t.orient.rotate_yb(np.pi / 2)
    v = m3d.Vector(2, 0, 0)
    assert t * v == m3d.Vector(1, 2, 0)


def test_inverse_invert() -> None:
    t = m3d.Transform()
    t.orient.rotate_xb(np.pi / 3)
    t.pos.x = 1
    t1 = t.copy()
    t2 = t1.inverse()
    assert not _are_equals(t1, t2)
    t1.invert()
    assert _are_equals(t1, t2)
    assert _are_equals(t * t1, m3d.Transform())


def test_inverse() -> None:
    t1 = m3d.Transform()
    t1.orient.rotate_xb(np.pi / 3)
    t1.pos.x = 1

    t2 = m3d.Transform()
    t2.orient.rotate_xb(-13 * np.pi / 6)
    t2.pos.x = 2.3

    v = m3d.Vector(0.1, -4.5, 3.0)

    tr = m3d.Transform()
    tr.orient.rotate_xb(np.pi)
    tr.pos.x = 3

    assert (t1 * t1.inverse()) == m3d.Transform.identity()
    assert (t1 * t1.inverse()) == m3d.Transform()
    assert (t2 * t2.inverse()) == m3d.Transform.identity()
    assert (t2 * t2.inverse()) == m3d.Transform()
    assert (t1 * t2 * t1.inverse() * t2.inverse()).similar(m3d.Transform.identity(), CONVERTION_ERROR)
    assert t1.inverse() * (t1 * v) == v


def test_inverse_2() -> None:
    t = m3d.Transform()
    t.pos.x = 1
    t.pos.z = 3
    t.orient.rotate_yb(1)
    t.orient.rotate_zb(1)
    v = m3d.Vector(2, 3, 4)
    assert v != t * v
    assert v == t.inverse() * t * v
    assert v == t * t.inverse() * v
    assert v != t @ v
    assert v == t.inverse() @ t @ v
    assert v == t @ t.inverse() @ v


def test_rotation_seq() -> None:
    t = m3d.Transform()
    t.pos.x = 1
    t.pos.z = 3
    t.orient.rotate_xb(1)
    res = t.copy()
    t.orient.rotate_yb(2)
    t.orient.rotate_zb(3)
    t.orient.rotate_zb(-3)
    t.orient.rotate_yb(-2)
    assert t == res


def test_rotation_seq_2() -> None:
    t = m3d.Transform()
    t.pos.x = 1
    t.pos.z = 3
    t.orient.rotate_xb(1)
    t.orient.rotate_yb(2)
    t.orient.rotate_zb(3)

    b = m3d.Transform()
    b.orient.rotate_zb(-3)
    b.orient.rotate_yb(-2)
    b.orient.rotate_xb(-1)
    b.pos = b.orient * m3d.Vector(1, 0, 3) * -1

    assert _are_equals(t.inverse().data, b.data)


def test_rotation_t() -> None:
    t = m3d.Transform()
    t.pos.x = 1
    t.orient.rotate_zt(np.pi / 2)
    t.orient.rotate_yt(np.pi / 2)
    v = m3d.Vector(2, 0, 0)
    assert t * v == m3d.Vector(1, 0, -2)


def test_rotation_t_2() -> None:
    t = m3d.Transform()
    t.orient.rotate_yt(-np.pi / 2)
    t.orient.rotate_xt(np.pi / 3)
    v = m3d.Vector(2, 0, 0)
    assert t * v == m3d.Vector(0, 0, 2)


def test_construct() -> None:
    o = m3d.Orientation()
    o.rotate_zb(1)
    v = m3d.Vector()
    v[0] = 1
    v[2] = 2
    t = m3d.Transform(o, v)
    assert t.pos.x == 1
    assert t.pos.z == 2
    t.pos = m3d.Vector()
    t.orient.rotate_zb(-1)
    assert t == m3d.Transform()
    t.orient = o
    assert t != m3d.Transform()


def test_orient() -> None:
    o = m3d.Orientation()
    o.rotate_zb(2)
    o2 = m3d.Orientation()
    o2.rotate_zb(2 * np.pi)
    assert o * o2 == o


def test_quaternion() -> None:
    o = m3d.Orientation()
    o.rotate_xb(np.pi / 3)
    o.rotate_zb(np.pi / 3)
    q = o.to_quaternion()
    o2 = m3d.Orientation.from_quaternion(q)
    assert o.similar(o2, CONVERTION_ERROR)
    o = m3d.Orientation()
    o2 = m3d.Orientation.from_quaternion(m3d.Quaternion(0.0, 0.0, 0.0, 0.0))
    assert o.similar(o2, CONVERTION_ERROR)


def test_axis_angle() -> None:
    o = m3d.Orientation()
    o.rotate_xb(np.pi / 3)
    o.rotate_zb(np.pi / 3)
    v, a = o.to_axis_angle()
    o2 = m3d.Orientation.from_axis_angle(v, a)
    assert o.similar(o2, CONVERTION_ERROR)


def test_from_axis_angle() -> None:
    axis_tuple = (1, 2, 3)
    axis_normalized = m3d.Vector(*axis_tuple).normalized()
    angle = 10

    o1 = m3d.Orientation.from_axis_angle(m3d.Vector(*axis_tuple), angle)
    o2 = m3d.Orientation.from_axis_angle(m3d.Vector(axis_normalized.x, axis_normalized.y, axis_normalized.z), angle)
    assert o1.similar(o2, CONVERTION_ERROR)


def test_pc() -> None:
    pc = np.array([[1, 2, 3], [1, 2, 3], [2, 3, 4], [3, 4, 5], [3, 4, 5]])
    pc = pc.T
    t = m3d.Transform()
    t.pos.x = 1.2
    t.pos.y = 1
    t.orient.rotate_yb(1)
    t.orient.rotate_zb(1)

    a = t * pc
    assert a.shape == pc.shape

    c = t * pc.T
    assert c.shape == pc.T.shape


def test_copy() -> None:
    t = m3d.Transform()
    t.pos.x = 1
    new = t.copy()
    t.orient.rotate_zb(1)
    new.pos.x = 5
    assert t.pos.x != new.pos.x
    assert t.orient.data[0, 0] != new.orient.data[0, 0]
    v = t.pos.copy()
    assert v == t.pos
    v[1] = 3.33
    assert v.y != t.pos.y
    assert v != t.pos


def test_vect_mul() -> None:
    v1 = m3d.Vector(10, 10, 10)
    const_val = 2
    const_val_2 = -5
    v_res = v1 * const_val
    v_res_2 = v1 * const_val_2
    assert v_res == m3d.Vector(20, 20, 20)
    assert v_res_2 == m3d.Vector(-50, -50, -50)


def test_vect_div() -> None:
    v1 = m3d.Vector(10, 10, 10)
    const_val = 2
    const_val_2 = -5
    v_res = v1 / const_val
    v_res_2 = v1 / const_val_2
    assert v_res == m3d.Vector(5, 5, 5)
    assert v_res_2 == m3d.Vector(-2, -2, -2)


def test_substraction() -> None:
    v1 = m3d.Vector(1, 2, 3)
    v2 = m3d.Vector(2, -3, 4)
    v_res = v2 - v1
    assert v_res == m3d.Vector(1, -5, 1)


def test_addition() -> None:
    v1 = m3d.Vector(1, 2, 3)
    v2 = m3d.Vector(2, -3, 4)
    v_res = v2 + v1
    assert v_res == m3d.Vector(3, -1, 7)


def test_dist() -> None:
    v1 = m3d.Vector(1, 1, 1)
    v2 = m3d.Vector(2, 2, 2)
    v_res = v2.dist(v1)
    assert v_res == m3d.Vector(1, 1, 1).length


def test_ang_dist() -> None:
    o1 = m3d.Orientation()
    o1.rotate_yb(1)
    o1.rotate_xb(1)
    o1.rotate_zb(1)

    o2 = m3d.Orientation()
    o2.rotate_yb(2)
    o2.rotate_xb(2)
    o2.rotate_zb(2)

    o_dist_m3d = o1.ang_dist(o2)
    o_inv_dist_m3d = o2.ang_dist(o1)

    assert abs(o_dist_m3d - o_inv_dist_m3d) <= m3d.float_eps


def test_trans_dist() -> None:
    a = m3d.Transform()
    b = m3d.Transform()
    b.pos.x = 3
    b.orient.rotate_zb(1)
    b.orient.rotate_yb(1)
    assert a.dist(b) > 0.1
    assert b.dist(b) == 0


def test_eq() -> None:
    t = m3d.Transform()
    t.orient.rotate_yb(1)
    t.orient.rotate_zb(1)
    t.pos.x = 1
    v = m3d.Vector()
    o = m3d.Orientation()
    assert t != v
    assert v != t
    assert o != v
    t2 = t.copy()
    assert t == t2
    assert t.pos == t2.pos
    assert t.orient == t2.orient
    t2.pos.y = 2
    assert t != t2
    assert t.pos != t2.pos
    assert t.orient == t2.orient
    t3 = t.copy()
    t3.orient.rotate_xb(1)
    assert t2.pos != t3.pos
    assert t2.orient != t3.orient
    assert t != t3


def test_norm() -> None:
    v = m3d.Vector(1, 2, 3)
    v.normalize()
    assert abs(v.length - 1) <= m3d.float_eps


def test_from_xy() -> None:
    x = m3d.Vector(1, 0, 0)
    y = m3d.Vector(0.01, 2.1, 0)
    orient = m3d.Orientation.from_xy(x, y)
    assert _are_equals(orient.data, np.identity(3), eps=0.1)


def test_from_yz() -> None:
    y = m3d.Vector(0, 1, 0)
    z = m3d.Vector(0, 0.01, 0.1)
    orient = m3d.Orientation.from_yz(y, z)
    assert _are_equals(orient.data, np.identity(3), eps=0.1)


def test_from_xz() -> None:
    x = m3d.Vector(1, 0, 0)
    z = m3d.Vector(0, 0, 1)
    orient = m3d.Orientation.from_xz(x, z)
    assert _are_equals(orient.data, np.identity(3))

    x = m3d.Vector(2, 0, 0.1)
    z = m3d.Vector(0.1, -0.1, 3)
    o = m3d.Orientation()
    o.rotate_yb(1)
    o.rotate_zb(1)
    x = o @ x
    z = o @ z
    orient = m3d.Orientation.from_xz(x, z)
    assert _are_equals(o, orient, eps=0.1)


def test_null_rotation_vector() -> None:
    o = m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, 0))
    assert np.array_equal(o.data, np.identity(3))


def test_update_trans_xyz() -> None:
    t = m3d.Transform()
    t.orient.rotate_yb(1)
    t.orient.rotate_zb(1)
    t.pos.x = 1

    t.pos.x += 1.2
    assert _are_equals(t.pos.x, 2.2)
    assert _are_equals(t.data[0, 3], 2.2)
    t.pos.y += 1.2
    assert _are_equals(t.pos.y, 1.2)
    assert _are_equals(t.data[1, 3], 1.2)


def test_similar() -> None:
    t = m3d.Transform()
    t.pos.x = 1
    t.pos.y = 2
    t.pos.z = 3
    t.orient.rotate_yb(1)

    t2 = t.copy()
    t2.orient.rotate_zb(1)

    t3 = t.copy()
    t3.orient.rotate_zb(1 - 4 * np.pi)

    t4 = t3.copy()
    t4.pos.x += m3d.float_eps

    t5 = t4.copy()
    t5.pos.x += 0.1

    assert not t.similar(t2)
    assert t2.similar(t3)
    assert t3.similar(t4)
    assert t2.similar(t4)
    assert t4.similar(t2)
    assert t4.orient.similar(t2.orient)
    assert not t.similar(t4)
    assert not t.orient.similar(t4.orient)
    assert not t4.similar(t)
    assert not t4.similar(t5)
    assert not t.similar(t5)
    assert t4.pos.similar(t5.pos, 0.2)
    assert t4.orient.similar(t5.orient, 0.2)
    assert t4.similar(t5, 0.2)


def test_orient_except() -> None:
    with pytest.raises(ValueError):
        o = m3d.Orientation(np.identity(4))
    o = m3d.Orientation()
    with pytest.raises(ValueError):
        o * np.identity(4)


def test_unit_vectors() -> None:
    assert m3d.vector.e0 == m3d.Vector(1, 0, 0)
    assert m3d.vector.e1 == m3d.Vector(0, 1, 0)
    assert m3d.vector.e2 == m3d.Vector(0, 0, 1)
    t = m3d.Transform()
    assert m3d.vector.ex == t.orient.vec_x
    assert m3d.vector.ey == t.orient.vec_y
    assert m3d.vector.ez == t.orient.vec_z
    t.orient.rotate_zb(1)
    assert m3d.vector.ex != t.orient.vec_x
    assert m3d.vector.ey != t.orient.vec_y
    assert m3d.vector.ez == t.orient.vec_z


def test_vector_dot() -> None:
    d1 = np.array([1, 2, -3])
    d2 = np.array([2, 2, 2])
    v1 = m3d.Vector.from_data(d1)
    v2 = m3d.Vector.from_data(d2)
    assert np.dot(d1, d2) == v1.dot(v2)
    assert v1.dot(v2) == v1 @ v2
    assert v1 @ v1 == v1.length**2


def test_vector_project() -> None:
    v1 = m3d.Vector(1, 1, 1)
    v2 = m3d.Vector(2, 2, 2)

    vx = m3d.Vector(1, 0, 0)
    vy = m3d.Vector(0, 1, 0)
    vz = m3d.Vector(0, 0, 1)

    assert v1.project(vx) == vx
    assert v1.project(vy) == vy
    assert v1.project(vz) == vz

    assert v1.project(v2) == v1
    assert v2.project(v1) == v2


def test_vector_angle() -> None:
    v1 = m3d.Vector(1, 1, 1)
    v2 = m3d.Vector(2, 2, 2)

    vx = m3d.Vector(1, 0, 0)
    vy = m3d.Vector(0, 1, 0)
    vz = m3d.Vector(0, 0, 1)

    assert vx.angle(vx) == 0
    assert vx.angle(vy) == np.pi / 2
    assert vx.angle(vz) == np.pi / 2

    assert v1.angle(v2) == 0
    assert v2.angle(v1) == 0


def test_vector_angle_perp() -> None:
    v1 = m3d.Vector(1, 0, 0)
    v2 = m3d.Vector(1, 1, 0)
    v3 = m3d.Vector(1, -1, 0)

    vx = m3d.Vector(1, 0, 0)
    vy = m3d.Vector(0, 1, 0)
    vz = m3d.Vector(0, 0, 1)

    assert vx.angle(vx, vz) == 0
    assert vx.angle(vy, vz) == np.pi / 2
    assert vx.angle(vz, vy) == -np.pi / 2

    # Flip nominal direction for perpendicular vector
    assert vx.angle(vx, -vz) == 0
    assert vx.angle(vy, -vz) == -np.pi / 2
    assert vx.angle(vz, -vy) == np.pi / 2

    assert v1.angle(v2, vz) == -v1.angle(v2, -vz)
    assert v1.angle(v2, vz) == v1.angle(v3, -vz)


def test_dual_quaternion_unit_condition() -> None:
    for _ in range(20):
        t = m3d.Transform.from_pose_vector(*np.random.default_rng().random(6))
        dq = m3d.DualQuaternion.from_transformation(t)
        assert dq.unity_condition


def test_frozen_vector() -> None:
    v = m3d.Vector(1, 2, 3, frozen=True)
    with pytest.raises(ValueError):
        v.x = 1
    with pytest.raises(ValueError):
        v /= 2
    v.frozen = False
    v.x = 9
    v.frozen = True
    with pytest.raises(ValueError):
        v.x = 1
    assert v.x == 9


def test_frozen_transform() -> None:
    t = m3d.Transform(frozen=True)
    with pytest.raises(ValueError):
        t.orient.rotate_yb(1)
    with pytest.raises(ValueError):
        t.pos.x = 1
    t.frozen = False
    t.pos.x = 1
    t.frozen = True
    with pytest.raises(ValueError):
        t.pos.x = 2
    assert t.pos.x == 1
    t.frozen = False


def test_frozen_orient() -> None:
    o = m3d.Orientation(frozen=True)
    with pytest.raises(ValueError):
        o.rotate_yb(1)
    o.frozen = False
    o.rotate_yb(1)
    o.frozen = True
    with pytest.raises(ValueError):
        o.rotate_yb(1)


def test_adjoint_transformation() -> None:
    """
    The correct values are and can be deduced intuitively
    """
    ft = np.array([1, 2, 3, 0.1, 0.2, 0.3])
    trf = m3d.Transform.from_data(
        np.array(
            [
                [1, 0, 0, 0],
                [0, -1, 0, 0],
                [0, 0, -1, 0],
                [0, 0, 0, 1],
            ]
        )
    )

    np.testing.assert_almost_equal(
        trf.as_adjoint() @ ft,
        np.array([ft[0], -ft[1], -ft[2], ft[3], -ft[4], -ft[5]]),
    )

    x = 0.1
    y = 0.2
    trf = m3d.Transform.from_data(
        np.array(
            [
                [1, 0, 0, x],
                [0, 1, 0, y],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ]
        )
    )

    np.testing.assert_almost_equal(
        trf.as_adjoint() @ ft,
        np.array([ft[0], ft[1], ft[2], ft[3] + y * ft[2], ft[4] - x * ft[2], ft[5] + x * ft[1] - y * ft[0]]),
    )


def test_valid_nan() -> None:
    t = m3d.Transform()
    assert t.is_valid()
    t.data[1, 0] = np.nan
    assert not t.is_valid()


def test_valid_0() -> None:
    t = m3d.Transform()
    assert t.is_valid()
    t.data[3, 1] = 0.01
    assert not t.is_valid()


def test_valid_1() -> None:
    t = m3d.Transform()
    assert t.is_valid()
    t.data[3, 3] = 0.99
    assert not t.is_valid()


def test_valid_and_invalid_rotation_matrices() -> None:
    reflection = m3d.Orientation(
        data=np.array(
            [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, -1],
            ]
        )
    )

    for i in range(1000):
        valid_orient = m3d.Orientation.from_rotation_vector(m3d.Vector(*np.random.default_rng().random(3)))
        assert valid_orient.is_valid()

        invalid_orient = valid_orient * reflection
        assert not invalid_orient.is_valid()


def test_valid_rotation() -> None:
    t = m3d.Transform()
    assert t.is_valid()
    t.orient.rotate_xb(1)
    t.orient.rotate_yt(-1)
    assert t.is_valid()
    t.data[0, 0] = 2
    assert not t.is_valid()


def test_transform_from_corresponding_points() -> None:
    p1 = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
        ]
    )
    t = m3d.Transform.from_pose_vector(0.0, 1.0, 2.0, 0.1, 0.2, 0.3)
    p2 = t * p1
    t2 = m3d.Transform.from_corresponding_points(p1, p2)
    assert t == t2


def test_rotated() -> None:
    identity = m3d.Transform()
    assert identity.rotated_zb(np.pi).similar(identity.rotated_zt(np.pi))

    X = m3d.Transform(pos=m3d.Vector(x=1.0))
    X_rot_b = X.rotated_zb(np.pi)
    X_rot_t = X.rotated_zt(np.pi)

    assert X_rot_t.pos.similar(X.pos)
    assert not X_rot_b.pos.similar(X.pos)
    assert not X_rot_t.orient.similar(X.orient)
    assert X_rot_b.orient.similar(X_rot_t.orient)


def test_translated() -> None:
    identity = m3d.Transform()
    assert identity.translated_zb(0.5).similar(identity.translated_zt(0.5))

    X = m3d.Transform(m3d.Orientation.from_x_rotation(np.pi))
    X_trans_b = X.translated_zb(0.5)
    X_trans_t = X.translated_zt(0.5)

    assert abs(X_trans_b.dist(X_trans_t) - 1.0) < m3d.float_eps


def test_pickle_vector() -> None:
    v1 = m3d.Vector(0.123, 1.232, -7.2)
    v2 = pickle.loads(pickle.dumps(v1))
    assert v1 == v2


def test_pickle_transform() -> None:
    t1 = m3d.Transform.from_pose_vector(0.0, 1.0, 2.0, 0.1, 0.2, 0.3)
    t2 = pickle.loads(pickle.dumps(t1))
    assert t1 == t2


def test_pickle_orient() -> None:
    o1 = m3d.Orientation(
        np.array(
            [
                [0.54030228, 0, 0.84147096],
                [0.0, 1, 0.0],
                [-0.84147096, 0.0, 0.54030228],
            ]
        )
    )
    o2 = pickle.loads(pickle.dumps(o1))
    assert o1 == o2


def test_pickle_quaternion() -> None:
    o = m3d.Orientation()
    o.rotate_xb(np.pi / 3)
    o.rotate_zb(np.pi / 3)
    q1 = o.to_quaternion()
    q2 = pickle.loads(pickle.dumps(q1))
    o2 = m3d.Orientation.from_quaternion(q2)
    assert _are_equals(o, o2)


def test_pickle_dual_quaternion() -> None:
    t1 = m3d.Transform.from_pose_vector(0.0, 1.0, 2.0, 0.1, 0.2, 0.3)
    dq1 = m3d.DualQuaternion.from_transformation(t1)
    dq2 = pickle.loads(pickle.dumps(dq1))
    assert _are_equals(dq1.data, dq2.data)
