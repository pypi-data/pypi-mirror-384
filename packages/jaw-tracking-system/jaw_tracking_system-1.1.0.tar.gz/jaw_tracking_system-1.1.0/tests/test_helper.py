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
__version__ = "1.1.0"
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


def test_inspect_hdf5(tmp_path):
    """
    Test the inspect_hdf5 function:
    - Checks that file inspection returns correct structure information
    - Verifies metadata, sample rate, unit, and dataset information
    - Tests verbose and non-verbose modes
    """
    # Create test HDF5 file
    N = 50
    T_t = np.zeros((N, 4, 4))
    T_t[:, :3, :3] = np.eye(3)
    T_t[:, :3, 3] = np.random.randn(N, 3) * 10
    T_t[:, 3, 3] = 1.0
    
    test_file = tmp_path / "test_inspect.h5"
    hlp.store_transformations(
        [T_t], [200.0], test_file,
        metadata=['Test trajectory for inspection'],
        group_names=['test_group'],
        derivative_order=2
    )
    
    # Test non-verbose mode
    info = hlp.inspect_hdf5(test_file, verbose=False)
    
    assert 'test_group' in info
    assert info['test_group']['sample_rate'] == 200.0
    assert info['test_group']['num_frames'] == N
    assert info['test_group']['rotation_format'] == 'quaternion'
    assert info['test_group']['derivative_order'] == 2
    assert 'translations' in info['test_group']['datasets']
    assert 'rotations' in info['test_group']['datasets']
    
    # Test verbose mode (should not raise errors)
    info_verbose = hlp.inspect_hdf5(test_file, verbose=True)
    assert info_verbose == info


def test_load_hdf5_transformations_as_matrices(tmp_path):
    """
    Test load_hdf5_transformations with as_matrices=True:
    - Verifies that quaternions are converted to rotation matrices
    - Checks that 4x4 transformation matrices are constructed correctly
    - Ensures translations, rotations, and metadata are loaded properly
    """
    # Create test data
    N = 30
    T_t = np.zeros((N, 4, 4))
    for i in range(N):
        # Random rotation
        angle = i * 0.1
        rot = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1]
        ])
        T_t[i, :3, :3] = rot
        T_t[i, :3, 3] = [i, i*2, i*3]
        T_t[i, 3, 3] = 1.0
    
    test_file = tmp_path / "test_load_matrices.h5"
    hlp.store_transformations(
        [T_t], [100.0], test_file,
        metadata=['Test data'],
        group_names=['trajectory'],
        store_as_quaternion=True
    )
    
    # Load with as_matrices=True
    data = hlp.load_hdf5_transformations(test_file, as_matrices=True)
    
    assert 'trajectory' in data
    assert data['trajectory']['transformations'].shape == (N, 4, 4)
    assert data['trajectory']['translations'].shape == (N, 3)
    assert data['trajectory']['rotations'].shape == (N, 3, 3)
    assert data['trajectory']['sample_rate'] == 100.0
    assert data['trajectory']['metadata'] == 'Test data'
    
    # Check that transformations are close to original
    np.testing.assert_allclose(
        data['trajectory']['transformations'],
        T_t,
        rtol=1e-5, atol=1e-6
    )


def test_load_hdf5_transformations_as_quaternions(tmp_path):
    """
    Test load_hdf5_transformations with as_matrices=False:
    - Verifies that quaternions are loaded without conversion
    - Checks shape and format of quaternion data
    """
    N = 20
    T_t = np.tile(np.eye(4), (N, 1, 1))
    T_t[:, :3, 3] = np.random.randn(N, 3) * 5
    
    test_file = tmp_path / "test_load_quat.h5"
    hlp.store_transformations(
        [T_t], [150.0], test_file,
        group_names=['quat_trajectory'],
        store_as_quaternion=True
    )
    
    # Load with as_matrices=False
    data = hlp.load_hdf5_transformations(test_file, as_matrices=False)
    
    assert 'quat_trajectory' in data
    assert data['quat_trajectory']['rotations'].shape == (N, 4)  # Quaternions
    assert 'transformations' not in data['quat_trajectory']  # Not constructed


def test_load_hdf5_transformations_specific_group(tmp_path):
    """
    Test loading a specific group from HDF5 file:
    - Creates file with multiple groups
    - Loads only one specific group
    - Verifies only requested group is loaded
    """
    N = 25
    T1 = np.tile(np.eye(4), (N, 1, 1))
    T1[:, :3, 3] = np.random.randn(N, 3)
    
    T2 = np.tile(np.eye(4), (N, 1, 1))
    T2[:, :3, 3] = np.random.randn(N, 3) * 2
    
    test_file = tmp_path / "test_multi_group.h5"
    hlp.store_transformations(
        [T1, T2], [100.0, 100.0], test_file,
        group_names=['group1', 'group2']
    )
    
    # Load only group1
    data = hlp.load_hdf5_transformations(test_file, group_name='group1')
    
    assert 'group1' in data
    assert 'group2' not in data
    assert data['group1']['transformations'].shape == (N, 4, 4)


def test_load_hdf5_transformations_with_derivatives(tmp_path):
    """
    Test loading transformations with derivatives:
    - Stores transformations with derivative_order=2
    - Verifies derivatives are loaded in the derivatives dictionary
    """
    N = 40
    T_t = np.tile(np.eye(4), (N, 1, 1))
    T_t[:, :3, 3] = np.random.randn(N, 3) * 10
    
    test_file = tmp_path / "test_derivatives.h5"
    hlp.store_transformations(
        [T_t], [200.0], test_file,
        group_names=['with_derivatives'],
        derivative_order=2
    )
    
    data = hlp.load_hdf5_transformations(test_file)
    
    assert 'with_derivatives' in data
    assert 'derivatives' in data['with_derivatives']
    derivs = data['with_derivatives']['derivatives']
    
    # Check that derivatives exist
    assert 'translational_derivative_order_1' in derivs
    assert 'translational_derivative_order_2' in derivs
    assert 'rotational_derivative_order_1' in derivs
    assert 'rotational_derivative_order_2' in derivs


def test_visualize_hdf5_trajectory(tmp_path):
    """
    Test visualize_hdf5_trajectory function:
    - Creates a simple trajectory
    - Visualizes it and checks that Figure and Axes are returned
    - Tests with and without coordinate frames
    - Tests saving to file
    """
    # Create test trajectory
    N = 100
    t = np.linspace(0, 2*np.pi, N)
    T_t = np.zeros((N, 4, 4))
    
    for i, theta in enumerate(t):
        T_t[i, :3, 3] = [np.cos(theta)*10, np.sin(theta)*10, theta]
        T_t[i, :3, :3] = np.eye(3)
        T_t[i, 3, 3] = 1.0
    
    test_file = tmp_path / "test_viz.h5"
    hlp.store_transformations(
        [T_t], [100.0], test_file,
        group_names=['helix_trajectory']
    )
    
    # Test visualization without saving
    fig, ax = hlp.visualize_hdf5_trajectory(
        test_file,
        group_name='helix_trajectory',
        frame_step=20,
        show_frames=True,
        frame_scale=2.0
    )
    
    import matplotlib.pyplot as plt
    assert fig is not None
    assert ax is not None
    plt.close(fig)
    
    # Test visualization with saving
    save_path = tmp_path / "trajectory_plot.png"
    fig2, ax2 = hlp.visualize_hdf5_trajectory(
        test_file,
        frame_step=0,  # No frames
        show_frames=False,
        save_path=save_path,
        title="Test Trajectory"
    )
    
    assert save_path.exists()
    plt.close(fig2)


def test_compare_hdf5_trajectories_translations(tmp_path):
    """
    Test compare_hdf5_trajectories with translations:
    - Creates raw and smoothed trajectories
    - Compares them using 'translations' component
    - Verifies Figure with 3 subplots is returned
    """
    N = 80
    
    # Raw trajectory (with noise)
    T_raw = np.zeros((N, 4, 4))
    T_raw[:, :3, 3] = np.column_stack([
        np.linspace(0, 10, N) + np.random.randn(N) * 0.5,
        np.linspace(0, 5, N) + np.random.randn(N) * 0.3,
        np.linspace(0, 3, N) + np.random.randn(N) * 0.2
    ])
    T_raw[:, :3, :3] = np.eye(3)
    T_raw[:, 3, 3] = 1.0
    
    # Smoothed trajectory (less noise)
    T_smooth = np.zeros((N, 4, 4))
    T_smooth[:, :3, 3] = np.column_stack([
        np.linspace(0, 10, N),
        np.linspace(0, 5, N),
        np.linspace(0, 3, N)
    ])
    T_smooth[:, :3, :3] = np.eye(3)
    T_smooth[:, 3, 3] = 1.0
    
    test_file = tmp_path / "test_compare_trans.h5"
    hlp.store_transformations(
        [T_raw, T_smooth], [100.0, 100.0], test_file,
        group_names=['raw', 'smooth']
    )
    
    # Compare translations
    fig, axes = hlp.compare_hdf5_trajectories(
        test_file,
        group_names=['raw', 'smooth'],
        component='translations'
    )
    
    import matplotlib.pyplot as plt
    assert fig is not None
    assert len(axes) == 3  # type: ignore # X, Y, Z subplots
    plt.close(fig)


def test_compare_hdf5_trajectories_rotations_euler(tmp_path):
    """
    Test compare_hdf5_trajectories with rotations_euler:
    - Creates trajectories with different rotations
    - Compares them using 'rotations_euler' component
    """
    from scipy.spatial.transform import Rotation as R
    
    N = 60
    
    # Trajectory 1: rotating around Z axis
    T1 = np.zeros((N, 4, 4))
    for i in range(N):
        angle = i * 0.1
        T1[i, :3, :3] = R.from_euler('z', angle).as_matrix()
        T1[i, 3, 3] = 1.0
    
    # Trajectory 2: rotating around X axis
    T2 = np.zeros((N, 4, 4))
    for i in range(N):
        angle = i * 0.05
        T2[i, :3, :3] = R.from_euler('x', angle).as_matrix()
        T2[i, 3, 3] = 1.0
    
    test_file = tmp_path / "test_compare_rot.h5"
    hlp.store_transformations(
        [T1, T2], [100.0, 100.0], test_file,
        group_names=['rotation_z', 'rotation_x']
    )
    
    # Compare rotations
    fig, axes = hlp.compare_hdf5_trajectories(
        test_file,
        component='rotations_euler',
        save_path=tmp_path / "rotation_comparison.png"
    )
    
    import matplotlib.pyplot as plt
    assert fig is not None
    assert len(axes) == 3  # type: ignore # Roll, Pitch, Yaw subplots
    assert (tmp_path / "rotation_comparison.png").exists()
    plt.close(fig)


def test_compare_hdf5_trajectories_rotations_rotvec(tmp_path):
    """
    Test compare_hdf5_trajectories with rotations_rotvec:
    - Verifies rotation vector component comparison works
    """
    N = 50
    T_t = np.tile(np.eye(4), (N, 1, 1))
    
    test_file = tmp_path / "test_compare_rotvec.h5"
    hlp.store_transformations(
        [T_t], [100.0], test_file,
        group_names=['identity']
    )
    
    # Compare rotation vectors
    fig, axes = hlp.compare_hdf5_trajectories(
        test_file,
        component='rotations_rotvec'
    )
    
    import matplotlib.pyplot as plt
    assert fig is not None
    assert len(axes) == 3  # type: ignore
    plt.close(fig)
