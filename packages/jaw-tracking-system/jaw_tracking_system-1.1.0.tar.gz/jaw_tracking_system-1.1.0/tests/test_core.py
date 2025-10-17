"""
Unit tests for jts.core module.

This test suite covers:
- Data class validation for FrameInterval and CalibrationPoint
- Configuration file loading and validation (including error handling)
- Initialization and method calls for the main JawMotionAnalysis pipeline (using mocks)

All tests use synthetic or minimal data and avoid file I/O for motion capture data.
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
import pytest
import tempfile
import json

from jts import core
from pathlib import Path


def test_frameinterval_and_calibrationpoint():
    """
    Test the FrameInterval and CalibrationPoint data classes:
    - Validates tuple conversion and string representation of FrameInterval.
    - Checks correct shape and assignment for CalibrationPoint.
    - Ensures ValueError is raised for invalid CalibrationPoint input.
    """
    fi = core.FrameInterval(1, 10, name="test")
    assert fi.to_tuple() == (1, 10)
    assert str(fi) == "test: [1, 10]"
    cp = core.CalibrationPoint(position=np.array([1, 2, 3]), name="A", frame_interval=fi)
    assert cp.position.shape == (3,)

    # Should raise ValueError for position with wrong shape
    with pytest.raises(ValueError):
        core.CalibrationPoint(position=np.zeros(2), name="bad")


def test_configmanager_load_and_validate():
    """
    Test the ConfigManager's config loading and validation:
    - Loads a valid config and checks required fields.
    - Tests error handling for missing required fields ('output', 'analysis', 'data_source').
    - Ensures FileNotFoundError is raised for missing config file.
    """
    # Valid config
    config = {
        "data_source": {"type": "qualisys", "filename": "dummy.mat"},
        "analysis": {"calibration": {}, "relative_motion": {"reference_body": "A", "moving_body": "B"},
                     "experiment": {"frame_interval": [0, 1]}, "smoothing": {"enabled": False}},
        "output": {"directory": "."}
    }

    # Write valid config to a temp file and load it
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
        json.dump(config, f)
        f.flush()
        loaded = core.ConfigManager.load_config(f.name)
        assert loaded["data_source"]["type"] == "qualisys"
        assert "analysis" in loaded
        assert "output" in loaded

    # Test missing required fields
    bad_config = {"data_source": {}, "analysis": {}}
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
        json.dump(bad_config, f)
        f.flush()
        with pytest.raises(ValueError):
            core.ConfigManager.load_config(f.name)

    bad_config2 = {"data_source": {}, "output": {}}
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
        json.dump(bad_config2, f)
        f.flush()
        with pytest.raises(ValueError):
            core.ConfigManager.load_config(f.name)

    bad_config3 = {"analysis": {}, "output": {}}
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
        json.dump(bad_config3, f)
        f.flush()
        with pytest.raises(ValueError):
            core.ConfigManager.load_config(f.name)

    # File not found
    with pytest.raises(FileNotFoundError):
        core.ConfigManager.load_config("nonexistent_config_file.json")


def test_jawmotionanalysis_init_and_methods(monkeypatch):
    """
    Test initialization and main methods of JawMotionAnalysis pipeline:
    - Uses a minimal config and a dummy motion data handler to avoid file I/O.
    - Mocks all required data and attributes for the pipeline.
    - Ensures all main pipeline methods execute without error.
    """
    # Minimal config for pipeline
    config = {
        "data_source": {"type": "qualisys", "filename": "dummy.mat"},
        "analysis": {
            "calibration": {},
            "relative_motion": {"reference_body": "A", "moving_body": "B"},
            "experiment": {"frame_interval": [0, 1]},
            "smoothing": {"enabled": False},
            "coordinate_transform": {"enabled": False, "calibration_type": "test",
                                     "model_points": [[0, 0, 0], [1, 0, 0], [0, 1, 0]]}
        },
        "output": {"directory": "."}
    }

    # Dummy motion data handler to avoid file I/O and external dependencies
    class DummyMotionData:
        rigid_bodies = {"A": object(), "B": object()}
        frame_rate = 100
        total_frames = 2

        def load_data(self, filename):
            pass  # No-op for test

        def get_rigid_body_transform(self, body_name, frame_interval=None):
            # Return identity transforms for all frames
            return np.tile(np.eye(4), (2, 1, 1))

        def compute_relative_transform(self, body1, body2, frame_interval=None):
            # Return identity transforms for all frames
            return np.tile(np.eye(4), (2, 1, 1))

    # Patch JawMotionAnalysis to use DummyMotionData
    monkeypatch.setattr(core.JawMotionAnalysis, "_create_motion_data_handler", lambda self: DummyMotionData())
    analysis = core.JawMotionAnalysis(config)
    analysis.motion_data = DummyMotionData()  # type: ignore

    # Mock calibration points, transforms, and trajectories
    analysis.calibration_points = {"test": np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])}
    analysis.calibration_transforms = {"T_B_landmark": np.eye(4)}
    analysis.trajectories["T_max_marker_mand_marker_t"] = np.tile(np.eye(4), (2, 1, 1))
    analysis.trajectories["T_max_marker_mand_landmark_t"] = np.tile(np.eye(4), (2, 1, 1))
    analysis.trajectories["T_model_origin_mand_landmark_t"] = np.tile(np.eye(4), (2, 1, 1))

    # Run all main pipeline methods (should not raise exceptions)
    analysis.perform_calibration()
    analysis.compute_relative_motion()
    analysis.transform_to_ref_markers_coordinates()
    analysis.register_to_model_coordinates()
    analysis.smooth_trajectory()


def test_config_unit_and_scale_factor(monkeypatch):
    """
    Test that the config's 'unit' and 'scale_factor' are passed to store_transformations.
    """
    config = {
        "data_source": {"type": "qualisys", "filename": "dummy.mat"},
        "analysis": {
            "calibration": {},
            "relative_motion": {"reference_body": "A", "moving_body": "B"},
            "experiment": {"frame_interval": [0, 1]},
            "smoothing": {"enabled": False},
            "coordinate_transform": {"enabled": False, "calibration_type": "test",
                                     "model_points": [[0, 0, 0], [1, 0, 0], [0, 1, 0]]}
        },
        "output": {"directory": ".", "unit": "m", "scale_factor": 0.001, "hdf5_filename": "test.h5"}
    }

    class DummyMotionData:
        rigid_bodies = {"A": object(), "B": object()}
        frame_rate = 100
        total_frames = 2
        def load_data(self, filename):
            pass
        def get_rigid_body_transform(self, body_name, frame_interval=None):
            return np.tile(np.eye(4), (2, 1, 1))
        def compute_relative_transform(self, body1, body2, frame_interval=None):
            return np.tile(np.eye(4), (2, 1, 1))

    monkeypatch.setattr(core.JawMotionAnalysis, "_create_motion_data_handler", lambda self: DummyMotionData())
    analysis = core.JawMotionAnalysis(config)
    analysis.motion_data = DummyMotionData()  # type: ignore
    analysis.calibration_points = {"test": np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])}
    analysis.calibration_transforms = {"T_B_landmark": np.eye(4)}
    analysis.trajectories["T_max_marker_mand_marker_t"] = np.tile(np.eye(4), (2, 1, 1))
    analysis.trajectories["T_max_marker_mand_landmark_t"] = np.tile(np.eye(4), (2, 1, 1))
    analysis.trajectories["T_model_origin_mand_landmark_t"] = np.tile(np.eye(4), (2, 1, 1))
    analysis.active_trajectory = np.tile(np.eye(4), (2, 1, 1))
    analysis.active_trajectory_label = "raw"

    called_args = {}
    def fake_store_transformations(*args, **kwargs):
        called_args['scale_factor'] = kwargs.get('scale_factor')
        called_args['unit'] = kwargs.get('unit')
        return None

    monkeypatch.setattr("jts.helper.store_transformations", fake_store_transformations)
    analysis._save_hdf5_results(Path("."))

    assert called_args['scale_factor'] == 0.001
    assert called_args['unit'] == "m"
