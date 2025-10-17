#!/usr/bin/env python3

"""
helper.py: General helper functions and utilities for motion capture data processing.

This module provides general-purpose utilities that are not specific to any
particular motion capture system.
"""

__author__ = "Paul-Otto Müller"
__copyright__ = "Copyright 2025, Paul-Otto Müller"
__credits__ = ["Paul-Otto Müller"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "1.0.4"
__maintainer__ = "Paul-Otto Müller"
__status__ = "Development"
__date__ = '16.10.2025'
__url__ = "https://github.com/paulotto/jaw_tracking_system"

import h5py
import csv
import numpy as np
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from typing import List, Dict, Tuple, Optional, Union

from scipy.signal import savgol_filter
from scipy.spatial.transform import Rotation as R

# Global variable to enable PGF/LaTeX output for matplotlib
USE_TEX_FONT = False  # Set to True to enable PGF/LaTeX output globally

if USE_TEX_FONT:
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


# Custom logger with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""

    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, record) -> str:
        """
        Format the log record with colors and separators.

        Args:
            record: The log record to format
        Returns:
            str: The formatted log message with colors and separators
        """
        # Add color to the log level
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"

        # Format the message
        formatted = super().format(record)

        # Add separator for better readability
        if levelname in ['ERROR', 'CRITICAL']:
            formatted = f"\n{'=' * 80}\n{formatted}\n{'=' * 80}"
        elif record.msg.startswith('[STEP]'):
            formatted = f"\n{'-' * 60}\n{formatted}\n{'-' * 60}"

        return formatted


def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with colored output.

    Args:
        name: Name of the logger (default: module name)
        level: Logging level (default: INFO)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Use colored formatter
    formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Set up module logger
logger = setup_logger(__name__)


def enable_better_3d_rotation(ax):
    """
    Enable improved 3D rotation in a matplotlib 3D plot by dragging with the left mouse button.
    Allows smooth rotation around all axes.
    """
    press = {'x': None, 'y': None, 'elev': None, 'azim': None, 'button': None}

    def on_press(event):
        if event.inaxes != ax:
            return
        if event.button == 1:  # Left mouse button
            press['x'] = event.x
            press['y'] = event.y
            press['elev'] = ax.elev
            press['azim'] = ax.azim
            press['button'] = 1  # type: ignore

    def on_release(event):
        press['button'] = None

    def on_move(event):
        if press['button'] != 1 or event.inaxes != ax:
            return
        dx = event.x - press['x']
        dy = event.y - press['y']
        new_elev = press['elev'] + dy * 0.5
        new_azim = press['azim'] - dx * 0.5
        ax.view_init(elev=new_elev, azim=new_azim)
        ax.figure.canvas.draw_idle()

    ax.figure.canvas.mpl_connect('button_press_event', on_press)
    ax.figure.canvas.mpl_connect('button_release_event', on_release)
    ax.figure.canvas.mpl_connect('motion_notify_event', on_move)


# Transformation utilities

def build_transform(position: np.ndarray, rotation: np.ndarray) -> np.ndarray:
    """
    Build 4x4 homogeneous transformation matrix.

    Args:
        position: 3D position vector
        rotation: 3x3 rotation matrix

    Returns:
        4x4 transformation matrix
    """
    T = np.eye(4)
    T[:3, :3] = rotation
    T[:3, 3] = position
    return T


def ensure_orthonormal(matrix: np.ndarray) -> np.ndarray:
    """
    Ensure a 3x3 matrix is orthonormal using SVD.

    Args:
        matrix: 3x3 matrix to orthonormalize

    Returns:
        Orthonormal 3x3 matrix with det = +1
    """
    u, _, vt = np.linalg.svd(matrix)
    result = u @ vt

    # Ensure positive determinant (proper rotation)
    if np.linalg.det(result) < 0:
        result[:, -1] *= -1

    return result


def kabsch_algorithm(P: np.ndarray, Q: np.ndarray) -> np.ndarray:
    """
    Compute optimal rigid transformation using Kabsch algorithm.

    Finds transformation T such that Q ≈ T @ P (minimizes ||Q - T @ P||²)

    Args:
        P: Source points, shape (N, 3)
        Q: Target points, shape (N, 3)

    Returns:
        4x4 homogeneous transformation matrix
    """
    if P.shape != Q.shape:
        raise ValueError("Point sets must have same shape")

    # Compute centroids
    centroid_P = np.mean(P, axis=0)
    centroid_Q = np.mean(Q, axis=0)

    # Center the points
    P_centered = P - centroid_P
    Q_centered = Q - centroid_Q

    # Compute optimal rotation using SVD
    H = P_centered.T @ Q_centered
    U, _, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T

    # Ensure proper rotation (det = +1)
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T

    # Compute translation
    t = centroid_Q - R @ centroid_P

    # Build transformation matrix
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t

    return T


def interval_to_string(interval: Tuple[int, int]) -> str:
    """
    Convert frame interval tuple to string representation.

    Args:
        interval: Tuple of (start_frame, end_frame)

    Returns:
        str: String representation of the interval in format "start-end"
    """
    return f'{interval[0]}-{interval[1]}'


# Filtering utilities

class TransformationFilter:
    """
    Filter for smoothing transformation trajectories.

    Uses Savitzky-Golay filtering for translations and rotations.
    The filter applies separately to translation components.
    A rotations vector representation is used for smoothing rotations,
    which better preserves the geometry of rotations compared to
    directly smoothing matrix or quaternion components.
    """

    def __init__(self, window_length: int = 11, poly_order: int = 3) -> None:
        """
        Initialize the filter.

        Args:
            window_length: Filter window length (must be odd)
            poly_order: Polynomial order for fitting

        Raises:
            ValueError: If window_length is even
        """
        if window_length % 2 == 0:
            raise ValueError("window_length must be odd")

        self.window_length = window_length
        self.poly_order = poly_order

        logger.info(f"Initialized TransformationFilter: "
                    f"window={window_length}, order={poly_order}")

    def __call__(self, transformations: np.ndarray) -> np.ndarray:
        """
        Apply filter to transformation matrices.

        Args:
            transformations: Array of shape (N, 4, 4) transformation matrices

        Returns:
            Smoothed transformations of shape (N, 4, 4)
        """
        return self.smooth(transformations)

    def smooth(self, transformations: np.ndarray) -> np.ndarray:
        """
        Smooth a sequence of 4x4 transformation matrices.

        Args:
            transformations: Array of shape (N, 4, 4)

        Returns:
            Smoothed transformations of shape (N, 4, 4)
        """
        if transformations.ndim != 3 or transformations.shape[1:] != (4, 4):
            raise ValueError("Input must have shape (N, 4, 4)")

        # Decompose into translations and rotations
        translations = transformations[:, :3, 3]
        rotations = transformations[:, :3, :3]

        # Smooth components separately
        smoothed_translations = self._smooth_translations(translations)
        smoothed_rotations = self._smooth_rotations(rotations)

        # Reconstruct transformation matrices
        smoothed = np.zeros_like(transformations)
        smoothed[:, :3, :3] = smoothed_rotations
        smoothed[:, :3, 3] = smoothed_translations
        smoothed[:, 3, 3] = 1.0

        return smoothed

    def _smooth_translations(self, translations: np.ndarray) -> np.ndarray:
        """
        Apply Savitzky-Golay filter to translation components with zero phase shift.
        The filter is symmetric and does not introduce phase lag.

        Args:
            translations: Array of shape (N, 3) translation vectors

        Returns:
            Smoothed translations of shape (N, 3)
        """
        smoothed = np.zeros_like(translations)

        for i in range(3):
            smoothed[:, i] = savgol_filter(
                translations[:, i],
                window_length=self.window_length,
                polyorder=self.poly_order,
                mode='interp'
            )

        return smoothed

    def _smooth_rotations(self, rotations: np.ndarray) -> np.ndarray:
        """
        Smooth rotations using a Savitzky-Golay filter with zero phase shift
        on the rotation vector representation.

        This approach better preserves the geometry of rotations compared
        to directly smoothing matrix or quaternion components.

        Args:
            rotations: Array of shape (N, 3, 3) rotation matrices

        Returns:
            Smoothed rotations of shape (N, 3, 3)
        """
        # Convert to rotation vectors
        rotvecs = R.from_matrix(rotations).as_rotvec()

        # Smooth rotation vector components
        smoothed_rotvecs = np.zeros_like(rotvecs)
        for i in range(3):
            smoothed_rotvecs[:, i] = savgol_filter(
                rotvecs[:, i],
                window_length=self.window_length,
                polyorder=self.poly_order,
                mode='interp'
            )

        # Convert back to rotation matrices
        return R.from_rotvec(smoothed_rotvecs).as_matrix()


# Visualization utilities

def plot_trajectories(T_list: List[np.ndarray],
                      title: str = "Trajectory",
                      labels: Optional[List[str]] = None,
                      plot_3d: bool = True,
                      plot_rot: bool = True,
                      sample_rate: int = 1,
                      linewidth: float = 2.0,
                      labelpad_scale: float = 1.0,
                      save_path: Optional[str] = None,
                      axes_label_fontsize: Optional[float] = None,
                      axes_tick_fontsize: Optional[float] = None,
                      title_fontsize: Optional[float] = None,
                      legend_fontsize: Optional[float] = None,
                      figure_size: Optional[List[float]] = None,
                      view_3d: Optional[Dict[str, float]] = None,
                      colors: Optional[List[str]] = None,
                      line_styles: Optional[List[str]] = None,
                      grid_enabled: bool = True,
                      grid_alpha: float = 0.3) -> Tuple[Figure, Axes]:
    """
    Plot transformation trajectories and return the matplotlib Figure object.

    Args:
        T_list: List of transformation arrays, each shape (N, 4, 4)
        title: Plot title
        labels: Labels for each trajectory
        plot_3d: If True, create 3D plot; else 2D components
        plot_rot: If True, include rotation visualization
        sample_rate: Sampling rate for plotting (1 = every frame)
        linewidth: Line width for plots
        labelpad_scale: Scale factor for label padding
        save_path: Optional path to save figure
        axes_label_fontsize: Font size for axes labels
        axes_tick_fontsize: Font size for axes ticks
        title_fontsize: Font size for title
        legend_fontsize: Font size for legend
        figure_size: Figure size [width, height]
        view_3d: Dict with 'elev', 'azim', 'roll', 'vertical_axis' for 3D view
        colors: List of colors for trajectories
        line_styles: List of line styles for trajectories
        grid_enabled: Whether to show grid
        grid_alpha: Grid transparency

    Returns:
        matplotlib.figure.Figure: The created figure. Does not show or close the figure.
    """
    # Set default values if not provided
    if figure_size is None:
        figure_size = [12, 8]
    if line_styles is None:
        line_styles = ['-', '--', '-.', ':']
    if colors is None:
        colors = plt.cm.tab10(np.linspace(0, 1, len(T_list)))  # type: ignore
    elif isinstance(colors, list) and all(isinstance(c, str) for c in colors):
        # If colors are provided as strings, use them cyclically
        colors = [colors[i % len(colors)] for i in range(len(T_list))]

    plt.rcParams.update({
        'figure.figsize': figure_size,
        'axes.grid': grid_enabled,
        'grid.alpha': grid_alpha,
    })

    # Update font sizes if provided
    if axes_label_fontsize:
        plt.rcParams['axes.labelsize'] = axes_label_fontsize
    if axes_tick_fontsize:
        plt.rcParams['xtick.labelsize'] = axes_tick_fontsize
        plt.rcParams['ytick.labelsize'] = axes_tick_fontsize
    if legend_fontsize:
        plt.rcParams['legend.fontsize'] = legend_fontsize

    if plot_3d:
        fig, ax = _plot_3d_trajectories(T_list, title, labels, plot_rot,
                                        sample_rate, linewidth, line_styles, colors,
                                        title_fontsize, view_3d)

        ax.set_xlabel(ax.get_xlabel(), labelpad=labelpad_scale * axes_label_fontsize)  # type: ignore
        ax.set_ylabel(ax.get_ylabel(), labelpad=labelpad_scale * axes_label_fontsize)  # type: ignore
        ax.set_zlabel(ax.get_zlabel(), labelpad=labelpad_scale * axes_label_fontsize)  # type: ignore

        if not grid_enabled:
            ax.grid(False)
    else:
        fig, ax = _plot_2d_trajectories(T_list, title, labels, plot_rot,
                                        sample_rate, linewidth, line_styles, colors,
                                        title_fontsize)

        for axis in ax.flat:  # type: ignore
            axis.set_xlabel(axis.get_xlabel(), labelpad=labelpad_scale * axes_label_fontsize * 0.7)  # type: ignore
            axis.set_ylabel(axis.get_ylabel(), labelpad=labelpad_scale * axes_label_fontsize * 0.7)  # type: ignore

    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=600, bbox_inches='tight')
        logger.info(f"Saved plot to: {save_path}")

    return fig, ax


def _plot_3d_trajectories(T_list, title, labels, plot_rot,
                          sample_rate, linewidth, line_styles, colors,
                          title_fontsize=None, view_3d=None) -> Tuple[Figure, Axes]:
    """
    Helper for 3D trajectory plotting.

    Args:
        T_list: List of transformation arrays, each shape (N, 4, 4)
        title: Plot title
        labels: Labels for each trajectory
        plot_rot: If True, include rotation visualization
        sample_rate: Sampling rate for plotting (1 = every frame)
        linewidth: Line width for plots
        line_styles: List of line styles for different trajectories
        colors: List of colors for different trajectories
        title_fontsize: Font size for title
        view_3d: Dict with view parameters

    Returns:
        matplotlib.figure.Figure: The created figure. Does not show or close the figure.
    """
    fig = plt.figure(figsize=plt.rcParams['figure.figsize'])
    ax = fig.add_subplot(111, projection='3d')

    # Set initial view with config values or defaults
    if view_3d is None:
        view_3d = {}

    ax.view_init(  # type: ignore
        elev=view_3d.get('elev', 30),
        azim=view_3d.get('azim', 0),
        roll=view_3d.get('roll', 0),
        vertical_axis=view_3d.get('vertical_axis', 'y')
    )

    # Enable better 3D rotation
    # enable_better_3d_rotation(ax)

    # Compute scaling for rotation vectors
    all_positions = np.vstack([T[:, :3, 3] for T in T_list])
    max_range = np.ptp(all_positions, axis=0).max()
    vector_scale = max_range * 0.05

    for i, T in enumerate(T_list):
        label = labels[i] if labels else f'Trajectory {i + 1}'
        T_sampled = T[::sample_rate]
        positions = T_sampled[:, :3, 3]

        # Plot trajectory
        ax.plot(positions[:, 0], positions[:, 1], positions[:, 2],
                label=label, color=colors[i],
                linestyle=line_styles[i % len(line_styles)],
                linewidth=linewidth)

        # Plot rotation frames if requested
        if plot_rot:
            step = max(1, len(T_sampled) // 20)
            for j in range(0, len(T_sampled), step):
                pos = positions[j]
                rot = T_sampled[j, :3, :3]

                # Plot coordinate axes
                for k, color in enumerate(['r', 'g', 'b']):
                    axis = rot[:, k] * vector_scale
                    ax.quiver(pos[0], pos[1], pos[2],
                              axis[0], axis[1], axis[2],
                              color=color, alpha=0.5)

    ax.set_xlabel('X [mm]')
    ax.set_ylabel('Y [mm]')
    ax.set_zlabel('Z [mm]')  # type: ignore
    ax.set_title(title, fontsize=title_fontsize)
    ax.legend()

    # Equal aspect ratio
    _set_axes_equal(ax)
    return fig, ax


def _plot_2d_trajectories(T_list, title, labels, plot_rot,
                          sample_rate, linewidth, line_styles, colors,
                          title_fontsize=None) -> Tuple[Figure, Axes]:
    """
    Helper for 2D component plotting.

    Args:
        T_list: List of transformation arrays, each shape (N, 4, 4)
        title: Plot title
        labels: Labels for each trajectory
        plot_rot: If True, include rotation visualization
        sample_rate: Sampling rate for plotting (1 = every frame)
        linewidth: Line width for plots
        line_styles: List of line styles for different trajectories
        colors: List of colors for different trajectories
        title_fontsize: Font size for title

    Returns:
        matplotlib.figure.Figure: The created figure. Does not show or close the figure.
        matplotlib.axes.Axes: The axes object containing the plots.
    """
    num_traj = len(T_list)
    num_cols = 6 if plot_rot else 3

    fig, axes = plt.subplots(num_traj, num_cols,
                             figsize=(3 * num_cols, 3 * num_traj))
    fig.suptitle(title, fontsize=title_fontsize if title_fontsize else 14)

    if num_traj == 1:
        axes = axes.reshape(1, -1)

    for i, T in enumerate(T_list):
        label = labels[i] if labels else f'Trajectory {i + 1}'
        T_sampled = T[::sample_rate]
        positions = T_sampled[:, :3, 3]
        frames = np.arange(len(T_sampled)) * sample_rate

        # Plot position components
        for j, (comp, comp_label) in enumerate([('X', 'X'), ('Y', 'Y'), ('Z', 'Z')]):
            axes[i, j].plot(frames, positions[:, j],
                            color=colors[i],
                            linestyle=line_styles[i % len(line_styles)],
                            linewidth=linewidth)
            axes[i, j].set_title(f'{label} - Position {comp_label}')
            axes[i, j].set_xlabel('Frame')
            axes[i, j].set_ylabel(f'{comp_label} [mm]')

        # Plot rotation components if requested
        if plot_rot:
            euler_angles = np.array([
                R.from_matrix(T_sampled[k, :3, :3]).as_euler('xyz', degrees=True)
                for k in range(len(T_sampled))
            ])

            for j, (angle, angle_label) in enumerate([('Roll', 'Roll'),
                                                      ('Pitch', 'Pitch'),
                                                      ('Yaw', 'Yaw')]):
                axes[i, j + 3].plot(frames, euler_angles[:, j],
                                    color=colors[i],
                                    linestyle=line_styles[i % len(line_styles)],
                                    linewidth=linewidth)
                axes[i, j + 3].set_title(f'{label} - {angle_label}')
                axes[i, j + 3].set_xlabel('Frame')
                axes[i, j + 3].set_ylabel(f'{angle_label} [°]')

    return fig, axes


def _set_axes_equal(ax):
    """Set equal aspect ratio for 3D axes."""
    limits = np.array([ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()])
    centers = np.mean(limits, axis=1)
    radius = 0.5 * np.max(np.abs(limits[:, 1] - limits[:, 0]))

    for i, center in enumerate(centers):
        getattr(ax, f'set_{"xyz"[i]}lim3d')(center - radius, center + radius)


# File I/O utilities

def save_transformation_to_csv(transform_matrices: np.ndarray,
                               csv_file: Union[str, Path]) -> None:
    """
    Save transformation matrices to CSV file.

    Format: [tx, ty, tz, qw, qx, qy, qz] per row

    Args:
        transform_matrices: Array of shape (N, 4, 4)
        csv_file: Output file path
    """
    if transform_matrices.ndim != 3 or transform_matrices.shape[1:] != (4, 4):
        raise ValueError("Input must have shape (N, 4, 4)")

    csv_file = Path(csv_file)
    csv_file.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)

        for T in transform_matrices:
            # Extract translation and rotation
            translation = T[:3, 3]
            rotation_matrix = T[:3, :3]

            # Convert to quaternion (scalar-first)
            quaternion = R.from_matrix(rotation_matrix).as_quat(scalar_first=True)

            # Write row
            writer.writerow([*translation, *quaternion])

    logger.info(f"Saved {len(transform_matrices)} transformations to: {csv_file}")


def load_csv_to_transformations(file_path: Union[str, Path],
                                delimiter: str = ",") -> np.ndarray:
    """
    Load transformations from CSV file.

    Expected format: [tx, ty, tz, qw, qx, qy, qz] per row

    Args:
        file_path: Input file path
        delimiter: CSV delimiter

    Returns:
        Array of shape (N, 4, 4) transformation matrices
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    data = np.loadtxt(file_path, delimiter=delimiter)

    if data.shape[1] != 7:
        raise ValueError(f"Expected 7 columns, got {data.shape[1]}")

    # Extract components
    translations = data[:, :3]
    quaternions = data[:, 3:]  # [qw, qx, qy, qz]

    # Convert quaternions to rotation matrices
    # scipy expects [qx, qy, qz, qw] order
    rotation_matrices = R.from_quat(quaternions[:, [1, 2, 3, 0]]).as_matrix()

    # Build transformation matrices
    N = len(data)
    transformations = np.zeros((N, 4, 4))
    transformations[:, :3, :3] = rotation_matrices
    transformations[:, :3, 3] = translations
    transformations[:, 3, 3] = 1.0

    logger.info(f"Loaded {N} transformations from: {file_path}")
    return transformations


def store_transformations(T_t_list: List[np.ndarray],
                          sample_rates: List[float],
                          filename: Union[str, Path],
                          metadata: Optional[List[str]] = None,
                          store_as_quaternion: bool = True,
                          derivative_order: int = 0,
                          scale_factor: float = 1.0,
                          unit: str = 'mm',
                          group_names: Optional[List[str]] = None) -> None:
    """
    Store transformation matrices to HDF5 file.

    Args:
        T_t_list: List of transformation arrays, each shape (N, 4, 4)
        sample_rates: Sample rates for each array
        filename: Output HDF5 file path
        metadata: Optional metadata strings for each array
        store_as_quaternion: If True, store rotations as quaternions
        derivative_order: Order of derivatives to compute and store
        scale_factor: Scale factor for translations (e.g., 0.001 for mm to m)
        unit: Unit of translations (default: 'mm')
        group_names: Optional list of group names for each transformation set
    """
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)

    if metadata is not None and len(metadata) != len(T_t_list):
        raise ValueError("Metadata list length must match transformation list length")
    if group_names is not None and len(group_names) != len(T_t_list):
        raise ValueError("group_names list length must match transformation list length")

    with h5py.File(filename, 'w') as f:
        for i, (T_t, sample_rate) in enumerate(zip(T_t_list, sample_rates)):
            group_name = group_names[i] if group_names else f"T_{i}"
            _store_single_transformation(
                f, group_name, T_t, sample_rate, unit,
                metadata[i] if metadata else None,
                store_as_quaternion, derivative_order, scale_factor
            )

    logger.info(f"Stored {len(T_t_list)} transformation sets to: {filename}")


def _store_single_transformation(f: h5py.File,
                                 group_name: str,
                                 T_t: np.ndarray,
                                 sample_rate: float,
                                 unit: str,
                                 metadata: Optional[str],
                                 store_as_quaternion: bool,
                                 derivative_order: int,
                                 scale_factor: float) -> None:
    """Store a single transformation array to HDF5 group."""
    if T_t.ndim != 3 or T_t.shape[1:] != (4, 4):
        raise ValueError(f"Transformation array {group_name} must have shape (N, 4, 4)")

    # Create group
    group = f.create_group(group_name)

    # Store metadata and sample rate
    if metadata:
        group.attrs['metadata'] = metadata
    group.attrs['sample_rate'] = float(sample_rate)
    group.attrs['unit'] = unit if unit else 'mm'

    # Extract and scale translations
    translations = T_t[:, :3, 3] * scale_factor

    # Store translations
    group.create_dataset('translations', data=translations)

    # Store rotations
    if store_as_quaternion:
        quaternions = np.array([
            R.from_matrix(T_t[j, :3, :3]).as_quat(scalar_first=True)
            for j in range(len(T_t))
        ])
        group.create_dataset('rotations', data=quaternions)
    else:
        group.create_dataset('rotations', data=T_t[:, :3, :3])

    # Compute and store derivatives if requested
    if derivative_order > 0:
        _store_derivatives(group, T_t, store_as_quaternion, derivative_order)


def _store_derivatives(group: h5py.Group, T_t: np.ndarray,
                       rot_as_quaternion: bool, derivative_order: int) -> None:
    """Compute and store transformation derivatives."""
    trans_derivs, rot_derivs = compute_derivatives(
        T_t, rot_as_quaternion, derivative_order
    )

    for order in range(1, derivative_order + 1):
        group.create_dataset(
            f'translational_derivative_order_{order}',
            data=trans_derivs[order - 1]
        )
        group.create_dataset(
            f'rotational_derivative_order_{order}',
            data=rot_derivs[order - 1]
        )


def compute_derivatives(T_t: np.ndarray, rot_as_quaternion: bool = True,
                        derivative_order: int = 1) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    Compute derivatives of transformation matrices.

    Args:
        T_t: Array of shape (N, 4, 4) transformations
        rot_as_quaternion: If True, compute rotational derivatives as quaternions
        derivative_order: Maximum derivative order to compute

    Returns:
        Tuple of (translational_derivatives, rotational_derivatives)
    """
    if T_t.ndim != 3 or T_t.shape[1:] != (4, 4):
        raise ValueError("Input must have shape (N, 4, 4)")

    # Extract components
    translations = T_t[:, :3, 3]
    rotations = T_t[:, :3, :3]

    # Convert rotations if needed
    if rot_as_quaternion:
        rotations = R.from_matrix(rotations).as_quat(scalar_first=True)

    # Compute derivatives
    trans_derivs = []
    rot_derivs = []

    current_trans = translations
    current_rot = rotations

    for order in range(derivative_order):
        current_trans = np.gradient(current_trans, axis=0)
        current_rot = np.gradient(current_rot, axis=0)

        trans_derivs.append(current_trans)
        rot_derivs.append(current_rot)

    return trans_derivs, rot_derivs


# Additional utility functions

def rotation_matrix_to_euler_angles(R_mat: np.ndarray, degrees: bool = True) -> Tuple[float, float, float]:
    """
    Convert rotation matrix to Euler angles.

    Args:
        R_mat: 3x3 rotation matrix
        degrees: If True, return angles in degrees

    Returns:
        Tuple of (roll, pitch, yaw) angles
    """
    if R_mat.shape != (3, 3):
        raise ValueError("Input must be 3x3 matrix")

    r = R.from_matrix(R_mat)
    angles = r.as_euler('xyz', degrees=degrees)

    return tuple(angles)


def relative_rotation(q1: np.ndarray, q2: np.ndarray,
                      output_format: str = "euler",
                      scalar_first: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute relative rotation between two quaternions.

    Args:
        q1: First quaternion
        q2: Second quaternion
        output_format: "euler" or "rotvec"
        scalar_first: If True, quaternions are [w, x, y, z]

    Returns:
        Tuple of (relative_quaternion, relative_angles)
    """
    # Normalize quaternions
    q1 = q1 / np.linalg.norm(q1)
    q2 = q2 / np.linalg.norm(q2)

    # Convert to scipy format if needed
    if scalar_first:
        q1 = np.roll(q1, -1)  # [w, x, y, z] -> [x, y, z, w]
        q2 = np.roll(q2, -1)

    # Compute relative rotation: q_rel = q2 * inv(q1)
    r1 = R.from_quat(q1)
    r2 = R.from_quat(q2)
    r_rel = r2 * r1.inv()

    # Get output
    q_rel = r_rel.as_quat(scalar_first=scalar_first)

    if output_format == "euler":
        angles = r_rel.as_euler('xyz', degrees=True)
    elif output_format == "rotvec":
        angles = r_rel.as_rotvec()
    else:
        raise ValueError("output_format must be 'euler' or 'rotvec'")

    return q_rel, angles
