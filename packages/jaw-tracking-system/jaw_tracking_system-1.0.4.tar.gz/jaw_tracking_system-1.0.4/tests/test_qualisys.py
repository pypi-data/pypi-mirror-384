"""
Unit tests for jts.qualisys module.

The test suite covers:
- Initialization and validation of the RigidBody class.
- Computation of coordinate systems from points.
- Transformation matrix generation from RigidBody data.
- Ensuring correct shapes and values in transformation sequences.
- Error handling for mismatched lengths and invalid inputs.
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

import pytest
import numpy as np

from jts import qualisys as qtm


def test_rigidbody_init_and_validation():
    """
    Test initialization and validation of the RigidBody class:
    - Checks correct assignment of name, positions, and rotations.
    - Ensures shape validation for positions and rotations.
    - Verifies that mismatched lengths raise a ValueError.
    """
    pos = np.random.rand(10, 3)
    rot = np.tile(np.eye(3), (10, 1, 1))
    rb = qtm.RigidBody(name="TestBody", positions=pos, rotations=rot)
    assert rb.name == "TestBody"
    assert rb.positions.shape == (10, 3)  # type: ignore
    assert rb.rotations.shape == (10, 3, 3)  # type: ignore

    # Mismatched lengths should raise ValueError
    with pytest.raises(ValueError):
        qtm.RigidBody(name="Bad", positions=np.zeros((5, 3)), rotations=np.zeros((6, 3, 3)))


def test_compute_coordinate_system():
    """
    Test the compute_coordinate_system static method:
    - Checks that a valid set of 3 points returns a 4x4 transformation matrix.
    - Ensures the last row is [0, 0, 0, 1] (homogeneous coordinates).
    - Verifies that providing fewer than 3 points raises a ValueError.
    """
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    T = qtm.QualysisData.compute_coordinate_system(points)
    assert T.shape == (4, 4)
    np.testing.assert_allclose(T[3], [0, 0, 0, 1])

    # Should raise ValueError with fewer than 3 points
    with pytest.raises(ValueError):
        qtm.QualysisData.compute_coordinate_system(np.array([[0, 0, 0], [1, 0, 0]]))


def test_T_from_rigid_body():
    """
    Test the T_from_rigid_body function:
    - Checks that the returned transformation sequence has the correct shape.
    - Verifies that translation and rotation components match the input RigidBody.
    """
    N = 5
    pos = np.random.rand(N, 3)
    rot = np.tile(np.eye(3), (N, 1, 1))
    rb = qtm.RigidBody(name="Test", positions=pos, rotations=rot)
    T_seq = qtm.T_from_rigid_body(rb)
    assert T_seq.shape == (N, 4, 4)
    np.testing.assert_allclose(T_seq[:, :3, 3], pos)
    np.testing.assert_allclose(T_seq[:, :3, :3], rot)
