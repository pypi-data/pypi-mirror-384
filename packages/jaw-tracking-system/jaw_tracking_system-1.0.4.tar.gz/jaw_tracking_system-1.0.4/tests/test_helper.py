"""
Test suite for the jts.helper module.

This suite includes tests for:
- Transformation matrix construction
- Orthonormalization of rotation matrices
- Kabsch algorithm for point set alignment
- Transformation filtering
- Euler angle extraction from rotation matrices
- Relative rotation computation between quaternions
- Interval string conversion
"""

__author__ = "Paul-Otto Müller"
__copyright__ = "Copyright 2025, Paul-Otto Müller"
__credits__ = ["Paul-Otto Müller"]
__license__ = "GNU GPLv3"
__version__ = "1.0.4"
__maintainer__ = "Paul-Otto Müller"
__status__ = "Development"
__date__ = '16.10.2025'
__url__ = "https://github.com/paulotto/jaw_tracking_system"

import numpy as np

from jts import helper as hlp


def test_build_transform():
    """
    Test the build_transform function:
    - Checks that the returned transformation matrix has the correct shape.
    - Verifies that the translation and rotation components are correctly placed.
    - Ensures the homogeneous coordinate is set to 1.
    """
    pos = np.array([1.0, 2.0, 3.0])
    rot = np.eye(3)
    T = hlp.build_transform(pos, rot)
    assert T.shape == (4, 4)
    np.testing.assert_array_equal(T[:3, 3], pos)
    np.testing.assert_array_equal(T[:3, :3], rot)
    assert T[3, 3] == 1.0


def test_ensure_orthonormal():
    """
    Test the ensure_orthonormal function:
    - Checks that the output matrix is orthonormal (R @ R^T = I).
    - Ensures the determinant is close to 1 (proper rotation matrix).
    """
    mat = np.eye(3) + 0.01 * np.random.randn(3, 3)
    ortho = hlp.ensure_orthonormal(mat)
    np.testing.assert_allclose(ortho @ ortho.T, np.eye(3), atol=1e-7)
    assert np.isclose(np.linalg.det(ortho), 1.0, atol=1e-7)


def test_kabsch_algorithm():
    """
    Test the kabsch_algorithm function:
    - Uses two point sets related by a pure translation.
    - Checks that the estimated transform recovers the translation.
    """
    P = np.random.rand(5, 3)
    Q = P + np.array([1.0, 2.0, 3.0])  # pure translation
    T = hlp.kabsch_algorithm(P, Q)
    P_h = np.hstack([P, np.ones((P.shape[0], 1))])
    Q_est = (T @ P_h.T).T[:, :3]
    np.testing.assert_allclose(Q, Q_est, atol=1e-7)


def test_transformation_filter():
    """
    Test the TransformationFilter class:
    - Applies the filter to a sequence of transforms along a straight line.
    - Checks that the smoothed output is close to the original.
    - Verifies output shape.
    """
    N = 21
    T_seq = np.tile(np.eye(4), (N, 1, 1))
    T_seq[:, :3, 3] = np.linspace([0, 0, 0], [10, 0, 0], N)
    filt = hlp.TransformationFilter(window_length=11, poly_order=3)
    T_smooth = filt(T_seq)
    assert T_smooth.shape == (N, 4, 4)

    # Should be close to original for a straight line
    np.testing.assert_allclose(T_seq, T_smooth, atol=1e-2)


def test_rotation_matrix_to_euler_angles():
    """
    Test the rotation_matrix_to_euler_angles function:
    - Checks that the identity matrix yields zero roll, pitch, and yaw.
    """
    R_mat = np.eye(3)
    roll, pitch, yaw = hlp.rotation_matrix_to_euler_angles(R_mat)
    assert np.isclose(roll, 0)
    assert np.isclose(pitch, 0)
    assert np.isclose(yaw, 0)


def test_relative_rotation():
    """
    Test the relative_rotation function:
    - Computes the relative rotation between two quaternions.
    - Checks output shape and expected Euler angles for a 180-degree rotation about x.
    """
    q1 = np.array([1, 0, 0, 0])  # identity quaternion (w, x, y, z)
    q2 = np.array([0, 1, 0, 0])  # 180 deg about x
    q_rel, angles = hlp.relative_rotation(q1, q2, output_format="euler", scalar_first=True)
    assert q_rel.shape == (4,)
    assert angles.shape == (3,)

    # For 180 deg about x, expect roll ~180, pitch/yaw ~0 (modulo sign)
    assert np.isclose(np.abs(angles[0]), 180, atol=1)
    assert np.isclose(angles[1], 0, atol=1)
    assert np.isclose(angles[2], 0, atol=1)


def test_interval_to_string():
    """
    Test the interval_to_string function:
    - Checks that a tuple (5, 10) is converted to the string '5-10'.
    """
    assert hlp.interval_to_string((5, 10)) == '5-10'


def test_store_transformations_scale_and_unit(tmp_path):
    """
    Test that store_transformations applies scale_factor and unit correctly.
    """
    T = np.tile(np.eye(4), (2, 1, 1))
    T[0, :3, 3] = [1, 2, 3]
    T[1, :3, 3] = [4, 5, 6]
    out_file = tmp_path / "test.h5"
    hlp.store_transformations([T], [100], out_file, scale_factor=0.01, unit="cm")
    import h5py
    with h5py.File(out_file, 'r') as f:
        group = f['T_0']
        translations = group['translations'][:]  # type: ignore
        # Should be scaled by 0.01
        np.testing.assert_allclose(translations[0], [0.01, 0.02, 0.03])  # type: ignore
        np.testing.assert_allclose(translations[1], [0.04, 0.05, 0.06])  # type: ignore
        assert group.attrs['unit'] == 'cm'
