#!/usr/bin/env python3

"""
qualisys.py: Qualisys motion capture system specific implementations.

This module provides classes and utilities specifically for handling
Qualisys QTM motion capture data exported as .mat files.
"""

__author__ = "Paul-Otto Müller"
__copyright__ = "Copyright 2025, Paul-Otto Müller"
__credits__ = ["Paul-Otto Müller"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "1.1.0"
__maintainer__ = "Paul-Otto Müller"
__status__ = "Development"
__date__ = '16.10.2025'
__url__ = "https://github.com/paulotto/jaw_tracking_system"

import h5py
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass

from scipy.io import loadmat
from sklearn.decomposition import PCA

# Import general utilities from helper module
from . import helper as hlp

# Use the logger from helper module
logger = hlp.setup_logger(__name__)


@dataclass
class RigidBody:
    """Represents a rigid body tracked by the Qualisys motion capture system."""
    name: str
    filter: str = ""
    coordinate_system: Optional[np.ndarray] = None
    positions: Optional[np.ndarray] = None
    rotations: Optional[np.ndarray] = None
    rpy: Optional[np.ndarray] = None
    residuals: Optional[np.ndarray] = None

    def __post_init__(self):
        """Validate rigid body data."""
        if self.positions is not None and self.rotations is not None:
            if len(self.positions) != len(self.rotations):
                raise ValueError(f"Positions and rotations must have same length for rigid body {self.name}")


class QualysisData:
    """
    Handles loading and processing of Qualisys motion capture data.

    This class loads .mat files exported from Qualisys QTM software and provides
    methods for data manipulation and analysis.
    """

    def __init__(self, filename: str,
                 hdf5: bool = False,
                 struct_as_record: bool = True,
                 squeeze_me: bool = False) -> None:
        """
        Initialize the QualysisData object by loading data from a mat file.

        Args:
            filename: Path to the mat file to load
            hdf5: If True, load using h5py (for newer mat files)
            struct_as_record: If True, preserve mat file structure
            squeeze_me: If True, remove singleton dimensions

        Raises:
            FileNotFoundError: If the specified file doesn't exist
            ValueError: If no valid data is found in the file
        """
        if not Path(filename).exists():
            raise FileNotFoundError(f"File not found: {filename}")

        logger.info(f"Loading Qualisys data from: {filename}")

        self.data = self._load_mat_file(filename, hdf5, struct_as_record, squeeze_me)
        self._parse_mat_data()

    @staticmethod
    def _load_mat_file(filename: str, hdf5: bool,
                       struct_as_record: bool, squeeze_me: bool) -> Union[h5py.File, dict]:
        """Load mat file with appropriate method."""
        if hdf5:
            return h5py.File(filename, 'r')
        return loadmat(filename, struct_as_record=struct_as_record, squeeze_me=squeeze_me)

    def _parse_mat_data(self) -> None:
        """Parse the loaded mat file data structure."""
        self.header = self.data['__header__']
        self.version = self.data['__version__']
        self.global_vars = self.data['__globals__']

        # Find main data key (non-dunder key)
        main_key = next((k for k in self.data.keys()
                         if not (k.startswith('__') and k.endswith('__'))), None)

        if not main_key:
            raise ValueError("No valid data found in the file")

        main_data = self.data[main_key]

        # Extract basic properties
        self.orig_filename = main_data['File']  # type: ignore
        self.timestamp = main_data['Timestamp']  # type: ignore
        self.start_frame = int(main_data['StartFrame'])  # type: ignore
        self.frames = int(main_data['Frames'])  # type: ignore
        self.frame_rate = float(main_data['FrameRate'])  # type: ignore
        self.trajectories = main_data['Trajectories']  # type: ignore

        # Parse rigid bodies
        self.rigid_bodies = self._parse_rigid_bodies(main_data['RigidBodies'][0, 0])  # type: ignore

        logger.info(f"Loaded {len(self.rigid_bodies)} rigid bodies, "
                    f"{self.frames} frames at {self.frame_rate} Hz")

    def _parse_rigid_bodies(self, rigid_body_data: Any) -> Dict[str, RigidBody]:
        """Parse rigid body data from mat file structure."""
        rigid_bodies = {}
        num_bodies = int(rigid_body_data['Bodies'][0][0][0][0])

        for n in range(num_bodies):
            rb = RigidBody(
                name=rigid_body_data['Name'][0][0][0][n][0],
                filter=rigid_body_data['Filter'][0][0][0][n][0][0],
                coordinate_system=rigid_body_data['CoordinateSystem'][0][0][0][n]
            )

            # Extract and transpose position data
            rb.positions = np.transpose(rigid_body_data['Positions'][0][0][n, :, :], (1, 0))

            # Extract and process rotation data
            raw_rotations = np.transpose(rigid_body_data['Rotations'][0][0][n, :, :], (1, 0))
            rb.rotations = self._process_rotation_matrices(raw_rotations)

            # Extract RPY and residuals
            rb.rpy = np.transpose(rigid_body_data['RPYs'][0][0][n, :, :], (1, 0))
            rb.residuals = np.transpose(rigid_body_data['Residual'][0][0][n, :, :], (1, 0))

            rigid_bodies[rb.name] = rb
            logger.debug(f"Loaded rigid body '{rb.name}' with {len(rb.positions)} frames")

        return rigid_bodies

    @staticmethod
    def _process_rotation_matrices(raw_rotations: np.ndarray) -> np.ndarray:
        """
        Process raw rotation data from Qualisys.

        Qualisys stores rotations in column-major order, so we need to transpose them.
        """
        num_frames = raw_rotations.shape[0]
        rotations = np.zeros((num_frames, 3, 3))

        for i in range(num_frames):
            # Transpose due to column-major storage in Qualisys
            rotations[i] = raw_rotations[i].reshape(3, 3).T

        return rotations

    @staticmethod
    def compute_coordinate_system(points: np.ndarray, origin_index: int = -1) -> np.ndarray:
        """
        Compute an orthonormal coordinate system from points using PCA.

        Args:
            points: Array of shape (n, 3) with at least 3 points
            origin_index: Index of point to use as origin (-1 for centroid)

        Returns:
            4x4 homogeneous transformation matrix

        Raises:
            ValueError: If fewer than 3 points are provided
        """
        if points.shape[0] < 3:
            raise ValueError("At least three points are required to compute a coordinate system")

        # Determine origin
        origin = np.mean(points, axis=0) if origin_index == -1 else points[origin_index]

        # Center points and compute PCA
        centered_points = points - origin
        pca = PCA(n_components=3)
        pca.fit(centered_points)

        # Get orthonormal coordinate system
        coord_system = pca.components_.T
        coord_system = hlp.ensure_orthonormal(coord_system)

        # Build transformation matrix
        T = np.eye(4)
        T[:3, :3] = coord_system
        T[:3, 3] = origin

        return T

    @staticmethod
    def compute_relative_transformations(rigid_bodies: List[RigidBody],
                                         frame_intervals: List[Tuple[int, int]],
                                         check_nan: bool = True) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Compute relative transformations between rigid body pairs.

        Args:
            rigid_bodies: List of RigidBody objects
            frame_intervals: List of (start_frame, end_frame) tuples
            check_nan: If True, check for and report NaN values

        Returns:
            Nested dictionary: {interval_key: {pair_key: transforms}}
        """
        relative_transformations = {}

        for start_frame, end_frame in frame_intervals:
            interval_key = f'{start_frame}-{end_frame}'
            relative_transformations[interval_key] = {}

            # Process all unique pairs
            for i, rb1 in enumerate(rigid_bodies):
                for j, rb2 in enumerate(rigid_bodies):
                    if i >= j:  # Skip self and duplicate pairs
                        continue

                    transforms = QualysisData._compute_pairwise_transforms(
                        rb1, rb2, start_frame, end_frame, check_nan
                    )

                    pair_key = f'{rb1.name}-{rb2.name}'
                    relative_transformations[interval_key][pair_key] = transforms

        return relative_transformations

    @staticmethod
    def _compute_pairwise_transforms(rb1: RigidBody, rb2: RigidBody,
                                     start_frame: int, end_frame: int,
                                     check_nan: bool) -> np.ndarray:
        """Compute relative transforms between two rigid bodies."""
        # Extract data for frame interval
        pos1 = rb1.positions[start_frame:end_frame + 1]  # type: ignore
        rot1 = rb1.rotations[start_frame:end_frame + 1]  # type: ignore
        pos2 = rb2.positions[start_frame:end_frame + 1]  # type: ignore
        rot2 = rb2.rotations[start_frame:end_frame + 1]  # type: ignore

        # Check for NaN values if requested
        if check_nan:
            nan_mask = (np.isnan(pos1).any(axis=1) | np.isnan(pos2).any(axis=1) |
                        np.isnan(rot1).any(axis=(1, 2)) | np.isnan(rot2).any(axis=(1, 2)))
            if nan_mask.any():
                nan_frames = np.where(nan_mask)[0] + start_frame
                logger.warning(f"NaN values detected in frames: {nan_frames}")

        # Compute relative transformations
        num_frames = pos1.shape[0]
        relative_transforms = np.zeros((num_frames, 4, 4))

        for k in range(num_frames):
            T1 = hlp.build_transform(pos1[k], rot1[k])
            T2 = hlp.build_transform(pos2[k], rot2[k])

            # T_1_2 = inv(T1) @ T2
            relative_transforms[k] = np.linalg.inv(T1) @ T2

        return relative_transforms

    @staticmethod
    def compute_average_transformations(rigid_bodies: List[RigidBody],
                                        frame_intervals: List[Tuple[int, int]]) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Compute average relative transformations for frame intervals.

        Returns transformation matrices averaged over each frame interval.
        """
        # First compute all relative transformations
        relative_transforms = QualysisData.compute_relative_transformations(
            rigid_bodies, frame_intervals
        )

        average_transformations = {}

        for interval_key, pairs in relative_transforms.items():
            average_transformations[interval_key] = {}

            for pair_key, transforms in pairs.items():
                # Average the transformations
                avg_transform = np.mean(transforms, axis=0)

                # Ensure valid transformation matrix
                avg_transform[:3, :3] = hlp.ensure_orthonormal(avg_transform[:3, :3])
                avg_transform[3, :] = [0, 0, 0, 1]

                average_transformations[interval_key][pair_key] = avg_transform

        return average_transformations


class QualysisDataPlotUtils:
    """Utilities for visualizing Qualisys motion capture data."""

    def __init__(self, data: QualysisData):
        """Initialize with QualysisData instance."""
        self.data = data

    def visualize_qualysis_data(self, three_d: bool = False,
                                frame_interval: Optional[Tuple[int, int]] = None) -> None:
        """
        Visualize motion capture data.

        Args:
            three_d: If True, create 3D plots; otherwise 2D component plots
            frame_interval: Optional (start, end) frames to visualize
        """
        rigid_bodies = self.data.rigid_bodies

        # Determine frame range
        start_frame, end_frame = frame_interval if frame_interval else (0, None)

        if three_d:
            self._plot_3d_trajectories(rigid_bodies, start_frame, end_frame)
        else:
            self._plot_2d_components(rigid_bodies, start_frame, end_frame)

        plt.tight_layout()
        plt.show()

    @staticmethod
    def _plot_3d_trajectories(rigid_bodies: Dict[str, RigidBody],
                              start_frame: int, end_frame: Optional[int]) -> None:
        """Create 3D trajectory plots."""
        fig = plt.figure(figsize=(15, 5 * ((len(rigid_bodies) + 2) // 3)))

        for i, (name, body) in enumerate(rigid_bodies.items()):
            ax = fig.add_subplot(
                (len(rigid_bodies) + 2) // 3, 3, i + 1,
                projection='3d'
            )

            positions = body.positions[start_frame:end_frame]  # type: ignore
            ax.plot(positions[:, 0], positions[:, 1], positions[:, 2],
                    label=name, linewidth=2)

            ax.set_title(f'{name} Trajectory')
            ax.set_xlabel('X [mm]')
            ax.set_ylabel('Y [mm]')
            ax.set_zlabel('Z [mm]')  # type: ignore
            ax.legend()

    @staticmethod
    def _plot_2d_components(rigid_bodies: Dict[str, RigidBody],
                            start_frame: int, end_frame: Optional[int]) -> None:
        """Create 2D component plots."""
        num_bodies = len(rigid_bodies)
        fig, axes = plt.subplots(num_bodies, 3, figsize=(12, 4 * num_bodies))

        if num_bodies == 1:
            axes = [axes]

        for i, (name, body) in enumerate(rigid_bodies.items()):
            positions = body.positions[start_frame:end_frame]  # type: ignore
            frames = np.arange(len(positions))

            # Plot each component
            for j, (component, color) in enumerate([('X', 'r'), ('Y', 'g'), ('Z', 'b')]):
                axes[i][j].plot(frames, positions[:, j], color=color, linewidth=2)
                axes[i][j].set_title(f'{name} - {component}')
                axes[i][j].set_xlabel('Frame')
                axes[i][j].set_ylabel(f'{component} [mm]')
                axes[i][j].grid(True, alpha=0.3)


# Utility function specific to Qualisys data
def T_from_rigid_body(rigid_body: RigidBody,
                      frame_interval: Optional[Tuple[int, int]] = None) -> np.ndarray:
    """
    Extract transformation matrices from a Qualisys RigidBody.

    Args:
        rigid_body: RigidBody object
        frame_interval: Optional (start, end) frames

    Returns:
        Array of shape (N, 4, 4) transformation matrices
    """
    start, end = frame_interval if frame_interval else (0, None)

    positions = rigid_body.positions[start:end]  # type: ignore
    rotations = rigid_body.rotations[start:end]  # type: ignore

    num_frames = len(positions)
    transformations = np.zeros((num_frames, 4, 4))

    for i in range(num_frames):
        transformations[i] = hlp.build_transform(positions[i], rotations[i])

    return transformations
