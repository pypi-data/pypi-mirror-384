#!/usr/bin/env python3

"""
core.py: Modular and flexible jaw motion analysis framework.

This module provides an abstract framework for analyzing motion capture data,
with specific implementations for jaw motion analysis. The design allows for
easy extension to other motion capture systems beyond Qualisys.

Mathematical Framework:
The analysis performs a series of coordinate transformations to map motion capture
marker data to anatomical landmark coordinate systems and finally to a 3D model's
coordinate system.

Key Transformations:
    1. T_marker_landmark: Static transform from marker CS to anatomical landmark CS (via calibration)
    2. T_max_marker_mand_marker_t: Time-varying transform of mandible marker relative to maxilla marker
    3. T_max_marker_mand_landmark_t: Time-varying transform of mandibular landmark relative to maxilla marker
    4. T_model_origin_max_marker: Static transform from maxilla marker CS to model origin CS (via registration)
    5. T_model_origin_mand_landmark_t: Final trajectory of mandibular landmark in model coordinates

-------------------------------------------------------------------------------
Real-Time Streaming and Online Calibration:
-------------------------------------------------------------------------------
This framework supports both offline and real-time (streaming) motion capture data processing.

- Real-Time Streaming:
    - Integration with Qualisys Track Manager (QTM) and other systems is provided via
      the streaming.py and qualisys_streaming.py modules.
    - These modules enable live data acquisition, real-time trajectory computation,
      and immediate feedback.
    - The core analysis pipeline can be executed in streaming mode, automatically switching
      to online data handlers and updating results as new frames arrive.

- Online Calibration:
    - The calibration_controllers.py module provides tools for interactive, online calibration
      of anatomical landmarks and marker coordinate systems during live sessions.
    - This allows for dynamic recalibration without interrupting the data stream, supporting
      workflows where marker placement or anatomical references may change.
    - Online calibration results are seamlessly integrated into the transformation pipeline,
      ensuring accurate, up-to-date coordinate mappings throughout real-time analysis.

See streaming.py, qualisys_streaming.py, and calibration_controllers.py for implementation details
and extension points for custom streaming or calibration workflows.
"""

__author__ = "Paul-Otto Müller"
__copyright__ = "Copyright 2025, Paul-Otto Müller"
__credits__ = ["JawTrackingSystem (JTS) (c) Paul-Otto Müller"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "1.0.4"
__maintainer__ = "Paul-Otto Müller"
__status__ = "Development"
__date__ = '16.10.2025'
__url__ = "https://github.com/paulotto/jaw_tracking_system"

import os
import json
import logging

from enum import Enum
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
from scipy.spatial.transform import Slerp
from typing import Dict, List, Tuple, Optional, Any, Union, Callable

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R

from . import helper as hlp
from . import qualisys as qtm

# Use the colored logger from helper module
logger = hlp.setup_logger(__name__)


@dataclass
class FrameInterval:
    """
    Represents a frame interval with start and end frames.

    Attributes:
        start: Starting frame number
        end: Ending frame number
        name: Optional name for the interval
    """
    start: int
    end: int
    name: Optional[str] = None

    def to_tuple(self) -> Tuple[int, int]:
        """Convert to tuple format."""
        return self.start, self.end

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name or 'Interval'}: [{self.start}, {self.end}]"


@dataclass
class CalibrationPoint:
    """
    Represents a calibration point in 3D space.

    Attributes:
        position: 3D position vector
        name: Name identifier for the point
        frame_interval: Frame interval where this point was captured
    """
    position: np.ndarray
    name: str
    frame_interval: Optional[FrameInterval] = None

    def __post_init__(self):
        """Validate the position array."""
        if self.position.shape != (3,):
            raise ValueError(f"Position must be a 3D vector, got shape {self.position.shape}")


class InterpolationMethod(Enum):
    """Interpolation methods for connecting frame intervals."""
    LINEAR = "linear"
    CUBIC = "cubic"
    SLERP = "slerp"  # For rotations
    HERMITE = "hermite"
    NONE = "none"  # Just concatenate without interpolation


class MultiIntervalProcessor:
    """
    Handles processing and connection of multiple frame intervals.
    """

    def __init__(self, interpolation_method: InterpolationMethod = InterpolationMethod.CUBIC,
                 transition_frames: int = 10):
        """
        Initialize the multi-interval processor.

        Args:
            interpolation_method: Method to use for connecting intervals
            transition_frames: Number of frames to use for smooth transitions
        """
        self.interpolation_method = interpolation_method
        self.transition_frames = transition_frames

        logger.info(f"Initialized MultiIntervalProcessor with {interpolation_method.value} interpolation")

    def process_intervals(self,
                          data_source: Callable[[FrameInterval], np.ndarray],
                          intervals: List[FrameInterval],
                          connect: bool = True) -> np.ndarray:
        """
        Process multiple intervals and optionally connect them.

        Args:
            data_source: Function that returns data for a given FrameInterval
            intervals: List of frame intervals to process
            connect: Whether to connect intervals with interpolation

        Returns:
            Combined transformation matrices
        """
        if not intervals:
            raise ValueError("No intervals provided")

        # Process each interval
        interval_data = []
        for interval in intervals:
            data = data_source(interval)
            if data is None or len(data) == 0:
                logger.warning(f"No data for interval {interval}")
                continue
            interval_data.append((interval, data))

        if not interval_data:
            raise ValueError("No valid data found in any interval")

        if len(interval_data) == 1:
            return interval_data[0][1]

        if not connect:
            # Just concatenate
            return np.vstack([data for _, data in interval_data])

        # Connect intervals with interpolation
        return self._connect_intervals(interval_data)

    def _connect_intervals(self, interval_data: List[Tuple[FrameInterval, np.ndarray]]) -> np.ndarray:
        """
        Connect multiple intervals with smooth transitions.

        Args:
            interval_data: List of (interval, transformation_data) tuples

        Returns:
            Connected transformation matrices
        """
        connected_transforms = []

        for i in range(len(interval_data)):
            interval, transforms = interval_data[i]

            if i == 0:
                # First interval - add as is
                connected_transforms.extend(transforms)
            else:
                # Need to interpolate between previous and current
                prev_interval, prev_transforms = interval_data[i - 1]

                # Create transition
                transition = self._create_transition(
                    prev_transforms[-1],  # Last transform of previous interval
                    transforms[0],  # First transform of current interval
                    prev_interval.end,
                    interval.start
                )

                # Add transition and current interval (excluding first frame to avoid duplication)
                connected_transforms.extend(transition)
                connected_transforms.extend(transforms[1:])

        return np.array(connected_transforms)

    def _create_transition(self,
                           T_start: np.ndarray,
                           T_end: np.ndarray,
                           frame_start: int,
                           frame_end: int,
                           T_before: Optional[np.ndarray] = None,
                           T_after: Optional[np.ndarray] = None) -> List[np.ndarray]:
        """
        Create smooth transition between two transformations.

        Args:
            T_start: Starting transformation (4x4)
            T_end: Ending transformation (4x4)
            frame_start: Starting frame number
            frame_end: Ending frame number
            T_before: Transformation before T_start (for velocity estimation)
            T_after: Transformation after T_end (for velocity estimation)

        Returns:
            List of interpolated transformations
        """
        num_frames = min(self.transition_frames, frame_end - frame_start - 1)
        if num_frames <= 0:
            return []

        # Decompose transformations
        pos_start = T_start[:3, 3]
        pos_end = T_end[:3, 3]

        # For velocity estimation
        pos_before = T_before[:3, 3] if T_before is not None else None
        pos_after = T_after[:3, 3] if T_after is not None else None

        rot_start = T_start[:3, :3]
        rot_end = T_end[:3, :3]

        # Interpolate positions
        t = np.linspace(0, 1, num_frames)

        if self.interpolation_method == InterpolationMethod.LINEAR:
            positions = self._linear_interpolate_positions(pos_start, pos_end, t)
        elif self.interpolation_method == InterpolationMethod.CUBIC:
            positions = self._cubic_interpolate_positions_with_velocity(pos_start, pos_end, t, pos_before, pos_after)
        else:
            positions = self._linear_interpolate_positions(pos_start, pos_end, t)

        # Interpolate rotations
        rotations = self._interpolate_rotations(rot_start, rot_end, t)

        # Reconstruct transformations
        transitions = []
        for i in range(num_frames):
            T = np.eye(4)
            T[:3, :3] = rotations[i]
            T[:3, 3] = positions[i]
            transitions.append(T)

        return transitions

    @staticmethod
    def _linear_interpolate_positions(start: np.ndarray, end: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Linear interpolation of positions."""
        return np.array([start + (end - start) * ti for ti in t])

    @staticmethod
    def _cubic_interpolate_positions_with_velocity(start: np.ndarray,
                                                   end: np.ndarray,
                                                   t: np.ndarray,
                                                   pos_before: Optional[np.ndarray] = None,
                                                   pos_after: Optional[np.ndarray] = None) -> np.ndarray:
        """Cubic Hermite interpolation with smart velocity estimation."""
        # Estimate velocities
        if pos_before is not None:
            # Use previous position for velocity estimate
            v_start = (end - pos_before) / 2.0
        else:
            # No previous data - use damped forward difference
            v_start = (end - start) * 0.3

        if pos_after is not None:
            # Use next position for velocity estimate
            v_end = (pos_after - start) / 2.0
        else:
            # No next data - use damped backward difference
            v_end = (end - start) * 0.3

        # Apply Hermite interpolation
        positions = []
        for ti in t:
            h00 = 2 * ti ** 3 - 3 * ti ** 2 + 1
            h10 = ti ** 3 - 2 * ti ** 2 + ti
            h01 = -2 * ti ** 3 + 3 * ti ** 2
            h11 = ti ** 3 - ti ** 2

            pos = h00 * start + h10 * v_start + h01 * end + h11 * v_end
            positions.append(pos)

        return np.array(positions)

    @staticmethod
    def _interpolate_rotations(R_start: np.ndarray, R_end: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Interpolate rotations using SLERP."""
        # Convert to scipy Rotation objects
        # r_start = R.from_matrix(R_start)
        # r_end = R.from_matrix(R_end)

        # Create slerp interpolator
        key_times = [0, 1]
        key_rots = R.from_matrix(np.array([R_start, R_end]))
        slerp = Slerp(key_times, key_rots)

        # Interpolate
        interpolated = slerp(t)
        return interpolated.as_matrix()


class MotionCaptureData(ABC):
    """
    Abstract base class for motion capture data handling.

    This class defines the interface for working with motion capture data
    from different systems (Qualisys, OptiTrack, Vicon, etc.).
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize motion capture data handler.

        Args:
            config: Configuration dictionary containing system-specific parameters
        """
        self.config = config
        self.data = None
        self.rigid_bodies = {}
        self.frame_rate = None
        self.total_frames = None

    @abstractmethod
    def load_data(self, filename: str) -> None:
        """
        Load motion capture data from file.

        Args:
            filename: Path to the data file
        """
        pass

    @abstractmethod
    def get_rigid_body_transform(self, body_name: str, frame_interval: Optional[FrameInterval] = None) -> np.ndarray:
        """
        Get transformation matrices for a rigid body over time.

        Args:
            body_name: Name of the rigid body
            frame_interval: Optional frame interval to extract

        Returns:
            Array of shape (N, 4, 4) containing transformation matrices
        """
        pass

    @abstractmethod
    def compute_relative_transform(self, body1: str, body2: str,
                                   frame_interval: Optional[FrameInterval] = None) -> np.ndarray:
        """
        Compute relative transformation between two rigid bodies.

        Args:
            body1: Name of the first rigid body (reference)
            body2: Name of the second rigid body (moving)
            frame_interval: Optional frame interval

        Returns:
            Array of shape (N, 4, 4) containing relative transformations T_body1_body2
        """
        pass


class QualysisMotionCaptureData(MotionCaptureData):
    """
    Concrete implementation for Qualisys motion capture data.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Qualisys data handler.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        self.qualisys_data = None
        self.plot_utils = None

    def load_data(self, filename: str) -> None:
        """
        Load Qualisys .mat file.

        Args:
            filename: Path to the .mat file
        """
        logger.info(f"Loading Qualisys data from {filename}")

        self.qualisys_data = qtm.QualysisData(filename)  # Use qtm module
        self.plot_utils = qtm.QualysisDataPlotUtils(self.qualisys_data)  # Use qtm module
        self.rigid_bodies = self.qualisys_data.rigid_bodies
        self.frame_rate = self.qualisys_data.frame_rate
        self.total_frames = self.qualisys_data.frames

        logger.info(
            f"✓ Loaded {len(self.rigid_bodies)} rigid bodies, {self.total_frames} frames at {self.frame_rate} Hz")

    def get_rigid_body_transform(self, body_name: str, frame_interval: Optional[FrameInterval] = None) -> np.ndarray:
        """
        Get transformation matrices for a rigid body.

        Args:
            body_name: Name of the rigid body
            frame_interval: Optional frame interval

        Returns:
            Transformation matrices of shape (N, 4, 4)
        """
        if body_name not in self.rigid_bodies:
            raise ValueError(f"Rigid body '{body_name}' not found")

        frame_tuple = frame_interval.to_tuple() if frame_interval else None

        return qtm.T_from_rigid_body(self.rigid_bodies[body_name], frame_tuple)

    def compute_relative_transform(self, body1: str, body2: str,
                                   frame_interval: Optional[FrameInterval] = None) -> np.ndarray:
        """
        Compute relative transformation between two rigid bodies.

        Args:
            body1: Name of the first rigid body (reference)
            body2: Name of the second rigid body (moving)
            frame_interval: Optional frame interval

        Returns:
            Relative transformations of shape (N, 4, 4) representing T_body1_body2
        """
        rb_list = [self.rigid_bodies[body1], self.rigid_bodies[body2]]
        frame_intervals = [frame_interval.to_tuple()] if frame_interval else [(0, self.total_frames)]

        result = qtm.QualysisData.compute_relative_transformations(rb_list, frame_intervals)  # Use qtm module
        key = list(result.keys())[0]

        return result[key][f'{body1}-{body2}']


class ConfigManager:
    """
    Manages configuration loading and validation.
    """

    @staticmethod
    def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        logger.info(f"Loading configuration from {config_path}")
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Validate required fields
        ConfigManager._validate_config(config)
        logger.info("✓ Configuration loaded and validated successfully")
        return config

    @staticmethod
    def _validate_config(config: Dict[str, Any]) -> None:
        """
        Validate configuration structure.

        Args:
            config: Configuration dictionary to validate
        """
        required_fields = ['data_source', 'analysis', 'output']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Required configuration field '{field}' is missing")


class JawMotionAnalysis:
    """
    Main class for jaw motion analysis.

    [Previous docstring content remains the same]
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize jaw motion analysis.

        Args:
            config: Configuration dictionary
        """
        self._figures_to_save = []  # (fig, filename, plot_type)

        self.config = config
        self.motion_data = self._create_motion_data_handler()

        # Calibration data storage
        self.calibration_points = {}  # Points in marker CS used to define landmark CS
        self.calibration_transforms = {}  # T_marker_landmark transformations

        # Trajectory storage
        self.trajectories: Dict[str, Optional[np.ndarray]] = {
            'T_max_marker_mand_marker_t': None,  # Relative marker motion
            'T_max_marker_mand_landmark_t': None,  # Landmark motion in max marker CS
            'T_model_origin_mand_landmark_t': None,  # Landmark motion in model CS (raw)
            'T_model_origin_mand_landmark_t_smooth': None  # Smoothed version
        }
        self.sub_experiment_trajectories = None

        # Registration transform
        self.T_model_origin_max_marker = None

        # Active trajectory for export
        self.active_trajectory = None
        self.active_trajectory_label = ""

        # Check if streaming mode
        self.is_streaming = config['data_source'].get('mode', 'offline') == 'streaming'

        if self.is_streaming:
            # Import streaming module
            from . import qualisys_streaming as qstm

            # Create streaming handler
            self.motion_data = qstm.create_qualisys_streaming_handler(config)

            # For streaming, we'll handle calibration differently
            self.calibration_controller = None  # Will be set up later
        else:
            # Use existing offline handler
            self.motion_data = self._create_motion_data_handler()

    def _create_motion_data_handler(self) -> MotionCaptureData:
        """
        Create appropriate motion capture data handler based on configuration.

        Returns:
            Motion capture data handler instance
        """
        data_type = self.config['data_source']['type']

        if data_type == 'qualisys':
            return QualysisMotionCaptureData(self.config['data_source'])
        else:
            raise ValueError(f"Unsupported data source type: {data_type}")

    @staticmethod
    def _log_step(message: str, level: str = "INFO") -> None:
        """
        Log a step in the analysis with consistent formatting.

        Args:
            message: Message to log
            level: Logging level
        """
        logger.log(getattr(logging, level), f"[STEP] {message}")

    @staticmethod
    def _log_transform(name: str, transform: np.ndarray) -> None:
        """
        Log transformation matrix with rotation in Euler angles.

        Args:
            name: Name of the transformation
            transform: 4x4 transformation matrix
        """
        euler = R.from_matrix(transform[:3, :3]).as_euler('xyz', degrees=True)
        translation = transform[:3, 3]

        logger.info(f"\n{name}:")
        logger.info(f"  Translation: [{translation[0]:.3f}, {translation[1]:.3f}, {translation[2]:.3f}] mm")
        logger.info(f"  Rotation (XYZ Euler): [{euler[0]:.1f}°, {euler[1]:.1f}°, {euler[2]:.1f}°]")

    def load_data(self) -> None:
        """Load motion capture data from file."""
        filename = self.config['data_source']['filename']
        self._log_step(f"Loading motion capture data from {filename}")
        
        if not hasattr(self.motion_data, 'load_data'):
            raise RuntimeError("Streaming data sources do not support load_data(). Data is loaded in real-time.")
        
        self.motion_data.load_data(filename)  # type: ignore

        # Visualize raw data if configured
        if self.config.get('visualization', {}).get('raw_data', False):
            self._log_step("Visualizing raw motion capture data")
            self._visualize_raw_data()

    def _visualize_raw_data(self) -> None:
        """Visualize raw motion capture data."""
        if hasattr(self.motion_data, 'plot_utils'):
            viz_config = self.config.get('visualization', {})
            experiment_interval = self.config['analysis']['experiment']['frame_interval']

            self.motion_data.plot_utils.visualize_qualysis_data(  # type: ignore
                three_d=viz_config.get('raw_data_3d', False),
                frame_interval=experiment_interval
            )

    def analyze_sub_experiments(self) -> Dict[str, np.ndarray]:
        """
        Analyze individual sub-experiments defined in configuration.

        Returns:
            Dictionary mapping sub-experiment names to their trajectories
        """
        self._log_step("Analyzing sub-experiments")

        sub_exp_config = self.config['analysis']['experiment'].get('sub_experiments', {})
        if not sub_exp_config:
            logger.info("No sub-experiments defined in configuration")
            return {}

        sub_trajectories = {}

        for name, interval_data in sub_exp_config.items():
            logger.info(f"Processing sub-experiment: {name}")

            # Handle both single interval and list of intervals
            if isinstance(interval_data[0], list):
                # Multiple intervals for this sub-experiment
                intervals = [FrameInterval(start=iv[0], end=iv[1], name=f"{name}_{i}")
                             for i, iv in enumerate(interval_data)]
            else:
                # Single interval
                intervals = [FrameInterval(start=interval_data[0], end=interval_data[1], name=name)]

            # Process this sub-experiment
            try:
                trajectory = self._process_sub_experiment(name, intervals)
                sub_trajectories[name] = trajectory
                logger.info(f"✓ Processed {name}: {trajectory.shape[0]} frames")
            except Exception as e:
                logger.error(f"Failed to process sub-experiment {name}: {e}")

        return sub_trajectories

    def _process_sub_experiment(self, name: str, intervals: List[FrameInterval]) -> np.ndarray:
        """
        Process a single sub-experiment with potentially multiple intervals.

        Args:
            name: Name of the sub-experiment
            intervals: List of frame intervals

        Returns:
            Processed trajectory for this sub-experiment
        """
        # Get interpolation settings from config
        interp_config = self.config['analysis']['experiment'].get('interpolation', {})
        method = InterpolationMethod(interp_config.get('method', 'cubic'))
        transition_frames = interp_config.get('transition_frames', 10)
        connect = interp_config.get('connect_intervals', True)

        processor = MultiIntervalProcessor(method, transition_frames)

        # Data source function for the processor
        def get_interval_motion(interval: FrameInterval) -> np.ndarray:
            motion_config = self.config['analysis']['relative_motion']
            reference_body = motion_config['reference_body']
            moving_body = motion_config['moving_body']

            # Get relative motion for this interval
            T_relative = self.motion_data.compute_relative_transform(
                reference_body, moving_body, interval  # type: ignore
            )

            if T_relative is None:
                raise RuntimeError(f"Failed to compute relative transform between {reference_body} and {moving_body}")

            # Apply calibration transform if available
            if self.calibration_transforms:
                mand_marker = moving_body
                T_mand_marker_landmark = self.calibration_transforms.get(f"T_{mand_marker}_landmark")
                if T_mand_marker_landmark is not None:
                    T_relative = np.array([T @ T_mand_marker_landmark for T in T_relative])

            return T_relative

        # Process intervals
        return processor.process_intervals(get_interval_motion, intervals, connect)

    def perform_calibration(self) -> Dict[str, np.ndarray]:
        """
        Performs calibration to determine transformations from anatomical landmarks to tracking markers.

        Mathematical Foundation:
        For each jaw (mandible/maxilla), we:
            1. Collect N calibration points where a calibration tool points to anatomical landmarks
            2. Express these points in the marker's coordinate system
            3. Fit a coordinate system to these points using PCA
            4. The result is T_marker_landmark: transformation from landmark CS to marker CS

        Equation: P_marker = T_marker_landmark @ P_landmark

        Returns:
            Dictionary of calibration transformations
        """
        self._log_step("Performing calibration to establish landmark-to-marker transformations")

        calib_config = self.config['analysis']['calibration']

        for calib_type, calib_data in calib_config.items():
            self._log_step(f"Calibrating {calib_type}")

            # Extract calibration points
            points = []
            bodies = calib_data['rigid_bodies']
            
            if not hasattr(self.motion_data, 'rigid_bodies'):
                raise RuntimeError("Streaming data sources do not support rigid_bodies attribute.")
            
            rb_list = [self.motion_data.rigid_bodies[body] for body in bodies]  # type: ignore

            for point_idx, point_config in enumerate(calib_data['points']):
                interval = FrameInterval(
                    start=point_config['frame_interval'][0],
                    end=point_config['frame_interval'][1],
                    name=point_config['name']
                )

                # Compute average transformation during calibration
                avg_transforms = qtm.QualysisData.compute_average_transformations(
                    rb_list, [interval.to_tuple()]
                )

                # Extract calibration point position in marker CS
                transform_key = f"{bodies[0]}-{bodies[1]}"
                interval_key = f"{interval.start}-{interval.end}"
                T_marker_calib_tool = avg_transforms[interval_key][transform_key]
                position = T_marker_calib_tool[:3, 3]  # Origin of calib tool in marker CS

                points.append(position)
                logger.info(f"  ✓ Calibration point {point_idx + 1}: {position} (in {bodies[0]} CS)")

            # Store calibration points
            self.calibration_points[calib_type] = np.array(points)

            # Compute landmark coordinate system
            # T_marker_landmark: Transform from landmark CS to marker CS
            T_marker_landmark = qtm.QualysisData.compute_coordinate_system(
                self.calibration_points[calib_type],
                origin_index=self.config['analysis'].get('coordinate_origin_index', 0)
            )

            self.calibration_transforms[f"T_{bodies[0]}_landmark"] = T_marker_landmark
            self._log_transform(f"T_{bodies[0]}_landmark", T_marker_landmark)

            # Visualize calibration if configured
            if self.config.get('visualization', {}).get('calibration_transforms', False):
                self._visualize_calibration_transforms()

        logger.info("✓ Calibration completed successfully")
        return self.calibration_transforms

    def _visualize_calibration_transforms(self) -> None:
        """Visualize calibration transformations."""
        # Implementation depends on specific visualization requirements
        logger.info("Visualization of calibration transforms requested but not implemented in base class")

    def compute_relative_motion(self) -> np.ndarray:
        """
        Compute relative motion between markers.

        Mathematical Foundation:
        Given two markers A and B with global poses T_world_A and T_world_B,
        the relative transformation is:
        T_A_B = inv(T_world_A) @ T_world_B

        For jaw motion, we compute:
        T_max_marker_mand_marker_t = inv(T_world_max_marker_t) @ T_world_mand_marker_t

        Returns:
            Time series of relative transformations
        """
        self._log_step("Computing relative marker motion")

        exp_config = self.config['analysis']['experiment']

        # Check if we should use sub-experiments
        use_sub_experiments = exp_config.get('use_sub_experiments', False)

        if use_sub_experiments and 'sub_experiments' in exp_config:
            # Process sub-experiments
            sub_trajectories = self.analyze_sub_experiments()

            # Determine which sub-experiments to combine for main trajectory
            combine_subs = exp_config.get('combine_sub_experiments', list(sub_trajectories.keys()))

            if isinstance(combine_subs, str) and combine_subs == 'all':
                combine_subs = list(sub_trajectories.keys())

            # Combine selected sub-experiments
            if combine_subs:
                combined_intervals = []
                for sub_name in combine_subs:
                    if sub_name in exp_config['sub_experiments']:
                        interval_data = exp_config['sub_experiments'][sub_name]
                        if isinstance(interval_data[0], list):
                            for iv in interval_data:
                                combined_intervals.append(FrameInterval(iv[0], iv[1], sub_name))
                        else:
                            combined_intervals.append(
                                FrameInterval(interval_data[0], interval_data[1], sub_name)
                            )

                # Process combined intervals
                processor = MultiIntervalProcessor(
                    InterpolationMethod(exp_config.get('interpolation', {}).get('method', 'cubic')),
                    exp_config.get('interpolation', {}).get('transition_frames', 10)
                )

                motion_config = self.config['analysis']['relative_motion']
                reference_body = motion_config['reference_body']
                moving_body = motion_config['moving_body']

                def get_motion(interval: FrameInterval) -> np.ndarray:
                    result = self.motion_data.compute_relative_transform(
                        reference_body, moving_body, interval  # type: ignore
                    )
                    if result is None:
                        raise RuntimeError(f"Failed to compute relative transform for interval {interval.name}")
                    return result

                T_relative_t = processor.process_intervals(
                    get_motion,
                    combined_intervals,
                    exp_config.get('interpolation', {}).get('connect_intervals', True)
                )

                # Store sub-experiment trajectories
                self.sub_experiment_trajectories = sub_trajectories
            else:
                # Fall back to single interval
                T_relative_t = self._compute_single_interval_motion()
        else:
            # Single interval
            T_relative_t = self._compute_single_interval_motion()

        self.trajectories['T_max_marker_mand_marker_t'] = T_relative_t
        logger.info(f"✓ Computed {T_relative_t.shape[0]} frames of relative motion")

        # Visualize if configured
        if self.config.get('visualization', {}).get('relative_marker_motion', False):
            self._visualize_trajectory(
                T_relative_t,
                title='Relative Motion with Connected Sub-Experiments',
                label='Connected Motion'
            )

        return T_relative_t

    def _compute_single_interval_motion(self) -> np.ndarray:
        """Single interval computation."""
        motion_config = self.config['analysis']['relative_motion']
        reference_body = motion_config['reference_body']
        moving_body = motion_config['moving_body']

        exp_config = self.config['analysis']['experiment']
        interval = FrameInterval(
            start=exp_config['frame_interval'][0],
            end=exp_config['frame_interval'][1],
            name="experiment"
        )

        # Handle both offline (FrameInterval) and streaming (window_size) APIs
        # Check if this is a streaming data source by checking class name
        if 'Streaming' in self.motion_data.__class__.__name__:
            # Streaming API - convert FrameInterval to window size
            window_size = interval.end - interval.start + 1
            T_relative_t = self.motion_data.compute_relative_transform(
                reference_body, moving_body, window_size  # type: ignore
            )
        else:
            # Offline API - use FrameInterval directly
            T_relative_t = self.motion_data.compute_relative_transform(
                reference_body, moving_body, interval  # type: ignore
            )

        if T_relative_t is None:
            raise RuntimeError(f"Failed to compute relative transform between {reference_body} and {moving_body}")

        return T_relative_t

    def transform_to_ref_markers_coordinates(self) -> np.ndarray:
        """
        Transform motion from anatomical landmark coordinates to marker coordinates.

        Mathematical Foundation:
        Given:
            - T_max_marker_mand_marker_t: Mandible marker trajectory in maxilla marker CS
            - T_mand_marker_mand_landmark: Static transform from landmark to mandible marker CS

        We compute:
        T_max_marker_mand_landmark_t = T_max_marker_mand_marker_t @ T_mand_marker_mand_landmark

        This gives us the mandibular landmark's trajectory relative to the maxilla marker.

        Returns:
            Landmark trajectory in reference marker coordinates
        """
        self._log_step("Transforming motion from anatomical landmark to reference marker coordinates")

        # Get the landmark to mandible marker transformation
        mand_marker = self.config['analysis']['relative_motion']['moving_body']
        T_mand_marker_landmark = self.calibration_transforms[f"T_{mand_marker}_landmark"]

        # Apply transformation to each frame
        # T_max_marker_mand_landmark_t = T_max_marker_mand_marker_t @ T_mand_marker_mand_landmark
        T_marker_motion = self.trajectories['T_max_marker_mand_marker_t']
        
        if T_marker_motion is None:
            raise RuntimeError("Marker motion trajectory not available. Run compute_relative_motion first.")
        
        T_landmark_motion = np.array([
            T_frame @ T_mand_marker_landmark for T_frame in T_marker_motion
        ])

        self.trajectories['T_max_marker_mand_landmark_t'] = T_landmark_motion

        logger.info(f"✓ Transformed {T_landmark_motion.shape[0]} frames to landmark coordinates")

        # Visualize if configured
        if self.config.get('visualization', {}).get('landmark_motion', False):
            max_marker = self.config['analysis']['relative_motion']['reference_body']
            self._visualize_trajectory(
                T_landmark_motion,
                title=f'Mandibular Landmark Motion in {max_marker} CS',
                label=f'T_{max_marker}_mand_landmark'
            )

        return T_landmark_motion

    def register_to_model_coordinates(self) -> Optional[np.ndarray]:
        """
        Register motion capture coordinate system to model coordinate system.

        Mathematical Foundation:
        Using corresponding points between motion capture and model:
            - P_mocap: Calibration points in motion capture CS (maxilla marker CS)
            - P_model: Corresponding points in model CS

        Kabsch algorithm finds optimal T such that:
        P_model ≈ T @ P_mocap

        Therefore: T_model_origin_max_marker minimizes ||P_model - T @ P_mocap||²

        Returns:
            Registration transformation matrix
        """
        self._log_step("Registering motion capture to model coordinate system")

        transform_config = self.config['analysis']['coordinate_transform']

        if not transform_config.get('enabled', True):
            logger.info("⚠ Coordinate transformation disabled in configuration")
            return None

        # Get calibration points in marker CS
        calib_type = transform_config['calibration_type']
        mocap_points = self.calibration_points[calib_type]

        # Get corresponding model points
        model_points = np.array(transform_config['model_points'])

        # Validate point correspondence
        if mocap_points.shape != model_points.shape:
            raise ValueError(
                f"Shape mismatch: mocap points {mocap_points.shape} vs model points {model_points.shape}"
            )

        # Compute registration using Kabsch algorithm
        # T_model_origin_max_marker: transforms from max_marker CS to model_origin CS
        self.T_model_origin_max_marker = hlp.kabsch_algorithm(mocap_points, model_points)

        self._log_transform("T_model_origin_max_marker", self.T_model_origin_max_marker)

        # Apply registration to landmark trajectory
        # T_model_origin_mand_landmark_t = T_model_origin_max_marker @ T_max_marker_mand_landmark_t
        T_landmark_in_marker = self.trajectories['T_max_marker_mand_landmark_t']
        
        if T_landmark_in_marker is None:
            raise RuntimeError("Landmark trajectory not available. Run transform_to_ref_markers_coordinates first.")
        
        T_landmark_in_model = np.array([
            self.T_model_origin_max_marker @ T_frame for T_frame in T_landmark_in_marker
        ])

        self.trajectories['T_model_origin_mand_landmark_t'] = T_landmark_in_model

        logger.info(f"✓ Registered {T_landmark_in_model.shape[0]} frames to model coordinates")
        return T_landmark_in_model

    def smooth_trajectory(self) -> Optional[np.ndarray]:
        """
        Apply smoothing to trajectory if configured.

        Sets the active trajectory for export based on smoothing configuration.

        Returns:
            Smoothed trajectory if smoothing is applied, None otherwise
        """
        self._log_step("Applying trajectory smoothing")

        smooth_config = self.config['analysis']['smoothing']
        raw_trajectory = self.trajectories['T_model_origin_mand_landmark_t']

        if raw_trajectory is None:
            logger.warning("⚠ No trajectory available for smoothing")
            return None

        if not smooth_config.get('enabled', True):
            self.active_trajectory = raw_trajectory
            self.active_trajectory_label = "raw"
            logger.info("ℹ Smoothing disabled, using raw trajectory")
            return None

        # Apply smoothing
        smooth_filter = hlp.TransformationFilter(
            window_length=smooth_config['window_length'],
            poly_order=smooth_config['poly_order']
        )

        smoothed = smooth_filter(raw_trajectory)
        self.trajectories['T_model_origin_mand_landmark_t_smooth'] = smoothed

        self.active_trajectory = smoothed
        self.active_trajectory_label = "smoothed"

        logger.info(
            f"✓ Applied Savitzky-Golay filter: window={smooth_config['window_length']}, "
            f"order={smooth_config['poly_order']}"
        )
        return smoothed

    def _visualize_trajectory(self, trajectory: np.ndarray, title: str, label: str) -> None:
        """
        Helper method to visualize a trajectory.

        Args:
            trajectory: Trajectory data to visualize
            title: Plot title
            label: Label for the trajectory
        """
        viz_config = self.config.get('visualization', {})
        plot_style = viz_config.get('plot_style', {})

        # Extract plot style parameters
        plot_params = {
            'plot_3d': True,
            'plot_rot': viz_config.get('plot_rot_3d', True),
            'sample_rate': viz_config.get('sample_rate', 10),
            'linewidth': viz_config.get('linewidth', 1.5),
            'labelpad_scale': plot_style.get('labelpad_scale', 1.0),
            'axes_label_fontsize': plot_style.get('axes_label_fontsize'),
            'axes_tick_fontsize': plot_style.get('axes_tick_fontsize'),
            'title_fontsize': plot_style.get('title_fontsize'),
            'legend_fontsize': plot_style.get('legend_fontsize'),
            'figure_size': plot_style.get('figure_size'),
            'view_3d': plot_style.get('view_3d'),
            'colors': plot_style.get('colors'),
            'line_styles': plot_style.get('line_styles'),
            'grid_enabled': plot_style.get('grid', {}).get('enabled', True),
            'grid_alpha': plot_style.get('grid', {}).get('alpha', 0.3)
        }

        hlp.plot_trajectories(
            [trajectory],
            title=title,
            labels=[label],
            **plot_params
        )
        plt.show()

        # Also plot 2D if configured
        if viz_config.get('plot_2d_components', True):
            plot_params['plot_3d'] = False
            hlp.plot_trajectories(
                [trajectory],
                title=f"{title} (2D Components)",
                labels=[label],
                **plot_params
            )
            plt.show()

    def visualize_results(self) -> None:
        """Visualize analysis results based on configuration and collect figures for later saving."""
        self._log_step("Visualizing analysis results")
        viz_config = self.config.get('visualization', {})
        plot_style = viz_config.get('plot_style', {})

        if not hasattr(self, '_figures_to_save'):
            self._figures_to_save = []

        if not viz_config.get('final_trajectory', True):
            logger.info("ℹ Final trajectory visualization disabled")
            return

        # Collect trajectories to plot
        trajectories = []
        labels = []

        # Add raw trajectory if available
        if self.trajectories['T_model_origin_mand_landmark_t'] is not None:
            trajectories.append(self.trajectories['T_model_origin_mand_landmark_t'])
            labels.append('Raw in Model CS')

        # Add smoothed trajectory if available
        if self.trajectories['T_model_origin_mand_landmark_t_smooth'] is not None:
            trajectories.append(self.trajectories['T_model_origin_mand_landmark_t_smooth'])
            labels.append('Smoothed in Model CS')

        if not trajectories:
            logger.warning("⚠ No trajectories available for visualization")
            return

        # Extract plot style parameters
        plot_params = {
            'plot_3d': True,
            'plot_rot': viz_config.get('plot_rot_3d', True),
            'sample_rate': plot_style.get('sample_rate', 10),
            'linewidth': plot_style.get('linewidth', 1.5),
            'labelpad_scale': plot_style.get('labelpad_scale', 1.0),
            'axes_label_fontsize': plot_style.get('axes_label_fontsize'),
            'axes_tick_fontsize': plot_style.get('axes_tick_fontsize'),
            'title_fontsize': plot_style.get('title_fontsize'),
            'legend_fontsize': plot_style.get('legend_fontsize'),
            'figure_size': plot_style.get('figure_size'),
            'view_3d': plot_style.get('view_3d'),
            'colors': plot_style.get('colors'),
            'line_styles': plot_style.get('line_styles'),
            'grid_enabled': plot_style.get('grid', {}).get('enabled', True),
            'grid_alpha': plot_style.get('grid', {}).get('alpha', 0.3)
        }

        # Plot all trajectories together (3D)
        fig, ax = hlp.plot_trajectories(
            trajectories,
            title='Jaw Motion in Global Model Coordinates',
            labels=labels,
            **plot_params
        )
        plt.show()
        self._figures_to_save.append((fig, 'jaw_motion_all_3d.png', 'png'))

        # Plot 2D components if configured
        if viz_config.get('plot_2d_components', True):
            plot_params['plot_3d'] = False
            fig, ax = hlp.plot_trajectories(
                trajectories,
                title='Jaw Motion in Global Model Coordinates (2D Components)',
                labels=labels,
                **plot_params
            )
            plt.show()
            self._figures_to_save.append((fig, 'jaw_motion_all_2d.png', 'png'))

        # Plot only the export trajectory if configured
        if viz_config.get('plot_export_only', False) and self.active_trajectory is not None:
            plot_params['plot_3d'] = True
            fig, ax = hlp.plot_trajectories(
                [self.active_trajectory],
                title=f'Trajectory for Export ({self.active_trajectory_label})',
                labels=[self.active_trajectory_label],
                **plot_params
            )
            plt.show()
            self._figures_to_save.append((fig, f'trajectory_export_{self.active_trajectory_label}.png', 'png'))

    def analyze_motion(self) -> Dict[str, np.ndarray]:
        """
        Perform complete motion analysis pipeline.

        Pipeline steps:
        1. Extract calibration points and compute landmark-to-marker transforms
        2. Compute relative motion between markers
        3. Transform to anatomical landmark coordinates
        4. Register to model coordinate system
        5. Apply smoothing (if configured)

        Returns:
            Dictionary containing all computed trajectories
        """
        self._log_step("Starting jaw motion analysis pipeline")

        # Step 1: Calibration
        self.perform_calibration()

        # Step 2: Relative motion
        self.compute_relative_motion()

        # Step 3: Transform to landmark
        self.transform_to_ref_markers_coordinates()

        # Step 4: Register to model
        self.register_to_model_coordinates()

        # Step 5: Smooth (optional)
        self.smooth_trajectory()

        # Visualize results
        self.visualize_results()

        self._log_step("Analysis pipeline completed")

        # Return all trajectories
        return {k: v for k, v in self.trajectories.items() if v is not None}

    def save_results(self) -> None:
        """Save analysis results based on configuration."""
        self._log_step("Saving analysis results")

        output_config = self.config['output']

        # Create output directory if needed
        output_dir = Path(output_config['directory'])
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save the active trajectory to CSV
        if output_config.get('save_csv', True) and self.active_trajectory is not None:
            csv_filename = output_dir / f"{output_config.get('csv_filename', 'jaw_motion')}_{self.active_trajectory_label}.csv"
            hlp.save_transformation_to_csv(self.active_trajectory, csv_filename)
            logger.info(f"✓ Saved {self.active_trajectory_label} trajectory to {csv_filename}")

        # Save to HDF5
        if output_config.get('save_hdf5', True):
            self._save_hdf5_results(output_dir)

        # Generate plots
        if output_config.get('save_plots', False):
            plots_dir = output_dir / 'plots'
            plots_dir.mkdir(parents=True, exist_ok=True)
            self._save_plots(plots_dir)

        self._log_step(f"Results saved to {output_dir}")

    def _save_hdf5_results(self, output_dir: Path) -> None:
        """
        Save results to HDF5 format.

        Args:
            output_dir: Directory where HDF5 file will be saved
        """
        filename = output_dir / self.config['output'].get('hdf5_filename', 'jaw_motion.h5')

        # Prepare data and metadata
        transforms = []
        sample_rates = []
        metadata_list = []
        group_names = []

        # Add raw trajectory if available
        if self.trajectories['T_model_origin_mand_landmark_t'] is not None:
            transforms.append(self.trajectories['T_model_origin_mand_landmark_t'])
            # Streaming data doesn't have frame_rate attribute
            frame_rate = getattr(self.motion_data, 'frame_rate', None)
            if frame_rate is None:
                raise RuntimeError("Frame rate not available. Streaming data sources do not support HDF5 export.")
            sample_rates.append(frame_rate)
            metadata_list.append(f"Raw T_model_origin_mand_landmark_t. Config: {json.dumps(self.config)}")
            group_names.append('T_model_origin_mand_landmark_t')

        # Add smoothed trajectory if available and different
        if (self.trajectories['T_model_origin_mand_landmark_t_smooth'] is not None and
                self.active_trajectory_label == "smoothed"):
            transforms.append(self.trajectories['T_model_origin_mand_landmark_t_smooth'])
            frame_rate = getattr(self.motion_data, 'frame_rate', None)
            if frame_rate is None:
                raise RuntimeError("Frame rate not available. Streaming data sources do not support HDF5 export.")
            sample_rates.append(frame_rate)
            smooth_config = self.config['analysis']['smoothing']
            metadata_list.append(
                f"Smoothed T_model_origin_mand_landmark_t. "
                f"Window={smooth_config['window_length']}, PolyOrder={smooth_config['poly_order']}. "
                f"Config: {json.dumps(self.config)}"
            )
            group_names.append('T_model_origin_mand_landmark_t_smooth')

        if transforms:
            hlp.store_transformations(
                transforms,
                sample_rates,
                filename,
                metadata_list,
                store_as_quaternion=self.config['output'].get('store_quaternions', True),
                derivative_order=self.config['output'].get('derivative_order', 2),
                scale_factor=self.config['output'].get('scale_factor', 1.0),
                unit=self.config['output'].get('unit', 'mm'),
                group_names=group_names
            )
            logger.info(f"✓ Saved {len(transforms)} trajectories to {filename}")
        else:
            logger.warning("⚠ No trajectories available for HDF5 export")

    def _save_plots(self, output_dir: Path) -> None:
        """
        Save all collected figures to files, including optional TikZ/PGF export via tikzplotlib.

        Args:
            output_dir: Directory where plots will be saved
        """
        output_config = self.config.get('output', {})
        save_tikz = output_config.get('save_tikz', False)

        if save_tikz:
            try:
                import tikzplotlib
            except ImportError:
                logger.warning("tikzplotlib is not installed. TikZ export will be skipped.")
                save_tikz = False

        if not hasattr(self, '_figures_to_save') or not self._figures_to_save:
            logger.warning("No figures to save. Did you run visualize_results()?")
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        plots_dir = output_dir / self.config.get('output', {}).get('csv_filename', 'plots')
        plots_dir.mkdir(parents=True, exist_ok=True)

        for fig, fname, ftype in self._figures_to_save:
            out_path = plots_dir / fname
            fig.savefig(out_path, bbox_inches='tight')
            logger.info(f"Saved plot: {out_path}")

            if save_tikz and ftype == 'png':
                try:
                    import tikzplotlib
                    tikz_path = str(out_path).replace('.png', '.tex')
                    tikzplotlib.save(tikz_path, figure=fig)
                    logger.info(f"Saved TikZ plot: {tikz_path}")
                except Exception as e:
                    logger.warning(f"Failed to save TikZ for {out_path}: {e}")

        # Optionally clear after saving
        self._figures_to_save.clear()

    def run_analysis(self) -> Dict[str, np.ndarray]:
        """
        Run the complete analysis pipeline.

        Returns:
            Dictionary of all computed trajectories
        """
        # Load data
        self.load_data()

        # Run analysis
        results = self.analyze_motion()

        # Save results
        self.save_results()

        return results


def validation(paths: list[str], scale_factor: float = 1.0, labels: Optional[list[str]] = None) -> None:
    """
    Validates simulated trajectory data against ground truth and optionally feasible poses.

    This function performs the following steps:
        1.  Loads ground truth pose data (assumed to be 'pose_data.csv') from the directory
            specified by the first path in the `paths` list.
        2.  Loads simulated pose data (assumed to be 'pose_sim.csv') from each directory
            specified in the `paths` list.
        3.  Optionally, loads feasible pose data (assumed to be 'feasible_pos.csv') from
            each directory if the file exists.
        4.  Generates and displays a 3D plot comparing the ground truth trajectory against
            all simulated trajectories.
        5.  For each simulated trajectory, calculates and logs the following error metrics
            against the ground truth:
            - Mean Absolute Error (MAE)
            - Root Mean Square Error (RMSE)
            - Maximum Error
            - Minimum Error
        6.  If feasible pose data is available for a simulation, it also calculates and logs
            the same error metrics for the simulated trajectory against its corresponding
            feasible poses.
        7.  Handles potential discrepancies in the number of frames between datasets by
            comparing up to the minimum length.
        8.  Manages plot labels, using provided labels or generating default ones.

    Args:
        paths: A list of strings, where each string is a path to a directory.
               The first path MUST point to the directory containing the ground truth
               data file ('pose_data.csv'). Subsequent paths (or the first path itself,
               if it also contains simulation data) should point to directories
               containing simulation data files ('pose_sim.csv') and optionally
               feasible pose data files ('feasible_pos.csv').
        scale_factor: A float used to scale the error metrics.

                      - If input data (CSVs) is in millimeters (mm) and errors are desired in mm,
                        `scale_factor` should be 1.0.
                      - If input data is in mm and errors are desired in meters (m),
                        `scale_factor` should be 0.001.
                      - If input data is in m and errors are desired in mm,
                        `scale_factor` should be 1000.0.
                      The default is 1.0, assuming input CSVs and desired error units are consistent (e.g., mm).
        labels: An optional list of strings for labeling the trajectories in the plot.
                If provided for simulations, ensure one label per simulation path.
                A "Ground Truth" label will be automatically prepended.
                Alternatively, provide N+1 labels for Ground Truth + N simulations.
                If None, default labels ('Ground Truth', 'Simulation 0', 'Simulation 1', ...)
                will be generated.
    """
    logger.info(f"Running validation for paths: {paths} with scale_factor: {scale_factor}")

    pose_data_path = os.path.join(paths[0], 'pose_data.csv')
    logger.info(f"Loading ground truth pose data from: {pose_data_path}")
    pose_data = hlp.load_csv_to_transformations(pose_data_path)
    pos_data = pose_data[:, :3, 3]

    all_poses_sim = []
    all_poses_feasible = []

    for path_idx, path in enumerate(paths):
        sim_path_str = f" (simulation {path_idx})" if len(paths) > 1 else ""

        pose_sim_path = os.path.join(path, 'pose_sim.csv')
        logger.info(f"Loading simulation pose data from: {pose_sim_path}{sim_path_str}")
        pose_sim = hlp.load_csv_to_transformations(pose_sim_path)
        all_poses_sim.append(pose_sim)

        feasible_pose_path = os.path.join(path, 'feasible_pos.csv')
        if os.path.exists(feasible_pose_path):
            logger.info(f"Loading feasible pose data from: {feasible_pose_path}{sim_path_str}")
            feasible_pose = hlp.load_csv_to_transformations(feasible_pose_path)
            all_poses_feasible.append(feasible_pose)
        else:
            logger.warning(f"Feasible pose data not found at: {feasible_pose_path}{sim_path_str}, skipping.")
            all_poses_feasible.append(None)

    if labels is None:
        labels_for_plot = ['Ground Truth'] + [f'Simulation {i}' for i in range(len(paths))]
    else:
        if len(labels) == len(paths):
            labels_for_plot = ['Ground Truth'] + labels
        elif len(labels) == len(paths) + 1:
            labels_for_plot = labels
        else:
            logger.warning(
                f"Number of labels ({len(labels)}) does not match number of datasets ({len(paths) + 1}). "
                f"Using default labels."
            )
            labels_for_plot = ['Ground Truth'] + [f'Simulation {i}' for i in range(len(paths))]

    hlp.plot_trajectories([pose_data] + all_poses_sim, title='Trajectory Comparison (Validation)',
                          labels=labels_for_plot,
                          plot_3d=True,
                          plot_rot=False,
                          sample_rate=10, linewidth=1.5)

    # Compute error metrics
    pos_sim_all = [pose[:, :3, 3] for pose in all_poses_sim]

    for i, pos_sim_single in enumerate(pos_sim_all):
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Metrics for Simulation {i} (Path: {paths[i]})")
        logger.info(f"{'=' * 60}")

        # Ensure pos_sim and pos_data have the same length for comparison
        min_len = min(len(pos_sim_single), len(pos_data))
        if len(pos_sim_single) != len(pos_data):
            logger.warning(
                f"Simulation {i} length ({len(pos_sim_single)}) and ground truth length ({len(pos_data)}) differ. "
                f"Comparing up to frame {min_len - 1}."
            )

        pos_sim_aligned = pos_sim_single[:min_len]
        pos_data_aligned = pos_data[:min_len]

        # MAE vs Ground Truth
        diff_data = np.linalg.norm(pos_sim_aligned - pos_data_aligned, axis=1)
        mae_data = np.mean(diff_data) * scale_factor
        rmse_data = np.sqrt(np.mean(diff_data ** 2)) * scale_factor
        max_error_data = np.max(diff_data) * scale_factor
        min_error_data = np.min(diff_data) * scale_factor

        logger.info(f"\nComparison against Ground Truth (pose_data.csv from {paths[0]}):")
        logger.info(f"  MAE:          {mae_data:.6f}")
        logger.info(f"  RMSE:         {rmse_data:.6f}")
        logger.info(f"  Max Error:    {max_error_data:.6f}")
        logger.info(f"  Min Error:    {min_error_data:.6f}")

        # Comparison vs Feasible Poses (if available for this simulation)
        if i < len(all_poses_feasible) and all_poses_feasible[i] is not None:
            pos_feasible_single = all_poses_feasible[i][:, :3, 3]

            min_len_feas = min(len(pos_sim_single), len(pos_feasible_single))
            if len(pos_sim_single) != len(pos_feasible_single):
                logger.warning(
                    f"Simulation {i} length ({len(pos_sim_single)}) and its feasible poses length "
                    f"({len(pos_feasible_single)}) differ. Comparing up to frame {min_len_feas - 1}."
                )

            pos_sim_aligned_feas = pos_sim_single[:min_len_feas]
            pos_feasible_aligned = pos_feasible_single[:min_len_feas]

            diff_feasible = np.linalg.norm(pos_sim_aligned_feas - pos_feasible_aligned, axis=1)
            mae_feasible = np.mean(diff_feasible) * scale_factor
            rmse_feasible = np.sqrt(np.mean(diff_feasible ** 2)) * scale_factor
            max_error_feasible = np.max(diff_feasible) * scale_factor
            min_error_feasible = np.min(diff_feasible) * scale_factor

            logger.info(f"\nComparison against Feasible Poses (feasible_pos.csv from {paths[i]}):")
            logger.info(f"  MAE Feasible: {mae_feasible:.6f}")
            logger.info(f"  RMSE Feasible:{rmse_feasible:.6f}")
            logger.info(f"  Max Error Feasible: {max_error_feasible:.6f}")
            logger.info(f"  Min Error Feasible: {min_error_feasible:.6f}")


def main():
    """Main entry point for jaw motion analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Jaw Motion Analysis Framework - '
                    'Processes motion capture data to analyze jaw movement, '
                    'transform it to model coordinates, smooth, visualize, and export.'
    )
    parser.add_argument('config', help='Path to JSON configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--plot', '-p', action='store_true', help='Show plots during analysis')

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # Load configuration
        config = ConfigManager.load_config(args.config)

        # Override plot settings if requested
        if args.plot:
            if 'visualization' not in config:
                config['visualization'] = {}
            config['visualization']['show_plots'] = True

        # Set PGF/LaTeX plotting option globally in helper.py if requested in config
        if config.get('visualization', {}).get('use_tex_font', False):
            hlp.USE_TEX_FONT = True
            # Re-apply matplotlib PGF/LaTeX settings if needed
            import matplotlib
            matplotlib.rcParams.update({
                "pgf.texsystem": "pdflatex",
                "text.usetex": True,
                "font.family": "serif",
                "font.size": 10,  # Match your document's font size
                "axes.labelsize": 10,
                "legend.fontsize": 8,
                "font.serif": ["Times New Roman", "Times", "DejaVu Serif", "serif"],
                "font.sans-serif": [],
                "pgf.rcfonts": False,
                "pgf.preamble": r"\usepackage{mathptmx}\usepackage[utf8x]{inputenc}\usepackage[T1]{fontenc}",
            })
            # plt.switch_backend("pgf")

        # Create and run analysis
        analysis = JawMotionAnalysis(config)
        results = analysis.run_analysis()

        logger.info("\n" + "=" * 60)
        logger.info("✓ ANALYSIS COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("Processed trajectories:")
        for name, trajectory in results.items():
            if trajectory is not None:
                logger.info(f"  - {name}: {trajectory.shape[0]} frames")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()

    # # Setup for main analysis or validation based on arguments
    # # The argparse setup implies this script is primarily for validation when run directly.
    # # To run the main analysis, one might call main_analysis() directly or comment out parser.
    #
    # # Default behavior: run validation if script is called with arguments,
    # # otherwise, consider running main_analysis.
    # # For now, let's assume if __name__ == '__main__', it's for validation as per parser.
    # # To run the analysis, one would typically call `main_analysis()` from elsewhere or uncomment it here.
    #
    # # main_analysis() # Uncomment to run the main analysis pipeline
    #
    # # Argument parser for validation
    # parser = argparse.ArgumentParser(
    #     description='Validate transformation data from simulations against ground truth. '
    #                 'The first path in `paths` should point to the directory containing the '
    #                 'ground truth `pose_data.csv`. Subsequent paths (or the first path itself, '
    #                 'if it also contains simulation data) point to directories with `pose_sim.csv` '
    #                 'and optionally `feasible_pos.csv`.')
    # parser.add_argument('paths', type=str, nargs='+',
    #                     help='List of paths. First path: directory with `pose_data.csv` (ground truth). '
    #                          'All paths: directories with `pose_sim.csv` and optionally `feasible_pos.csv`.')
    # parser.add_argument('--scale_factor', type=float, default=1e-3,
    #                     help='Scale factor for error metrics (e.g., 1e-3 to convert mm to m, 1.0 for same units). Default: 1e-3.')
    # parser.add_argument('--labels', type=str, nargs='+',
    #                     help='List of labels for the plots. If provided for simulations, ensure one label per simulation path. '
    #                          'A "Ground Truth" label will be prepended. Or provide N+1 labels for GT + N sims.')
    #
    # # Check if any arguments were passed. If not, maybe run main_analysis?
    # # This is a common pattern: if no args, run default function. If args, parse them.
    # import sys
    #
    # if len(sys.argv) > 1 and sys.argv[1] not in ['-h', '--help']:  # Basic check if args other than help are present
    #     print("Running validation script with command line arguments...")
    #     args = parser.parse_args()
    #     validation(args.paths, args.scale_factor, args.labels)
    # else:
    #     # No specific arguments for validation, or help was requested.
    #     # If help was requested, argparse handles it.
    #     # If no args, you might want to run main_analysis() or print help.
    #     if len(sys.argv) == 1:  # No arguments at all
    #         print("No command line arguments provided for validation. Running main analysis pipeline instead.")
    #         main_analysis()
    #     # If only -h/--help, argparse will show help and exit.
    #     # else:
    #     # parser.print_help() # Or handle other cases
