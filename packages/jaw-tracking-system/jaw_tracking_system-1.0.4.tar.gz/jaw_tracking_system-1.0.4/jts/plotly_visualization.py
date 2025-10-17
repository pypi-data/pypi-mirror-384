#!/usr/bin/env python3

"""
plotly_visualization.py: Interactive 3D visualization of jaw motion data using Plotly.

This module provides interactive visualization capabilities for HDF5 files exported
by the jaw motion analysis framework. It uses Plotly for full 3D rotation control
and offers various export options including static images and HTML.

For LaTeX integration, the module can export to:
    - Static images (PNG, SVG, PDF) that can be included in LaTeX
    - HTML files that can be converted to PDF
    - Plotly's native JSON format for reproducibility
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

import os
import h5py
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.spatial.transform import Rotation as R

# Import the helper module for logger setup
from . import helper as hlp

# Suppress GTK warnings
os.environ['GTK_MODULES'] = ''

# Set up logger
logger = hlp.setup_logger(__name__)


class JawMotionVisualizer:
    """
    Interactive 3D visualization of jaw motion trajectories using Plotly.

    This class loads transformation data from HDF5 files and creates
    interactive 3D plots with full rotation control.
    """

    def __init__(self, hdf5_path: Union[str, Path]):
        """
        Initialize the visualizer with an HDF5 file.

        Args:
            hdf5_path: Path to the HDF5 file containing transformation data
        """
        self.hdf5_path = Path(hdf5_path)
        if not self.hdf5_path.exists():
            raise FileNotFoundError(f"HDF5 file not found: {self.hdf5_path}")

        self.data = {}
        self.metadata = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load transformation data from HDF5 file."""
        logger.info(f"Loading data from {self.hdf5_path}")

        with h5py.File(self.hdf5_path, 'r') as f:
            for group_name in f.keys():
                group = f[group_name]

                # Load translations
                translations = group['translations'][:]  # type: ignore

                # Load rotations (quaternions or matrices)
                rotations_data = group['rotations'][:]  # type: ignore
                if rotations_data.shape[1] == 4:  # Quaternions  # type: ignore
                    # Convert to rotation matrices for visualization
                    rotations = np.array([
                        R.from_quat(q[[1, 2, 3, 0]]).as_matrix()  # Convert from scalar-first
                        for q in rotations_data  # type: ignore
                    ])
                else:  # Already rotation matrices
                    rotations = rotations_data

                # Store data
                self.data[group_name] = {
                    'translations': translations,
                    'rotations': rotations,
                    'sample_rate': group.attrs.get('sample_rate', 1.0),
                    'unit': group.attrs.get('unit', 'mm')
                }

                # Store metadata
                self.metadata[group_name] = group.attrs.get('metadata', '')

                logger.info(f"Loaded {group_name}: {len(translations)} frames")  # type: ignore

    def get_available_groups(self) -> List[str]:
        """Get list of available trajectory groups in the HDF5 file."""
        return list(self.data.keys())

    def plot_trajectory_3d(self,
                           trajectory_names: Optional[List[str]] = None,
                           show_frames: bool = True,
                           frame_step: int = 100,
                           frame_scale: float = 0.05,
                           title: str = "Jaw Motion Trajectory",
                           show_grid: bool = True,
                           background_color: str = 'white',
                           save_html: Optional[str] = None) -> go.Figure:
        """
        Create an interactive 3D plot of trajectories.

        Args:
            trajectory_names: List of trajectory names to plot (None = all)
            show_frames: Whether to show coordinate frames along trajectory
            frame_step: Step size for showing coordinate frames (e.g., 100 = every 100th frame)
            frame_scale: Scale factor for coordinate frame arrows
            title: Plot title
            show_grid: Whether to show grid
            background_color: Background color
            save_html: Path to save interactive HTML file

        Returns:
            Plotly Figure object
        """
        if trajectory_names is None:
            trajectory_names = list(self.data.keys())

        fig = go.Figure()

        # Color palette
        colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown']

        # Calculate scale for frames based on trajectory extent
        all_positions = []
        for name in trajectory_names:
            if name in self.data:
                all_positions.append(self.data[name]['translations'])

        if all_positions:
            all_positions = np.vstack(all_positions)
            trajectory_extent = np.ptp(all_positions, axis=0).max()
            arrow_length = trajectory_extent * frame_scale
        else:
            arrow_length = 10.0

        # Plot each trajectory
        for idx, name in enumerate(trajectory_names):
            if name not in self.data:
                logger.warning(f"Trajectory '{name}' not found in data")
                continue

            color = colors[idx % len(colors)]
            translations = self.data[name]['translations']
            rotations = self.data[name]['rotations']

            # Main trajectory line
            fig.add_trace(go.Scatter3d(
                x=translations[:, 0],
                y=translations[:, 1],
                z=translations[:, 2],
                mode='lines',
                name=name,
                line=dict(
                    color=color,
                    width=4
                ),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                              'X: %{x:.2f}<br>' +
                              'Y: %{y:.2f}<br>' +
                              'Z: %{z:.2f}<br>' +
                              '<extra></extra>'
            ))

            # Add start and end markers
            fig.add_trace(go.Scatter3d(
                x=[translations[0, 0]],
                y=[translations[0, 1]],
                z=[translations[0, 2]],
                mode='markers',
                name=f'{name} (start)',
                marker=dict(
                    color='green',
                    size=8,
                    symbol='circle'
                ),
                showlegend=False
            ))

            fig.add_trace(go.Scatter3d(
                x=[translations[-1, 0]],
                y=[translations[-1, 1]],
                z=[translations[-1, 2]],
                mode='markers',
                name=f'{name} (end)',
                marker=dict(
                    color='red',
                    size=8,
                    symbol='circle'
                ),
                showlegend=False
            ))

            # Add coordinate frames only if requested
            if show_frames and frame_step > 0:
                frame_indices = range(0, len(translations), frame_step)
                axis_colors = ['red', 'green', 'blue']  # X, Y, Z
                axis_names = ['X', 'Y', 'Z']

                logger.info(f"Plotting coordinate frames for {name}: {len(list(frame_indices))} frames "
                            f"(every {frame_step} frames)")

                for frame_idx in frame_indices:
                    pos = translations[frame_idx]
                    rot = rotations[frame_idx]

                    # Draw coordinate axes
                    for axis_idx, (axis_color, axis_name) in enumerate(zip(axis_colors, axis_names)):
                        axis_vec = rot[:, axis_idx] * arrow_length

                        # Create arrow using cone
                        fig.add_trace(go.Scatter3d(
                            x=[pos[0], pos[0] + axis_vec[0]],
                            y=[pos[1], pos[1] + axis_vec[1]],
                            z=[pos[2], pos[2] + axis_vec[2]],
                            mode='lines',
                            line=dict(color=axis_color, width=2),
                            showlegend=False,
                            hoverinfo='skip'
                        ))

                        # Add cone for arrow head
                        fig.add_trace(go.Cone(
                            x=[pos[0] + axis_vec[0]],
                            y=[pos[1] + axis_vec[1]],
                            z=[pos[2] + axis_vec[2]],
                            u=[axis_vec[0] * 0.2],
                            v=[axis_vec[1] * 0.2],
                            w=[axis_vec[2] * 0.2],
                            sizemode='absolute',
                            sizeref=arrow_length * 0.1,
                            showscale=False,
                            colorscale=[[0, axis_color], [1, axis_color]],
                            showlegend=False,
                            hoverinfo='skip'
                        ))

        # Update layout
        unit = self.data[trajectory_names[0]]['unit'] if trajectory_names else 'mm'

        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=20)
            ),
            scene=dict(
                xaxis=dict(
                    title=f'X [{unit}]',
                    gridcolor='gray' if show_grid else 'rgba(0,0,0,0)',
                    showbackground=True,
                    backgroundcolor=background_color
                ),
                yaxis=dict(
                    title=f'Y [{unit}]',
                    gridcolor='gray' if show_grid else 'rgba(0,0,0,0)',
                    showbackground=True,
                    backgroundcolor=background_color
                ),
                zaxis=dict(
                    title=f'Z [{unit}]',
                    gridcolor='gray' if show_grid else 'rgba(0,0,0,0)',
                    showbackground=True,
                    backgroundcolor=background_color
                ),
                aspectmode='data',  # Equal aspect ratio
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            margin=dict(l=0, r=0, b=0, t=50)
        )

        # Save HTML if requested
        if save_html:
            fig.write_html(save_html)
            logger.info(f"Saved interactive HTML to: {save_html}")

        return fig

    def plot_components_2d(self,
                           trajectory_names: Optional[List[str]] = None,
                           components: List[str] = ['translation', 'rotation'],
                           title: str = "Trajectory Components") -> go.Figure:
        """
        Create 2D plots of trajectory components over time.

        Args:
            trajectory_names: List of trajectory names to plot (None = all)
            components: List of components to plot ('translation', 'rotation')
            title: Plot title

        Returns:
            Plotly Figure object
        """
        if trajectory_names is None:
            trajectory_names = list(self.data.keys())

        # Determine subplot layout
        n_components = 0
        if 'translation' in components:
            n_components += 3  # X, Y, Z
        if 'rotation' in components:
            n_components += 3  # Roll, Pitch, Yaw

        fig = make_subplots(
            rows=n_components,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=self._get_subplot_titles(components)
        )

        colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown']

        for idx, name in enumerate(trajectory_names):
            if name not in self.data:
                continue

            color = colors[idx % len(colors)]
            data = self.data[name]
            sample_rate = data['sample_rate']
            n_frames = len(data['translations'])
            time = np.arange(n_frames) / sample_rate

            row = 1

            # Plot translation components
            if 'translation' in components:
                for i, axis in enumerate(['X', 'Y', 'Z']):
                    fig.add_trace(
                        go.Scatter(
                            x=time,
                            y=data['translations'][:, i],
                            mode='lines',
                            name=f'{name}' if row == 1 else None,
                            line=dict(color=color, width=2),
                            showlegend=(row == 1),
                            legendgroup=name
                        ),
                        row=row, col=1
                    )
                    row += 1

            # Plot rotation components
            if 'rotation' in components:
                # Convert to Euler angles
                euler_angles = np.array([
                    R.from_matrix(data['rotations'][i]).as_euler('xyz', degrees=True)
                    for i in range(n_frames)
                ])

                for i, axis in enumerate(['Roll', 'Pitch', 'Yaw']):
                    fig.add_trace(
                        go.Scatter(
                            x=time,
                            y=euler_angles[:, i],
                            mode='lines',
                            name=f'{name}' if row == 4 and 'translation' not in components else None,
                            line=dict(color=color, width=2),
                            showlegend=(row == 4 and 'translation' not in components),
                            legendgroup=name
                        ),
                        row=row, col=1
                    )
                    row += 1

        # Update axes
        unit = self.data[trajectory_names[0]]['unit'] if trajectory_names else 'mm'
        fig.update_xaxes(title_text="Time [s]", row=n_components, col=1)

        row = 1
        if 'translation' in components:
            for axis in ['X', 'Y', 'Z']:
                fig.update_yaxes(title_text=f"{axis} [{unit}]", row=row, col=1)
                row += 1

        if 'rotation' in components:
            for axis in ['Roll', 'Pitch', 'Yaw']:
                fig.update_yaxes(title_text=f"{axis} [°]", row=row, col=1)
                row += 1

        fig.update_layout(
            title=title,
            height=200 * n_components,
            showlegend=True
        )

        return fig

    def _get_subplot_titles(self, components: List[str]) -> List[str]:
        """Generate subplot titles based on components."""
        titles = []
        if 'translation' in components:
            titles.extend(['Translation X', 'Translation Y', 'Translation Z'])
        if 'rotation' in components:
            titles.extend(['Roll', 'Pitch', 'Yaw'])
        return titles

    def animate_trajectory(self,
                           trajectory_name: str,
                           fps: int = 30,
                           trail_length: int = 50,
                           show_frames: bool = True) -> go.Figure:
        """
        Create an animated 3D visualization of a trajectory.

        Args:
            trajectory_name: Name of trajectory to animate
            fps: Frames per second for animation
            trail_length: Number of previous positions to show as trail
            show_frames: Whether to show coordinate frame

        Returns:
            Animated Plotly Figure
        """
        if trajectory_name not in self.data:
            raise ValueError(f"Trajectory '{trajectory_name}' not found")

        data = self.data[trajectory_name]
        translations = data['translations']
        rotations = data['rotations']

        # Create frames for animation
        frames = []

        for i in range(len(translations)):
            frame_data = []

            # Trail
            trail_start = max(0, i - trail_length)
            trail_positions = translations[trail_start:i + 1]

            if len(trail_positions) > 0:
                frame_data.append(
                    go.Scatter3d(
                        x=trail_positions[:, 0],
                        y=trail_positions[:, 1],
                        z=trail_positions[:, 2],
                        mode='lines',
                        line=dict(color='blue', width=3),
                        showlegend=False
                    )
                )

            # Current position
            frame_data.append(
                go.Scatter3d(
                    x=[translations[i, 0]],
                    y=[translations[i, 1]],
                    z=[translations[i, 2]],
                    mode='markers',
                    marker=dict(color='red', size=8),
                    showlegend=False
                )
            )

            # Coordinate frame
            if show_frames:
                pos = translations[i]
                rot = rotations[i]
                arrow_length = 20  # Adjust as needed

                for axis_idx, color in enumerate(['red', 'green', 'blue']):
                    axis_vec = rot[:, axis_idx] * arrow_length
                    frame_data.append(
                        go.Scatter3d(
                            x=[pos[0], pos[0] + axis_vec[0]],
                            y=[pos[1], pos[1] + axis_vec[1]],
                            z=[pos[2], pos[2] + axis_vec[2]],
                            mode='lines',
                            line=dict(color=color, width=4),
                            showlegend=False
                        )
                    )

            frames.append(go.Frame(data=frame_data, name=str(i)))

        # Initial figure
        fig = go.Figure(
            data=frames[0].data,
            frames=frames
        )

        # Animation settings
        fig.update_layout(
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'buttons': [
                    {
                        'label': 'Play',
                        'method': 'animate',
                        'args': [None, {
                            'frame': {'duration': 1000 / fps, 'redraw': True},
                            'fromcurrent': True,
                            'transition': {'duration': 0}
                        }]
                    },
                    {
                        'label': 'Pause',
                        'method': 'animate',
                        'args': [[None], {
                            'frame': {'duration': 0, 'redraw': False},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }]
                    }
                ]
            }],
            sliders=[{
                'active': 0,
                'steps': [
                    {
                        'args': [[f.name], {  # type: ignore
                            'frame': {'duration': 0, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }],
                        'label': str(i),
                        'method': 'animate'
                    }
                    for i, f in enumerate(fig.frames)  # type: ignore
                ]
            }]
        )

        # Set scene properties
        unit = data['unit']
        fig.update_layout(
            title=f"Animated Trajectory: {trajectory_name}",
            scene=dict(
                xaxis=dict(title=f'X [{unit}]'),
                yaxis=dict(title=f'Y [{unit}]'),
                zaxis=dict(title=f'Z [{unit}]'),
                aspectmode='data'
            )
        )

        return fig

    def export_for_latex(self,
                         fig: go.Figure,
                         output_path: Union[str, Path],
                         format: str = 'pdf',
                         width: int = 800,
                         height: int = 600,
                         scale: float = 2.0) -> None:
        """
        Export Plotly figure for LaTeX inclusion.

        Args:
            fig: Plotly figure to export
            output_path: Output file path
            format: Export format ('pdf', 'svg', 'png', 'eps')
            width: Image width in pixels
            height: Image height in pixels
            scale: Scale factor for high DPI
        """
        output_path = Path(output_path)

        # Ensure kaleido is installed for static export
        try:
            import kaleido  # type: ignore  # noqa: F401
        except ImportError:
            logger.error("kaleido package is required for static export. Install with: pip install kaleido")
            raise

        # Export based on format
        if format == 'pdf':
            fig.write_image(output_path, format='pdf', width=width, height=height, scale=scale)
        elif format == 'svg':
            fig.write_image(output_path, format='svg', width=width, height=height, scale=scale)
        elif format == 'png':
            fig.write_image(output_path, format='png', width=width, height=height, scale=scale)
        elif format == 'eps':
            # EPS requires special handling
            fig.write_image(output_path, format='eps', width=width, height=height, scale=scale)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Exported figure to: {output_path}")

        # Also save as JSON for reproducibility
        json_path = output_path.with_suffix('.json')
        fig.write_json(json_path)
        logger.info(f"Saved figure JSON to: {json_path}")

    def create_latex_figure(self,
                            image_path: Union[str, Path],
                            caption: str,
                            label: str,
                            width: str = "0.8\\textwidth") -> str:
        """
        Generate LaTeX code for including the exported figure.

        Args:
            image_path: Path to the exported image
            caption: Figure caption
            label: LaTeX label for referencing
            width: Figure width in LaTeX units

        Returns:
            LaTeX code as string
        """
        image_path = Path(image_path)

        latex_code = f"""
\\begin{{figure}}[htbp]
    \\centering
    \\includegraphics[width={width}]{{{image_path.stem}}}
    \\caption{{{caption}}}
    \\label{{{label}}}
\\end{{figure}}
"""

        # Save LaTeX snippet
        tex_path = image_path.with_suffix('.tex')
        with open(tex_path, 'w') as f:
            f.write(latex_code)

        logger.info(f"Saved LaTeX snippet to: {tex_path}")

        return latex_code


def visualize_hdf5_file(hdf5_path: Union[str, Path],
                        output_dir: Optional[Union[str, Path]] = None,
                        show_interactive: bool = True,
                        export_formats: List[str] = ['pdf', 'png'],
                        components_to_plot: List[str] = ['translation', 'rotation'],
                        groups_to_plot: Optional[List[str]] = None,
                        show_frames: bool = True,
                        frame_step: int = 100,
                        create_animation: bool = False,
                        animation_group: Optional[str] = None) -> Dict[str, go.Figure]:
    """
    Convenience function to visualize all trajectories in an HDF5 file.

    Args:
        hdf5_path: Path to HDF5 file
        output_dir: Directory for saving outputs (creates if not exists)
        show_interactive: Whether to show interactive plots
        export_formats: List of formats to export ('pdf', 'svg', 'png', 'eps')
        components_to_plot: Components to plot in 2D view
        groups_to_plot: Specific groups to plot (None = all available)
        show_frames: Whether to show coordinate frames in 3D plot
        frame_step: Step interval for plotting coordinate frames
        create_animation: Whether to create an animated visualization
        animation_group: Specific group to animate (default: first available)

    Returns:
        Dictionary of created figures
    """
    # Create visualizer
    viz = JawMotionVisualizer(hdf5_path)

    # Show available groups
    available_groups = viz.get_available_groups()
    logger.info(f"Available groups: {available_groups}")

    # Select groups to plot
    if groups_to_plot:
        # Validate requested groups
        invalid_groups = [g for g in groups_to_plot if g not in available_groups]
        if invalid_groups:
            logger.warning(f"Groups not found: {invalid_groups}")
        trajectory_names = [g for g in groups_to_plot if g in available_groups]
        if not trajectory_names:
            logger.error("No valid groups specified")
            return {}
    else:
        trajectory_names = None  # Will use all available

    # Create output directory if specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    figures = {}

    # Create 3D trajectory plot
    fig_3d = viz.plot_trajectory_3d(
        trajectory_names=trajectory_names,
        show_frames=show_frames,
        frame_step=frame_step,
        title="Jaw Motion Trajectories - 3D View"
    )
    figures['3d_trajectory'] = fig_3d

    if show_interactive:
        try:
            fig_3d.show()
        except Exception as e:
            logger.warning(f"Could not open browser automatically: {e}")
            # Save to file as fallback
            fallback_path = output_dir / "jaw_motion_plot.html" if output_dir else Path("jaw_motion_plot.html")
            fig_3d.write_html(fallback_path)
            logger.info(f"Saved plot to: {fallback_path}")
            logger.info("Open this file manually in your browser")

    # Create 2D component plots
    fig_2d = viz.plot_components_2d(
        trajectory_names=trajectory_names,
        components=components_to_plot,
        title="Jaw Motion Components Over Time"
    )
    figures['2d_components'] = fig_2d

    if show_interactive:
        fig_2d.show()

    # Get base name for file outputs
    base_name = hdf5_path.stem if isinstance(hdf5_path, Path) else Path(hdf5_path).stem

    # Export if output directory specified
    if output_dir:

        # Export 3D plot
        for fmt in export_formats:
            viz.export_for_latex(
                fig_3d,
                output_dir / f"{base_name}_3d.{fmt}",
                format=fmt
            )

        # Export 2D plot
        for fmt in export_formats:
            viz.export_for_latex(
                fig_2d,
                output_dir / f"{base_name}_2d.{fmt}",
                format=fmt,
                height=800  # Taller for multiple subplots
            )

        # Save interactive HTML versions
        fig_3d.write_html(output_dir / f"{base_name}_3d_interactive.html")
        fig_2d.write_html(output_dir / f"{base_name}_2d_interactive.html")

        # Generate LaTeX snippets
        latex_3d = viz.create_latex_figure(
            output_dir / f"{base_name}_3d.pdf",
            "3D visualization of jaw motion trajectories with coordinate frames",
            f"fig:{base_name}_3d"
        )

        latex_2d = viz.create_latex_figure(
            output_dir / f"{base_name}_2d.pdf",
            "Temporal evolution of jaw motion components",
            f"fig:{base_name}_2d"
        )

        # Save combined LaTeX file
        with open(output_dir / f"{base_name}_figures.tex", 'w') as f:
            f.write("% Include these figures in your LaTeX document\n\n")
            f.write(latex_3d)
            f.write("\n")
            f.write(latex_2d)

        # Add animation creation after 2D plots
    if create_animation:
        # Select group to animate
        if animation_group and animation_group in available_groups:
            anim_group = animation_group
        else:
            # Use first available group or first from groups_to_plot
            anim_group = (trajectory_names[0] if trajectory_names
                          else available_groups[0])

        logger.info(f"Creating animation for group: {anim_group}")

        fig_anim = viz.animate_trajectory(
            anim_group,
            fps=30,
            trail_length=50,
            show_frames=show_frames
        )
        figures['animation'] = fig_anim

        if show_interactive:
            fig_anim.show()

        if output_dir:
            anim_path = output_dir / f"{base_name}_{anim_group}_animation.html"
            fig_anim.write_html(anim_path)
            logger.info(f"Saved animation to: {anim_path}")

    return figures


def compare_trajectories(hdf5_files: List[Union[str, Path]],
                         labels: Optional[List[str]] = None,
                         output_path: Optional[Union[str, Path]] = None,
                         show_frames: bool = False,
                         frame_step: int = 100) -> go.Figure:
    """
    Compare trajectories from multiple HDF5 files in a single plot.

    Args:
        hdf5_files: List of HDF5 file paths
        labels: Optional labels for each file
        output_path: Optional path to save comparison plot
        show_frames: Whether to show coordinate frames
        frame_step: Step interval for plotting coordinate frames

    Returns:
        Plotly figure with all trajectories
    """
    if labels is None:
        labels = [Path(f).stem for f in hdf5_files]

    fig = go.Figure()
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown']

    for idx, (hdf5_path, label) in enumerate(zip(hdf5_files, labels)):
        viz = JawMotionVisualizer(hdf5_path)
        color = colors[idx % len(colors)]

        # Plot first trajectory from each file
        traj_name = list(viz.data.keys())[0]
        translations = viz.data[traj_name]['translations']

        fig.add_trace(go.Scatter3d(
            x=translations[:, 0],
            y=translations[:, 1],
            z=translations[:, 2],
            mode='lines',
            name=label,
            line=dict(color=color, width=4)
        ))

    # Update layout
    fig.update_layout(
        title="Trajectory Comparison",
        scene=dict(
            xaxis_title="X [mm]",
            yaxis_title="Y [mm]",
            zaxis_title="Z [mm]",
            aspectmode='data'
        ),
        showlegend=True
    )

    if output_path:
        fig.write_html(output_path)

    return fig


def create_trajectory_animation(hdf5_path: Union[str, Path],
                                trajectory_name: Optional[str] = None,
                                output_path: Optional[Union[str, Path]] = None,
                                fps: int = 30,
                                trail_length: int = 50,
                                show_frames: bool = True,
                                show_interactive: bool = True) -> go.Figure:
    """
    Create an animated visualization of a trajectory.

    Args:
        hdf5_path: Path to HDF5 file
        trajectory_name: Name of trajectory to animate (None = first available)
        output_path: Optional path to save animation HTML
        fps: Frames per second for animation
        trail_length: Number of previous positions to show as trail
        show_frames: Whether to show coordinate frame
        show_interactive: Whether to show the animation in browser

    Returns:
        Animated Plotly Figure
    """
    viz = JawMotionVisualizer(hdf5_path)

    # Select trajectory
    if trajectory_name is None:
        trajectory_name = list(viz.data.keys())[0]
        logger.info(f"No trajectory specified, using: {trajectory_name}")
    
    assert trajectory_name is not None, "trajectory_name must be set"

    # Create animation
    fig = viz.animate_trajectory(
        trajectory_name,
        fps=fps,
        trail_length=trail_length,
        show_frames=show_frames
    )

    # Show if requested
    if show_interactive:
        fig.show()

    # Save if path provided
    if output_path:
        fig.write_html(output_path)
        logger.info(f"Saved animation to: {output_path}")

    return fig


def main():
    """Example usage and command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Visualize jaw motion data from HDF5 files using Plotly'
    )
    parser.add_argument('hdf5_file', help='Path to HDF5 file')
    parser.add_argument('--output-dir', '-o', help='Output directory for exports')
    parser.add_argument('--formats', '-f', nargs='+',
                        default=['pdf', 'png'],
                        choices=['pdf', 'png', 'svg', 'eps'],
                        help='Export formats')
    parser.add_argument('--no-show', action='store_true',
                        help='Do not show interactive plots')
    parser.add_argument('--compare', nargs='+',
                        help='Additional HDF5 files for comparison')
    parser.add_argument('--groups', '-g', nargs='+',
                        help='Specific groups to plot from HDF5 file')
    parser.add_argument('--no-frames', action='store_true',
                        help='Do not show rotation frames in 3D plot')
    parser.add_argument('--frame-step', type=int, default=100,
                        help='Step interval for plotting coordinate frames (default: 100)')
    parser.add_argument('--list-groups', action='store_true',
                        help='List available groups in HDF5 file and exit')

    parser.add_argument('--animate', action='store_true',
                        help='Create animated visualization')
    parser.add_argument('--animate-group',
                        help='Specific group to animate')
    parser.add_argument('--fps', type=int, default=30,
                        help='Animation frames per second (default: 30)')
    parser.add_argument('--trail-length', type=int, default=50,
                        help='Animation trail length (default: 50)')

    args = parser.parse_args()

    # Handle list-groups option
    if args.list_groups:
        viz = JawMotionVisualizer(args.hdf5_file)
        print("\nAvailable groups in HDF5 file:")
        for group in viz.get_available_groups():
            print(f"  - {group}")
        return

    # Single file visualization
    _ = visualize_hdf5_file(  # Result not needed in CLI
        Path(args.hdf5_file),
        output_dir=args.output_dir,
        show_interactive=not args.no_show,
        export_formats=args.formats,
        groups_to_plot=args.groups,
        show_frames=not args.no_frames,
        frame_step=args.frame_step
    )

    # Comparison if requested
    if args.compare:
        all_files = [args.hdf5_file] + args.compare
        comparison_fig = compare_trajectories(
            all_files,
            show_frames=not args.no_frames,
            frame_step=args.frame_step
        )

        if not args.no_show:
            comparison_fig.show()

        if args.output_dir:
            output_path = Path(args.output_dir) / "trajectory_comparison.html"
            comparison_fig.write_html(output_path)
            logger.info(f"Saved comparison to: {output_path}")

    # Handle animation
    if args.animate:
        if args.animate_group:
            anim_group = args.animate_group
        elif args.groups:
            anim_group = args.groups[0]
        else:
            # Will use first available
            anim_group = None

        _ = create_trajectory_animation(  # Result not needed in CLI
            args.hdf5_file,
            trajectory_name=anim_group,
            output_path=Path(args.output_dir) / "animation.html" if args.output_dir else None,
            fps=args.fps,
            trail_length=args.trail_length,
            show_frames=not args.no_frames,
            show_interactive=not args.no_show
        )


if __name__ == '__main__':
    main()
