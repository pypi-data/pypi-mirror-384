import m3d
import numpy as np

CONVERTION_ERROR = 1000 * m3d.float_eps


def test_transform_mean() -> None:
    trfs = [
        m3d.Transform(
            m3d.Orientation(
                np.array(
                    [
                        [1, 0, 0],
                        [0, 0, -1],
                        [0, 1, 0],
                    ]
                )
            ),
            m3d.Vector(1, 0, 0),
        ),
        m3d.Transform(
            m3d.Orientation(
                np.array(
                    [
                        [0, 0, 1],
                        [0, 1, 0],
                        [-1, 0, 0],
                    ]
                )
            ),
            m3d.Vector(0, 1, 0),
        ),
        m3d.Transform(
            m3d.Orientation(
                np.array(
                    [
                        [0, -1, 0],
                        [1, 0, 0],
                        [0, 0, 1],
                    ]
                )
            ),
            m3d.Vector(0, 0, 1),
        ),
    ]

    mean_trf = m3d.Transform.mean(*trfs)
    assert mean_trf.similar(
        m3d.Transform(
            m3d.Orientation(
                np.array(
                    [
                        [2 / 3, -1 / 3, 2 / 3],
                        [2 / 3, 2 / 3, -1 / 3],
                        [-1 / 3, 2 / 3, 2 / 3],
                    ]
                )
            ),
            m3d.Vector(1 / 3, 1 / 3, 1 / 3),
        ),
        tol=CONVERTION_ERROR,
    )
    assert not mean_trf.similar(
        m3d.Transform.from_pose_vector(*np.mean([trf.pose_vector for trf in trfs], axis=0)),
        tol=CONVERTION_ERROR,
    )


def test_order() -> None:
    trfs = [
        m3d.Transform(
            m3d.Orientation(
                np.array(
                    [
                        [1, 0, 0],
                        [0, 0, -1],
                        [0, 1, 0],
                    ]
                )
            ),
            m3d.Vector(1, 0, 0),
        ),
        m3d.Transform(
            m3d.Orientation(
                np.array(
                    [
                        [0, 0, 1],
                        [0, 1, 0],
                        [-1, 0, 0],
                    ]
                )
            ),
            m3d.Vector(0, 1, 0),
        ),
        m3d.Transform(
            m3d.Orientation(
                np.array(
                    [
                        [0, -1, 0],
                        [1, 0, 0],
                        [0, 0, 1],
                    ]
                )
            ),
            m3d.Vector(0, 0, 1),
        ),
    ]

    m3d.Transform.mean(*trfs).similar(m3d.Transform.mean(*trfs[::-1]))


def test_mean_simple_rotations() -> None:
    mean_ori = m3d.Orientation.mean(m3d.Orientation())
    assert mean_ori.similar(m3d.Orientation(), tol=CONVERTION_ERROR)

    mean_ori = m3d.Orientation.mean(*[m3d.Orientation()] * 5)
    assert mean_ori.similar(m3d.Orientation(), tol=CONVERTION_ERROR)

    mean_ori = m3d.Orientation.mean(
        *[
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, np.pi / 4)),
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, -np.pi / 4)),
        ]
    )
    assert mean_ori.similar(m3d.Orientation(), tol=CONVERTION_ERROR)

    mean_ori = m3d.Orientation.mean(
        *[
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, np.pi / 2)),
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, -np.pi / 2)),
        ]
    )
    assert mean_ori.similar(m3d.Orientation(), tol=CONVERTION_ERROR)


def test_rotation_direction() -> None:
    mean_ori = m3d.Orientation.mean(
        *[
            m3d.Orientation(),
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, 3 * np.pi / 2)),
        ]
    )
    assert mean_ori.similar(m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, 7 * np.pi / 4)), tol=CONVERTION_ERROR)

    mean_ori = m3d.Orientation.mean(
        *[
            m3d.Orientation(),
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, np.pi / 2)),
        ]
    )
    assert mean_ori.similar(m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, np.pi / 4)), tol=CONVERTION_ERROR)

    mean_ori = m3d.Orientation.mean(
        *[
            m3d.Orientation(),
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, np.pi)),
        ]
    )
    assert mean_ori.similar(
        m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, np.pi / 2)), tol=CONVERTION_ERROR
    ) or mean_ori.similar(m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, 3 * np.pi / 2)), tol=CONVERTION_ERROR)

    mean_ori = m3d.Orientation.mean(
        *[
            m3d.Orientation(),
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, np.pi / 2)),
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, np.pi)),
        ]
    )
    assert mean_ori.similar(m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, np.pi / 2)), tol=CONVERTION_ERROR)

    mean_ori = m3d.Orientation.mean(
        *[
            m3d.Orientation(),
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, np.pi)),
            m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, 3 * np.pi / 2)),
        ]
    )
    assert mean_ori.similar(m3d.Orientation.from_rotation_vector(m3d.Vector(0, 0, 3 * np.pi / 2)), tol=CONVERTION_ERROR)


def test_equal_weights_vector() -> None:
    vectors = [
        m3d.Vector(0, 0, 0),
        m3d.Vector(2, 2, 2),
    ]

    assert m3d.Vector.mean(*vectors, weights=[1, 1]).similar(m3d.Vector.mean(*vectors))
    assert m3d.Vector.mean(*vectors, weights=[1, 1]).similar(m3d.Vector.mean(*vectors, weights=[2, 2]))


def test_zero_weight_vector() -> None:
    vectors = [
        m3d.Vector(0, 0, 0),
        m3d.Vector(2, 2, 2),
    ]

    assert m3d.Vector().similar(m3d.Vector.mean(*vectors, weights=[1, 0]))
    assert m3d.Vector().similar(m3d.Vector.mean(*vectors, weights=[0.5, 0]))


def test_weighted_vector() -> None:
    vectors = [
        m3d.Vector(0, 0, 0),
        m3d.Vector(3, 3, 3),
    ]
    weights = [2, 1]

    assert m3d.Vector.mean(*vectors, weights=weights).similar(m3d.Vector(1, 1, 1))
