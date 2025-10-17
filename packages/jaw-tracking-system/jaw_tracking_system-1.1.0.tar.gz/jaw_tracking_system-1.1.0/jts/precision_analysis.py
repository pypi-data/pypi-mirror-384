#!/usr/bin/env python3

"""
precision_analysis.py: Module for analyzing precision of jaw tracking data.

This module reads HDF5 files produced by the jaw tracking system and analyzes
the precision by separating human motion from measurement noise using frequency
domain analysis.

Mathematical Framework:
The analysis assumes that true jaw motion is band-limited (typically < 5 Hz)
while measurement noise extends to higher frequencies. By applying a low-pass
filter and analyzing the residuals, we can estimate the system's precision.

Key Equations:
- Precision (RMS): $\\sigma = \\sqrt{\\frac{1}{N}\\sum_{i=1}^{N}||r_i||^2}$
- SNR: $\\text{SNR} = 10\\log_{10}\\left(\\frac{P_{signal}}{P_{noise}}\\right)$ dB
- PSD (Welch): $S(f) = \\frac{1}{KU}\\sum_{k=1}^{K}|X_k(f)|^2$
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
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Union
from dataclasses import dataclass
from scipy import signal
from scipy.spatial.transform import Rotation as R
from scipy.stats import norm

# Import the helper module for logging
from . import helper as hlp

# Set up logger
logger = hlp.setup_logger(__name__)


@dataclass
class PrecisionMetrics:
    """
    Container for precision analysis metrics.

    All translation metrics are in millimeters (mm).
    All rotation metrics are in degrees (°).
    """
    # Translation metrics
    rms_translation: float  # RMS of translation residuals magnitude in mm
    rms_translation_per_axis: np.ndarray  # RMS per axis [X, Y, Z] in mm
    std_translation: np.ndarray  # Std dev per axis in mm
    mean_translation_error: float  # Mean of residual magnitudes in mm

    # Rotation metrics
    rms_rotation: float  # RMS of rotation angle residuals in degrees
    rms_rotation_per_axis: np.ndarray  # RMS per Euler axis in degrees
    std_rotation: float  # Std dev of angle residuals in degrees
    mean_rotation_error: float  # Mean rotation error in degrees

    # Extreme values
    max_translation_error: float  # Maximum translation deviation in mm
    max_rotation_error: float  # Maximum rotation deviation in degrees

    # Signal quality metrics
    snr_translation: float  # Signal-to-noise ratio for translation
    snr_rotation: float  # Signal-to-noise ratio for rotation

    # Frequency domain data
    power_spectrum_freq: np.ndarray  # Frequency array for PSD
    power_spectrum_trans: np.ndarray  # PSD of translation noise
    power_spectrum_rot: np.ndarray  # PSD of rotation noise


class JawMotionPrecisionAnalyzer:
    """
    Analyzes precision of jaw tracking data by separating human motion from noise.

    The approach uses frequency domain filtering to separate slow human jaw motion
    (typically < 5 Hz) from higher frequency measurement noise. The analysis is
    based on the assumption that measurement noise is uncorrelated with the true
    motion signal.

    Mathematical Foundation:
    Given a measured signal $x(t) = s(t) + n(t)$ where:
        - $s(t)$ is the true jaw motion (band-limited)
        - $n(t)$ is measurement noise (broadband)

    We estimate $\\hat{s}(t)$ using a low-pass filter and compute:
        - Residuals: $r(t) = x(t) - \\hat{s}(t) \\approx n(t)$
        - Precision: $\\sigma = \\text{RMS}(r(t))$
    """

    def __init__(self, cutoff_frequency: float = 5.0):
        """
        Initialize the precision analyzer.

        Args:
            cutoff_frequency: Low-pass filter cutoff frequency in Hz.
                             Default 5.0 Hz is suitable for most jaw movements.
                             - Normal chewing: 1-2 Hz
                             - Fast chewing: 2-3 Hz
                             - Speech jaw motion: 3-5 Hz
                             - Rapid movements: up to 5 Hz
        """
        self.cutoff_frequency = cutoff_frequency
        logger.info(f"Initialized JawMotionPrecisionAnalyzer with cutoff frequency: {cutoff_frequency} Hz")

    @staticmethod
    def load_hdf5_data(filename: Union[str, Path],
                       group_name: Optional[str] = None) -> Tuple[np.ndarray, float, Dict]:
        """
        Load transformation data from HDF5 file.

        The HDF5 file should contain:
            - 'translations': (N, 3) array of positions
            - 'rotations': Either (N, 4) quaternions or (N, 3, 3) rotation matrices
            - 'sample_rate': Attribute specifying sampling frequency in Hz
            - 'unit': Attribute specifying the unit of translations (e.g., 'mm', 'm', 'cm')

        Args:
            filename: Path to HDF5 file
            group_name: Specific group to load. If None, loads first available group.

        Returns:
            Tuple containing:
            - transformations: (N, 4, 4) homogeneous transformation matrices with translations in mm
            - sample_rate: Sampling rate in Hz
            - metadata: Dictionary of HDF5 attributes

        Raises:
            FileNotFoundError: If HDF5 file doesn't exist
            ValueError: If required data is missing or malformed
        """
        filename = Path(filename)
        if not filename.exists():
            raise FileNotFoundError(f"HDF5 file not found: {filename}")

        logger.info(f"Loading data from: {filename}")

        with h5py.File(filename, 'r') as f:
            # Get group name
            if group_name is None:
                group_names = list(f.keys())
                if not group_names:
                    raise ValueError("No data groups found in HDF5 file")
                group_name = group_names[0]
                logger.info(f"Using first available group: {group_name}")

            group = f[group_name]

            # Extract data
            translations = group['translations'][:]  # type: ignore
            sample_rate = group.attrs['sample_rate']  # type: ignore

            # Get unit and convert to mm if necessary
            unit = group.attrs.get('unit', 'mm')  # Default to mm if not specified  # type: ignore

            # Define conversion factors to mm
            unit_to_mm = {
                'mm': 1.0,
                'millimeter': 1.0,
                'millimeters': 1.0,
                'cm': 10.0,
                'centimeter': 10.0,
                'centimeters': 10.0,
                'm': 1000.0,
                'meter': 1000.0,
                'meters': 1000.0,
                'in': 25.4,
                'inch': 25.4,
                'inches': 25.4,
                'ft': 304.8,
                'foot': 304.8,
                'feet': 304.8
            }

            # Convert translations to mm
            conversion_factor = unit_to_mm.get(unit.lower(), None)
            if conversion_factor is None:
                logger.warning(f"Unknown unit '{unit}'. Assuming data is in mm.")
                conversion_factor = 1.0

            if conversion_factor != 1.0:
                logger.info(f"Converting translations from {unit} to mm (factor: {conversion_factor})")
                translations = translations * conversion_factor  # type: ignore

            # Handle rotations (quaternions or matrices)
            if 'rotations' in group:  # type: ignore
                rot_data = group['rotations'][:]  # type: ignore
                if rot_data.shape[-1] == 4:  # Quaternions  # type: ignore
                    # Convert to rotation matrices
                    rotations = np.array([
                        R.from_quat(rot_data[i, [1, 2, 3, 0]]).as_matrix()  # type: ignore
                        for i in range(len(rot_data))  # type: ignore
                    ])
                else:  # Already matrices
                    rotations = rot_data
            else:
                raise ValueError("No rotation data found in HDF5 file")

            # Build transformation matrices
            n_frames = len(translations)  # type: ignore
            transformations = np.zeros((n_frames, 4, 4))
            transformations[:, :3, :3] = rotations
            transformations[:, :3, 3] = translations  # Now in mm
            transformations[:, 3, 3] = 1.0

            # Extract metadata
            metadata = {}
            for key, value in group.attrs.items():
                metadata[key] = value

            # Update unit in metadata to reflect conversion
            metadata['original_unit'] = unit
            metadata['unit'] = 'mm'  # Data is now in mm

        logger.info(f"Loaded {n_frames} frames at {sample_rate} Hz")
        logger.info(f"Data unit: {unit} (converted to mm for analysis)")

        return transformations, float(sample_rate), metadata  # type: ignore

    def compute_frequency_spectrum(self, transformations: np.ndarray,
                                   sample_rate: float,
                                   nperseg: Optional[int] = None,
                                   plot: bool = True,
                                   save_path: Optional[Path] = None,
                                   window_title: Optional[str] = None) -> Dict[str, np.ndarray]:
        """
        Compute and visualize frequency spectrum of the motion data.

        Uses Welch's method to estimate power spectral density:
        $$S(f) = \\frac{1}{K \\cdot f_s \\cdot U} \\sum_{k=0}^{K-1} |X_k(f)|^2$$

        where:
            - $K$ = number of segments
            - $f_s$ = sampling frequency
            - $U$ = normalization factor for window function
            - $X_k(f)$ = FFT of $k$-th windowed segment

        This helps identify the frequency content of actual jaw motion vs noise,
        enabling informed selection of the cutoff frequency.

        Args:
            transformations: Array of shape (N, 4, 4) transformation matrices
            sample_rate: Sampling rate in Hz
            nperseg: Length of each segment for Welch's method. If None, uses N/8
            plot: Whether to create visualization
            save_path: Optional path to save the plot
            window_title: Optional title for the plot window

        Returns:
            Dictionary containing frequency arrays and power spectra for both
            translation and rotation components
        """
        # Extract translation and rotation components
        translations = transformations[:, :3, 3]

        # Convert rotations to axis-angle representation for spectral analysis
        rotvecs = np.array([R.from_matrix(transformations[i, :3, :3]).as_rotvec()
                            for i in range(len(transformations))])

        # Compute power spectral density using Welch's method
        if nperseg is None:
            nperseg = min(len(transformations) // 8, 512)

        # Translation spectra (per axis and magnitude)
        trans_spectra = {}
        for i, axis in enumerate(['X', 'Y', 'Z']):
            f, psd = signal.welch(translations[:, i], fs=sample_rate, nperseg=nperseg)
            trans_spectra[f'trans_{axis}'] = (f, psd)

        # Translation magnitude spectrum
        trans_magnitude = np.linalg.norm(translations, axis=1)
        f, psd_trans_mag = signal.welch(trans_magnitude, fs=sample_rate, nperseg=nperseg)
        trans_spectra['trans_magnitude'] = (f, psd_trans_mag)

        # Rotation spectra (per axis and magnitude)
        rot_spectra = {}
        for i, axis in enumerate(['X', 'Y', 'Z']):
            f, psd = signal.welch(rotvecs[:, i], fs=sample_rate, nperseg=nperseg)
            rot_spectra[f'rot_{axis}'] = (f, psd)

        # Rotation magnitude spectrum
        rot_magnitude = np.linalg.norm(rotvecs, axis=1)
        f, psd_rot_mag = signal.welch(rot_magnitude, fs=sample_rate, nperseg=nperseg)
        rot_spectra['rot_magnitude'] = (f, psd_rot_mag)

        if plot:
            self._plot_frequency_spectrum(trans_spectra, rot_spectra, sample_rate, save_path, window_title)

        return {**trans_spectra, **rot_spectra}

    def _plot_frequency_spectrum(self, trans_spectra: Dict, rot_spectra: Dict,
                                 sample_rate: float, save_path: Optional[Path] = None,
                                 window_title: Optional[str] = None) -> None:
        """
        Create frequency spectrum visualization.

        Generates four subplots:
            1. Translation PSD per axis (X, Y, Z)
            2. Translation magnitude PSD with cutoff suggestions
            3. Rotation PSD per axis
            4. Cumulative power distribution

        Args:
            trans_spectra: Dictionary of frequency arrays
            rot_spectra: Dictionary of rotation frequency arrays
            sample_rate: Sampling rate in Hz
            save_path: Optional path to save the figure
            window_title: Optional name for the figure window
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        if window_title is not None:
            fig.canvas.manager.set_window_title(window_title)  # type: ignore
        fig.suptitle('Frequency Spectrum Analysis for Cutoff Selection', fontsize=16)

        # Plot 1: Translation spectra per axis
        ax = axes[0, 0]
        colors = ['r', 'g', 'b']
        for i, axis in enumerate(['X', 'Y', 'Z']):
            f, psd = trans_spectra[f'trans_{axis}']
            ax.semilogy(f, psd, color=colors[i], label=f'Translation {axis} axis', alpha=0.7)

        ax.axvline(self.cutoff_frequency, color='k', linestyle='--',
                   label=f'Current cutoff ({self.cutoff_frequency} Hz)')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('PSD (mm²/Hz)')
        ax.set_title('Translation Power Spectrum (Per Axis)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, min(20, sample_rate / 2))

        # Plot 2: Translation magnitude spectrum with annotations
        ax = axes[0, 1]
        f, psd = trans_spectra['trans_magnitude']
        ax.loglog(f, psd, 'b-', linewidth=2, label='Translation magnitude')

        # Find and annotate potential cutoff points
        # Look for frequency where power drops significantly
        db_psd = 10 * np.log10(psd)
        db_drop_threshold = -20  # 20 dB drop
        max_db = np.max(db_psd[:len(db_psd) // 4])  # Look in lower frequencies

        potential_cutoffs = []
        for i in range(1, len(f)):
            if db_psd[i] < max_db + db_drop_threshold and f[i] > 1.0:
                potential_cutoffs.append(f[i])
                if len(potential_cutoffs) == 1:  # Mark first significant drop
                    ax.axvline(f[i], color='r', linestyle=':', alpha=0.7,
                               label=f'Suggested: {f[i]:.1f} Hz')

        ax.axvline(self.cutoff_frequency, color='k', linestyle='--',
                   label=f'Current: {self.cutoff_frequency} Hz')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('PSD (mm²/Hz)')
        ax.set_title('Translation Magnitude Power Spectrum')
        ax.legend()
        ax.grid(True, which='both', alpha=0.3)
        ax.set_xlim(0.1, min(50, sample_rate / 2))

        # Plot 3: Rotation spectra per axis
        ax = axes[1, 0]
        for i, axis in enumerate(['X', 'Y', 'Z']):
            f, psd = rot_spectra[f'rot_{axis}']
            ax.semilogy(f, psd, color=colors[i], label=f'Rotation {axis} axis', alpha=0.7)

        ax.axvline(self.cutoff_frequency, color='k', linestyle='--',
                   label=f'Current cutoff ({self.cutoff_frequency} Hz)')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('PSD (rad²/Hz)')
        ax.set_title('Rotation Power Spectrum (Per Axis)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, min(20, sample_rate / 2))

        # Plot 4: Cumulative power plot
        ax = axes[1, 1]
        f, psd = trans_spectra['trans_magnitude']

        # Compute cumulative power: C(f) = ∫₀ᶠ S(f')df' / ∫₀^∞ S(f')df' × 100%
        df = f[1] - f[0] if len(f) > 1 else 1.0
        cumulative_power = np.cumsum(psd * df) / np.sum(psd * df) * 100

        ax.plot(f, cumulative_power, 'b-', linewidth=2, label='Translation')

        # Mark frequencies containing certain percentages of power
        for pct in [90, 95, 99]:
            idx = np.where(cumulative_power >= pct)[0]
            if len(idx) > 0:
                freq_pct = f[idx[0]]
                ax.axvline(freq_pct, color='gray', linestyle=':', alpha=0.5)
                ax.text(freq_pct, 50, f'{pct}%\n{freq_pct:.1f}Hz',
                        ha='center', va='center', fontsize=8)

        ax.axvline(self.cutoff_frequency, color='k', linestyle='--',
                   label=f'Current cutoff ({self.cutoff_frequency} Hz)')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Cumulative Power (%)')
        ax.set_title(
            r'Cumulative Power Distribution: $C(f) = \frac{\int_0^f S(f^\prime) df^\prime}{\int_0^\infty S(f^\prime) df^\prime} \times 100\%$')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, min(20, sample_rate / 2))
        ax.set_ylim(0, 100)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved frequency spectrum to: {save_path}")

        plt.show()

    def compute_cutoff_suggestions(self, transformations: np.ndarray,
                                   sample_rate: float,
                                   methods: List[str] = ['knee', 'power_ratio', 'snr', 'derivative']) -> Dict[
        str, float]:
        """
        Compute cutoff frequency suggestions using multiple mathematical methods.

        Available methods:
            1. 'knee': Find elbow point in log-log PSD curve
            2. 'power_ratio': Find frequency containing X% of total power
            3. 'snr': Find where SNR drops below threshold
            4. 'derivative': Find maximum negative slope in log-log space

        Args:
            transformations: Input transformation data (N, 4, 4)
            sample_rate: Sampling rate in Hz
            methods: List of methods to use

        Returns:
            Dictionary mapping method names to suggested cutoff frequencies
        """
        # Extract translation for analysis
        translations = transformations[:, :3, 3]
        trans_magnitude = np.linalg.norm(translations, axis=1)

        # Compute PSD
        nperseg = min(len(trans_magnitude) // 8, 512)
        freqs, psd = signal.welch(trans_magnitude, fs=sample_rate, nperseg=nperseg)

        suggestions = {}

        if 'knee' in methods:
            suggestions['knee_point'] = self._find_knee_point(freqs, psd)

        if 'power_ratio' in methods:
            suggestions['power_95'] = self._find_power_percentage(freqs, psd, 95)
            suggestions['power_99'] = self._find_power_percentage(freqs, psd, 99)

        if 'snr' in methods:
            suggestions['snr_based'] = self._find_snr_cutoff(freqs, psd)

        if 'derivative' in methods:
            suggestions['max_derivative'] = self._find_max_derivative_cutoff(freqs, psd)

        return suggestions

    @staticmethod
    def _find_knee_point(freqs: np.ndarray, psd: np.ndarray) -> float:
        """
        Find knee point using perpendicular distance method.

        Mathematical formulation:
            1. Transform to log-log space: $(\\log f, \\log S(f))$
            2. Fit line from first to last point
            3. Find point with maximum perpendicular distance to this line:
                $$d = \\frac{|ax_0 + by_0 + c|}{\\sqrt{a^2 + b^2}}$$

        Args:
            freqs: Frequency array
            psd: Power spectral density array

        Returns:
            Suggested cutoff frequency at knee point
        """
        # Work in log-log space
        valid_idx = (freqs > 0) & (psd > 0)
        log_f = np.log10(freqs[valid_idx])
        log_psd = np.log10(psd[valid_idx])

        if len(log_f) < 3:
            return freqs[1]  # Fallback

        # Line from first to last point
        p1 = np.array([log_f[0], log_psd[0]])
        p2 = np.array([log_f[-1], log_psd[-1]])

        # Compute perpendicular distances
        distances = []
        for i in range(len(log_f)):
            p = np.array([log_f[i], log_psd[i]])
            # Distance from point to line
            v1 = p2 - p1
            v2 = p1 - p
            cross = v1[0] * v2[1] - v1[1] * v2[0]
            d = np.abs(cross) / np.linalg.norm(v1)
            distances.append(d)

        # Find knee point
        knee_idx = np.argmax(distances)
        knee_freq = 10 ** log_f[knee_idx]

        return knee_freq

    @staticmethod
    def _find_power_percentage(freqs: np.ndarray, psd: np.ndarray,
                               percentage: float) -> float:
        """
        Find frequency containing specified percentage of total power.

        Mathematical formulation:
        Find $f_c$ such that:
        $$\\frac{\\int_0^{f_c} S(f) df}{\\int_0^\\infty S(f) df} = \\frac{\\text{percentage}}{100}$$

        Args:
            freqs: Frequency array
            psd: Power spectral density
            percentage: Target percentage (0-100)

        Returns:
            Frequency containing specified percentage of power
        """
        # Compute cumulative power using trapezoidal integration
        df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
        cumulative_power = np.cumsum(psd * df)
        total_power = cumulative_power[-1]
        cumulative_percentage = (cumulative_power / total_power) * 100

        # Find frequency where cumulative power exceeds percentage
        idx = np.where(cumulative_percentage >= percentage)[0]
        if len(idx) > 0:
            return float(freqs[idx[0]])
        return float(freqs[-1])

    @staticmethod
    def _estimate_frequency_dependent_noise_floor(freqs: np.ndarray, psd: np.ndarray,
                                                  percentile: float = 10) -> np.ndarray:
        """
        Estimate frequency-dependent noise floor using adaptive window sizes.

        Uses larger windows at low frequencies (better averaging) and smaller windows
        at high frequencies (better frequency resolution).

        Mathematical formulation:
        Window size: $$w(f) = w_{\\text{max}} \\left( \\frac{f_{\\text{max}}}{f + f_{\\text{min}}} \\right)^{\\alpha}$$
        where $\alpha$ controls the frequency dependence.

        Args:
            freqs: Frequency array
            psd: Power spectral density array
            percentile: Percentile to use for noise floor estimation (default: 10)

        Returns:
            noise_floor: Estimated noise floor array of the same length as psd
        """
        noise_floor = np.zeros_like(psd)

        # Frequency-adaptive window sizing
        f_min = freqs[1] if len(freqs) > 1 else 0.1  # Avoid division by zero
        f_max = freqs[-1]

        for i in range(len(psd)):
            # Larger windows for lower frequencies
            freq_ratio = (freqs[i] + f_min) / (f_max + f_min)
            window_size = max(3, int(len(psd) * 0.1 * (1 - 0.8 * freq_ratio)))

            start = max(0, i - window_size // 2)
            end = min(len(psd), i + window_size // 2)
            noise_floor[i] = np.percentile(psd[start:end], percentile)

        return noise_floor

    @staticmethod
    def _robust_signal_smoothing(psd: np.ndarray, freqs: np.ndarray,
                                 noise_floor: np.ndarray) -> np.ndarray:
        """
        Apply frequency-dependent smoothing with non-negative guarantees.
        Uses adaptive blending of Savitzky-Golay and median filtering:
            - High SNR regions: Trust Savitzky-Golay (preserves features)
            - Low SNR regions: Trust median filter (avoids negatives)

        Mathematical formulation:
            $$\\hat{s}(f) = w(f) \\cdot S_{SG}(f) + (1 - w(f)) \\cdot S_{med}(f)$$
        where:
            - $S_{SG}(f)$ = Savitzky-Golay smoothed PSD
            - $S_{med}(f)$ = Median filtered PSD
            - $w(f)$ = Adaptive blending weight based on local SNR

        Args:
            psd: Power spectral density array
            freqs: Frequency array
            noise_floor: Estimated noise floor array

        Returns:
            signal_estimate: Smoothed signal estimate array
        """
        if len(freqs) != len(psd):
            raise ValueError("freqs and psd must have the same length")

        window_size = max(5, len(psd) // 50)
        if window_size % 2 == 0:
            window_size += 1

        # Compute both smoothing methods
        signal_est_savgol = signal.savgol_filter(psd, window_size, 3)
        signal_est_median = signal.medfilt(psd, window_size)

        # Adaptive blending based on local SNR
        snr_ratio = (signal_est_savgol + 1e-12) / (noise_floor + 1e-12)
        blend_weight = 1 / (1 + np.exp(-10 * (snr_ratio - 1)))  # Sigmoid transition at SNR=1

        return blend_weight * signal_est_savgol + (1 - blend_weight) * signal_est_median

    @staticmethod
    def _find_snr_cutoff(freqs: np.ndarray, psd: np.ndarray,
                         snr_threshold_db: float = 10) -> float:
        """
        Find cutoff based on signal-to-noise ratio criterion.

        Mathematical formulation:
            - Signal power: $P_s(f)$ = Moving average of PSD (low frequencies)
            - Noise power: $P_n$ = High-frequency floor estimate
            - Find $f_c$ where: $10\\log_{10}(P_s(f_c)/P_n) < \\text{threshold}$

        Args:
            freqs: Frequency array
            psd: Power spectral density
            snr_threshold_db: SNR threshold in dB (default: 10)

        Returns:
            Suggested cutoff frequency based on SNR
        """
        # Frequency-dependent noise floor
        noise_floor = JawMotionPrecisionAnalyzer._estimate_frequency_dependent_noise_floor(freqs, psd)

        # Non-negative signal estimate
        signal_estimate = JawMotionPrecisionAnalyzer._robust_signal_smoothing(psd, freqs, noise_floor)

        # Robust SNR calculation
        eps = np.finfo(float).eps
        snr_db = 10 * np.log10((signal_estimate + eps) / (noise_floor + eps))

        # ratio = signal_estimate / (noise_floor + np.finfo(float).eps)
        # ratio = np.maximum(ratio, np.finfo(float).eps)
        # snr_db = 10 * np.log10(ratio)

        # Artifact detection in SNR
        artifacts = JawMotionPrecisionAnalyzer._detect_snr_artifacts(snr_db, freqs)
        if len(artifacts) > 0:
            logger.warning(f"Detected potential SNR artifacts at frequencies: {artifacts}")

        # Find where SNR drops below threshold
        below_threshold = np.where(snr_db < snr_threshold_db)[0]
        if len(below_threshold) > 0:
            return float(freqs[below_threshold[0]])

        return JawMotionPrecisionAnalyzer._find_knee_point(freqs, psd)  # Fallback

        # # Estimate noise floor from high frequencies (last 20%)
        # noise_floor = np.median(psd[int(0.8 * len(psd)):])
        #
        # # Compute moving average for signal estimate
        # window_size = max(5, len(psd) // 50)
        # if window_size % 2 == 0:
        #     window_size += 1
        # signal_estimate = signal.savgol_filter(psd, window_size, 3)
        #
        # # Compute SNR
        # # snr_db = 10 * np.log10(signal_estimate / (noise_floor + 1e-10))
        # ratio = signal_estimate / (noise_floor + 1e-10)
        # ratio = np.maximum(ratio, 1e-12)  # avoid log of zero or negative
        # snr_db = 10 * np.log10(ratio)
        #
        # # Find where SNR drops below threshold
        # below_threshold = np.where(snr_db < snr_threshold_db)[0]
        # if len(below_threshold) > 0:
        #     return freqs[below_threshold[0]]
        #
        # return JawMotionPrecisionAnalyzer._find_knee_point(freqs, psd)  # Fallback

    @staticmethod
    def _detect_snr_artifacts(snr_db: np.ndarray, freqs: np.ndarray,
                              threshold_jump: float = 10.0) -> List[float]:
        """
        Detect potential artifacts in SNR calculation.

        Args:
            snr_db: SNR values in dB
            freqs: Frequency array
            threshold_jump: Minimum dB jump to consider an artifact

        Returns:
            List of frequencies where artifacts are detected
        """
        artifacts = []

        # Look for sudden jumps in SNR (indicates estimation problems)
        snr_diff = np.diff(snr_db)
        jump_indices = np.where(np.abs(snr_diff) > threshold_jump)[0]

        # Look for local maxima that are significantly higher than neighbors
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(snr_db, height=np.median(snr_db) + 15)

        # Combine detected anomalies
        all_anomalies = np.concatenate([jump_indices, peaks])
        for idx in all_anomalies:
            if 0 <= idx < len(freqs):
                artifacts.append(freqs[idx])

        return artifacts

    @staticmethod
    def _find_max_derivative_cutoff(freqs: np.ndarray, psd: np.ndarray) -> float:
        """
        Find cutoff based on maximum negative derivative (steepest roll-off).

        Mathematical formulation:
        In log-log space, find:
        $$f_c = \\arg\\min_f \\frac{d(\\log S)}{d(\\log f)}$$

        This identifies where the spectrum has the steepest negative slope.

        Args:
            freqs: Frequency array
            psd: Power spectral density

        Returns:
            Frequency at maximum negative derivative
        """
        # Work in log-log space
        valid_idx = (freqs > 0) & (psd > 0)
        log_f = np.log10(freqs[valid_idx])
        log_psd = np.log10(psd[valid_idx])

        if len(log_f) < 11:
            return JawMotionPrecisionAnalyzer._find_knee_point(freqs, psd)  # Fallback

        # Compute derivative using Savitzky-Golay filter
        window_size = min(11, len(log_psd) // 4)
        if window_size % 2 == 0:
            window_size += 1

        derivative = signal.savgol_filter(log_psd, window_size, 3, deriv=1)

        # Find minimum (most negative) derivative in first half
        search_end = len(derivative) // 2
        min_deriv_idx = np.argmin(derivative[:search_end])

        return 10 ** log_f[min_deriv_idx]

    def visualize_cutoff_analysis(self, transformations: np.ndarray,
                                  sample_rate: float,
                                  save_path: Optional[Path] = None,
                                  window_title: Optional[str] = None) -> None:
        """
        Create comprehensive visualization of cutoff frequency analysis.

        Generates four subplots:
            1. PSD with all cutoff suggestions
            2. Cumulative power distribution
            3. SNR-based analysis
            4. Spectral slope analysis

        Args:
            transformations: Input transformation data
            sample_rate: Sampling rate in Hz
            save_path: Optional path to save figure
            window_title: Optional name for the figure window
        """
        # Compute all suggestions
        suggestions = self.compute_cutoff_suggestions(transformations, sample_rate)

        # Get frequency spectrum
        trans_magnitude = np.linalg.norm(transformations[:, :3, 3], axis=1)
        freqs, psd = signal.welch(trans_magnitude, fs=sample_rate,
                                  nperseg=min(len(trans_magnitude) // 8, 512))

        # Create figure
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        if window_title is not None:
            fig.canvas.manager.set_window_title(window_title)  # type: ignore
        fig.suptitle('Cutoff Frequency Analysis', fontsize=16)

        # 1. PSD with all suggestions
        ax = axes[0, 0]
        ax.loglog(freqs, psd, 'b-', linewidth=2, label='Translation PSD')

        # Plot all suggestions
        colors = plt.cm.rainbow(np.linspace(0, 1, len(suggestions)))  # type: ignore
        for (method, freq), color in zip(suggestions.items(), colors):
            ax.axvline(freq, color=color, linestyle='--', alpha=0.7,
                       label=f'{method}: {freq:.2f} Hz')

        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('PSD (mm²/Hz)')
        ax.set_title('Translation Power Spectral Density with Cutoff Suggestions')
        ax.legend(fontsize=8)
        ax.grid(True, which='both', alpha=0.3)
        ax.set_xlim(0.1, sample_rate / 2)

        # 2. Cumulative Power with mathematical formulation
        ax = axes[0, 1]

        # Compute cumulative power correctly
        df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
        cumulative_power = np.cumsum(psd * df) / np.sum(psd * df) * 100

        ax.semilogx(freqs, cumulative_power, 'b-', linewidth=2)

        # Mark key percentages
        for pct, color in [(90, 'g'), (95, 'orange'), (99, 'r')]:
            idx = np.where(cumulative_power >= pct)[0]
            if len(idx) > 0:
                f_pct = freqs[idx[0]]
                ax.axvline(f_pct, color=color, linestyle=':', alpha=0.7)
                ax.axhline(pct, color=color, linestyle=':', alpha=0.3)
                ax.text(f_pct, pct / 2, f'{pct}%\n{f_pct:.1f}Hz',
                        ha='center', va='center', fontsize=9,
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Cumulative Power (%)')
        ax.set_title(
            r'$C(f) = \frac{\int_0^f S(f^\prime) df^\prime}{\int_0^\infty S(f^\prime) df^\prime} \times 100\%$')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0.1, sample_rate / 2)
        ax.set_ylim(0, 100)

        # 3. SNR-based analysis
        ax = axes[1, 0]

        noise_floor = JawMotionPrecisionAnalyzer._estimate_frequency_dependent_noise_floor(freqs, psd)
        signal_estimate = JawMotionPrecisionAnalyzer._robust_signal_smoothing(psd, freqs, noise_floor)

        # Robust SNR calculation
        eps = np.finfo(float).eps
        snr_db = 10 * np.log10((signal_estimate + eps) / (noise_floor + eps))

        # ratio = signal_estimate / (noise_floor + np.finfo(float).eps)
        # ratio = np.maximum(ratio, np.finfo(float).eps)
        # snr_db = 10 * np.log10(ratio)

        # Plot with artifact detection
        artifacts = JawMotionPrecisionAnalyzer._detect_snr_artifacts(snr_db, freqs)

        ax.semilogx(freqs, snr_db, 'b-', linewidth=2, label='SNR')
        ax.axhline(10, color='r', linestyle='--', label='10 dB threshold')
        ax.axhline(0, color='k', linestyle='-', alpha=0.3)

        # Mark detected artifacts
        for artifact_freq in artifacts:
            ax.axvline(artifact_freq, color='orange', linestyle=':', alpha=0.7,
                       label='Potential artifact' if artifact_freq == artifacts[0] else "")

        if 'snr_based' in suggestions:
            ax.axvline(suggestions['snr_based'], color='r', linestyle=':', linewidth=2,
                       label=f"Suggested: {suggestions['snr_based']:.2f} Hz")

        # # Estimate noise floor
        # noise_floor = np.median(psd[int(0.8 * len(psd)):])
        # window_size = max(5, len(psd) // 50)
        # if window_size % 2 == 0:
        #     window_size += 1
        # signal_estimate = signal.savgol_filter(psd, window_size, 3)
        #
        # # snr_db = 10 * np.log10(signal_estimate / (noise_floor + 1e-10))
        # ratio = signal_estimate / (noise_floor + 1e-10)
        # ratio = np.maximum(ratio, 1e-12)  # avoid log of zero or negative
        # snr_db = 10 * np.log10(ratio)
        #
        # ax.semilogx(freqs, snr_db, 'b-', linewidth=2)
        # ax.axhline(10, color='r', linestyle='--', label='10 dB threshold')
        # ax.axhline(0, color='k', linestyle='-', alpha=0.3)
        #
        # if 'snr_based' in suggestions:
        #     ax.axvline(suggestions['snr_based'], color='r', linestyle=':', linewidth=2,
        #                label=f"Suggested: {suggestions['snr_based']:.2f} Hz")

        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('SNR (dB)')
        ax.set_title('Signal-to-Noise Ratio Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0.1, sample_rate / 2)

        # 4. Derivative analysis (roll-off rate)
        ax = axes[1, 1]

        # Compute log-log derivative
        valid_idx = (freqs > 0) & (psd > 0)
        log_f = np.log10(freqs[valid_idx])
        log_psd = np.log10(psd[valid_idx])

        if len(log_psd) >= 11:
            window_size = min(11, len(log_psd) // 4)
            if window_size % 2 == 0:
                window_size += 1
            derivative = signal.savgol_filter(log_psd, window_size, 3, deriv=1)

            ax.semilogx(10 ** log_f, derivative, 'b-', linewidth=2)
            ax.axhline(0, color='k', linestyle='-', alpha=0.3)
            ax.axhline(-1, color='g', linestyle=':', alpha=0.5, label='Slope = -1 (1/f)')
            ax.axhline(-2, color='orange', linestyle=':', alpha=0.5, label='Slope = -2 (1/f²)')

            if 'max_derivative' in suggestions:
                ax.axvline(suggestions['max_derivative'], color='r', linestyle=':', linewidth=2,
                           label=f"Max slope: {suggestions['max_derivative']:.2f} Hz")

        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('d(log PSD)/d(log f)')
        ax.set_title('Spectral Slope Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0.1, sample_rate / 2)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.show()

        # Print summary
        logger.info("\nCutoff Frequency Suggestions:")
        logger.info("=" * 50)
        for method, freq in suggestions.items():
            logger.info(f"{method:20s}: {freq:6.2f} Hz")
        logger.info("=" * 50)
        freq_values = list(suggestions.values())
        logger.info(f"Mean suggestion: {np.mean(freq_values):.2f} Hz")
        logger.info(f"Median suggestion: {np.median(freq_values):.2f} Hz")

    def design_lowpass_filter(self, sample_rate: float,
                              filter_order: int = 4) -> Tuple[np.ndarray, np.ndarray]:
        """
        Design a Butterworth low-pass filter.

        Transfer function:
        $$H(s) = \\frac{1}{\\sqrt{1 + (s/\\omega_c)^{2n}}}$$

        where $\\omega_c = 2\\pi f_c$ is the cutoff frequency and $n$ is the filter order.

        Args:
            sample_rate: Sampling rate in Hz
            filter_order: Filter order (default 4 for good roll-off without excessive ringing)

        Returns:
            Tuple of (b, a) filter coefficients for discrete-time implementation

        Note:
            The effective filter order when using filtfilt is 2n due to forward-backward filtering.
        """
        nyquist = sample_rate / 2
        normalized_cutoff = self.cutoff_frequency / nyquist

        if normalized_cutoff >= 1.0:
            logger.warning(f"Cutoff frequency {self.cutoff_frequency} Hz is above Nyquist frequency. "
                           f"Setting to 0.95 * Nyquist")
            normalized_cutoff = 0.95

        b, a = signal.butter(filter_order, normalized_cutoff, btype='low')  # type: ignore

        logger.info(f"Designed Butterworth filter: order={filter_order}, "
                    f"cutoff={self.cutoff_frequency} Hz, fs={sample_rate} Hz")

        return b, a

    def filter_transformations(self, transformations: np.ndarray,
                               sample_rate: float) -> np.ndarray:
        """
        Apply zero-phase low-pass filter to transformation data.

        Mathematical formulation for zero-phase filtering (filtfilt):
            1. Forward pass: $y_1[n] = \\mathcal{F}\\{x[n]\\}$
            2. Time reversal: $y_1'[n] = y_1[N-1-n]$
            3. Backward pass: $y_2[n] = \\mathcal{F}\\{y_1'[n]\\}$
            4. Time reversal: $y[n] = y_2[N-1-n]$

        This results in:
            - Zero phase shift: $\\angle H(e^{j\\omega}) = 0$
            - Squared magnitude response: $|H_{filtfilt}(e^{j\\omega})|^2 = |H(e^{j\\omega})|^4$
            - Effective filter order = 2 × design_order

        Args:
            transformations: Array of shape (N, 4, 4) homogeneous transformation matrices
            sample_rate: Sampling rate in Hz

        Returns:
            Filtered transformations with NO phase shift, preserving time alignment

        Note:
            Rotations are filtered in axis-angle representation to maintain proper
            interpolation on the rotation manifold.
        """
        # Design filter
        b, a = self.design_lowpass_filter(sample_rate)

        # Log filter characteristics
        logger.debug(f"Filter gain at DC: {np.sum(b) / np.sum(a):.6f}")
        logger.debug(f"Filter gain at cutoff: {self._compute_filter_gain_at_cutoff(b, a, sample_rate):.6f}")

        # Extract components
        translations = transformations[:, :3, 3]
        rotations = transformations[:, :3, :3]

        # Convert rotations to axis-angle for filtering
        rotvecs = np.array([R.from_matrix(rot).as_rotvec() for rot in rotations])

        # Apply zero-phase filter to translations
        filtered_translations = np.zeros_like(translations)
        for i in range(3):
            filtered_translations[:, i] = signal.filtfilt(b, a, translations[:, i])

        # Apply zero-phase filter to rotation vectors
        filtered_rotvecs = np.zeros_like(rotvecs)
        for i in range(3):
            filtered_rotvecs[:, i] = signal.filtfilt(b, a, rotvecs[:, i])

        # Convert back to matrices
        filtered_rotations = np.array([
            R.from_rotvec(rv).as_matrix() for rv in filtered_rotvecs
        ])

        # Reconstruct transformations
        filtered_transformations = np.zeros_like(transformations)
        filtered_transformations[:, :3, :3] = filtered_rotations
        filtered_transformations[:, :3, 3] = filtered_translations
        filtered_transformations[:, 3, 3] = 1.0

        return filtered_transformations

    def _compute_filter_gain_at_cutoff(self, b: np.ndarray, a: np.ndarray,
                                       sample_rate: float) -> float:
        """
        Compute filter gain at cutoff frequency.

        For digital filter: $H(e^{j\\omega}) = \\frac{B(e^{j\\omega})}{A(e^{j\\omega})}$
        where $\\omega = 2\\pi f / f_s$

        Returns squared gain due to filtfilt application.
        """
        w = 2 * np.pi * self.cutoff_frequency / sample_rate
        z = np.exp(1j * w)
        H = np.polyval(b[::-1], z) / np.polyval(a[::-1], z)

        return np.abs(H) ** 2  # Squared due to filtfilt

    def analyze_filter_response(self, sample_rate: float,
                                plot: bool = True) -> Dict[str, np.ndarray]:
        """
        Analyze and visualize the filter frequency response.

        Computes:
            - Magnitude response: $|H(e^{j\\omega})|$ in dB
            - Phase response: $\\angle H(e^{j\\omega})$ (zero for filtfilt)
            - Group delay: $-d\\phi/d\\omega$ (zero for filtfilt)
            - Impulse response: $h[n]$

        Args:
            sample_rate: Sampling rate in Hz
            plot: Whether to create a visualization of the frequency response

        Returns:
            Dictionary with frequency response data
        """
        b, a = self.design_lowpass_filter(sample_rate)

        # Compute frequency response
        w, h = signal.freqz(b, a, worN=8000, fs=sample_rate)  # type: ignore

        # Account for filtfilt (squared response)
        h_filtfilt = h ** 2

        # Phase response (zero for filtfilt)
        phase_filtfilt = np.zeros_like(w)

        # Group delay (zero for filtfilt)
        gd = np.zeros_like(w)

        if plot:
            fig, axes = plt.subplots(3, 1, figsize=(10, 8))
            fig.suptitle('Filter Characterization', fontsize=14)

            # Magnitude response
            axes[0].plot(w, 20 * np.log10(np.abs(h)), 'b', label='Single pass', alpha=0.7)
            axes[0].plot(w, 20 * np.log10(np.abs(h_filtfilt)), 'r', linewidth=2, label='filtfilt (used)')
            axes[0].axvline(self.cutoff_frequency, color='k', linestyle='--', alpha=0.5,
                            label=f'Cutoff: {self.cutoff_frequency} Hz')
            axes[0].axhline(-3, color='g', linestyle=':', alpha=0.5, label='-3 dB')
            axes[0].set_xlim(0, sample_rate / 2)
            axes[0].set_ylabel('Magnitude (dB)')
            axes[0].set_title('Filter Frequency Response')
            axes[0].grid(True, alpha=0.3)
            axes[0].legend()

            # Phase response
            axes[1].plot(w, np.angle(h), 'b', label='Single pass', alpha=0.7)
            axes[1].plot(w, phase_filtfilt, 'r', linewidth=3, label='filtfilt (zero phase)')
            axes[1].axvline(self.cutoff_frequency, color='k', linestyle='--', alpha=0.5)
            axes[1].set_xlim(0, sample_rate / 2)
            axes[1].set_ylabel('Phase (radians)')
            axes[1].set_xlabel('Frequency (Hz)')
            axes[1].grid(True, alpha=0.3)
            axes[1].legend()

            # Impulse response
            imp = signal.unit_impulse(100)
            y_single = signal.lfilter(b, a, imp)
            y_filtfilt = signal.filtfilt(b, a, imp)

            axes[2].stem(np.arange(len(y_single)), y_single, basefmt=" ", label='Single pass')
            axes[2].stem(np.arange(len(y_filtfilt)), y_filtfilt, basefmt=" ", label='filtfilt (symmetric)',
                         markerfmt='ro')
            axes[2].set_xlabel('Sample')
            axes[2].set_ylabel('Amplitude')
            axes[2].set_title('Impulse Response')
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

        return {
            'frequency': w,
            'magnitude': np.abs(h_filtfilt),
            'phase': phase_filtfilt,
            'group_delay': gd
        }

    @staticmethod
    def compute_residuals(raw: np.ndarray, filtered: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute residuals between raw and filtered data.

        Translation residuals:
        $$\\mathbf{r}_{\\text{trans}} = \\mathbf{p}_{\\text{raw}} - \\mathbf{p}_{\\text{filtered}}$$

        Rotation residuals (using relative rotation):
        $$\\mathbf{R}_{\\text{residual}} = \\mathbf{R}_{\\text{raw}} \\mathbf{R}_{\\text{filtered}}^T$$
        $$\\theta = \\arccos\\left(\\frac{\\text{trace}(\\mathbf{R}_{\\text{residual}}) - 1}{2}\\right)$$

        Args:
            raw: Raw transformation matrices (N, 4, 4)
            filtered: Filtered transformation matrices (N, 4, 4)

        Returns:
            Tuple containing:
            - translation_residuals: (N, 3) array in mm
            - rotation_residuals_degrees: (N,) array of rotation angles in degrees
            - rotation_euler_residuals: (N, 3) array of Euler angles in degrees
        """
        # Translation residuals (in mm)
        trans_residuals = raw[:, :3, 3] - filtered[:, :3, 3]

        # Rotation residuals (angle magnitude)
        rot_residuals_rad = []
        rot_euler_residuals = []

        for i in range(len(raw)):
            # Relative rotation: R_residual = R_raw @ R_filtered^T
            R_residual = raw[i, :3, :3] @ filtered[i, :3, :3].T

            # Convert to angle magnitude (Rodrigues' formula)
            trace = np.trace(R_residual)
            # Clamp to avoid numerical issues with arccos
            cos_angle = np.clip((trace - 1) / 2, -1, 1)
            angle = np.arccos(cos_angle)
            rot_residuals_rad.append(angle)

            # Also get Euler angles for per-axis analysis
            euler = R.from_matrix(R_residual).as_euler('xyz', degrees=True)
            rot_euler_residuals.append(euler)

        rot_residuals_deg = np.degrees(rot_residuals_rad)
        rot_euler_residuals = np.array(rot_euler_residuals)

        return trans_residuals, rot_residuals_deg, rot_euler_residuals

    @staticmethod
    def compute_power_spectral_density(residuals: np.ndarray,
                                       sample_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute power spectral density of residuals using Welch's method.

        Welch's method estimates PSD by:
            1. Dividing signal into overlapping segments
            2. Windowing each segment
            3. Computing FFT of each windowed segment
            4. Averaging the squared magnitudes

        $$S(f) = \\frac{1}{K \\cdot U} \\sum_{k=1}^{K} |\\text{FFT}(w[n] \\cdot x_k[n])|^2$$

        Args:
            residuals: Residual signal (either 1D or multi-dimensional)
            sample_rate: Sampling rate in Hz

        Returns:
            Tuple of (frequencies, psd) arrays
        """
        # Use Welch's method for PSD estimation
        nperseg = min(len(residuals) // 4, 256)  # Segment length

        if residuals.ndim == 1:
            freqs, psd = signal.welch(residuals, fs=sample_rate, nperseg=nperseg)
        else:
            # For multi-dimensional, compute PSD of magnitude
            magnitude = np.linalg.norm(residuals, axis=1)
            freqs, psd = signal.welch(magnitude, fs=sample_rate, nperseg=nperseg)

        return freqs, psd

    def analyze_precision(self, transformations: np.ndarray,
                          sample_rate: float,
                          metadata: Optional[Dict] = None) -> PrecisionMetrics:
        """
        Perform complete precision analysis.

        The analysis separates signal from noise using frequency-domain filtering
        and computes various error metrics from the residuals.

        Translation metrics:
            - RMS magnitude: $\\sigma_{\\text{trans}} = \\sqrt{\\frac{1}{N}\\sum_{i=1}^{N}||\\mathbf{r}_i||^2}$
            - Per-axis RMS: $\\sigma_x = \\sqrt{\\frac{1}{N}\\sum_{i=1}^{N}r_{x,i}^2}$
            - Mean error: $\\bar{e} = \\frac{1}{N}\\sum_{i=1}^{N}||\\mathbf{r}_i||$

        Rotation metrics:
            - RMS angle: $\\sigma_{\\text{rot}} = \\sqrt{\\frac{1}{N}\\sum_{i=1}^{N}\\theta_i^2}$
            - Per-axis RMS: Using Euler angle decomposition

        Signal-to-Noise Ratio:
        $$\\text{SNR} = 10\\log_{10}\\left(\\frac{\\text{Var}(\\text{signal})}{\\text{Var}(\\text{noise})}\\right)$$ dB

        Args:
            transformations: Raw transformation data (N, 4, 4)
            sample_rate: Sampling rate in Hz
            metadata: Optional metadata dictionary (not currently used but for consistency)

        Returns:
            PrecisionMetrics object with comprehensive analysis results
        """
        logger.info("Starting precision analysis...")

        # Filter data
        filtered = self.filter_transformations(transformations, sample_rate)

        # Compute residuals
        trans_residuals, rot_residuals, rot_euler_residuals = self.compute_residuals(transformations, filtered)

        # Translation metrics (in mm)
        trans_magnitude = np.linalg.norm(trans_residuals, axis=1)
        rms_trans = np.sqrt(np.mean(trans_magnitude ** 2))
        rms_trans_per_axis = np.sqrt(np.mean(trans_residuals ** 2, axis=0))
        std_trans = np.std(trans_residuals, axis=0)
        mean_trans = np.mean(trans_magnitude)
        max_trans = np.max(trans_magnitude)

        # Rotation metrics (in degrees)
        rms_rot = np.sqrt(np.mean(rot_residuals ** 2))
        rms_rot_per_axis = np.sqrt(np.mean(rot_euler_residuals ** 2, axis=0))
        std_rot = np.std(rot_residuals)
        mean_rot = np.mean(rot_residuals)
        max_rot = np.max(rot_residuals)

        # Signal-to-noise ratio for translation
        signal_trans_mag = np.linalg.norm(filtered[:, :3, 3], axis=1)
        signal_power_trans = np.var(signal_trans_mag)
        noise_power_trans = np.var(trans_magnitude)
        snr_trans = 10 * np.log10(signal_power_trans / noise_power_trans) if noise_power_trans > 0 else np.inf

        # Signal-to-noise ratio for rotation
        filtered_angles = []
        for i in range(len(filtered)):
            trace = np.trace(filtered[i, :3, :3])
            cos_angle = np.clip((trace - 1) / 2, -1, 1)
            angle = np.arccos(cos_angle)
            filtered_angles.append(angle)
        signal_power_rot = np.var(np.degrees(filtered_angles))
        noise_power_rot = np.var(rot_residuals)
        snr_rot = 10 * np.log10(signal_power_rot / noise_power_rot) if noise_power_rot > 0 else np.inf

        # Power spectral density of noise
        freq_trans, psd_trans = self.compute_power_spectral_density(trans_residuals, sample_rate)
        freq_rot, psd_rot = self.compute_power_spectral_density(rot_residuals, sample_rate)

        metrics = PrecisionMetrics(
            rms_translation=rms_trans,
            rms_translation_per_axis=rms_trans_per_axis,
            std_translation=std_trans,
            mean_translation_error=mean_trans,
            rms_rotation=rms_rot,
            rms_rotation_per_axis=rms_rot_per_axis,
            std_rotation=float(std_rot),
            mean_rotation_error=float(mean_rot),
            max_translation_error=max_trans,
            max_rotation_error=max_rot,
            snr_translation=snr_trans,
            snr_rotation=snr_rot,
            power_spectrum_freq=freq_trans,
            power_spectrum_trans=psd_trans,
            power_spectrum_rot=psd_rot
        )

        logger.info("Precision Analysis Results:")
        logger.info(f"  Translation RMS (magnitude): {rms_trans:.3f} mm")
        logger.info(f"  Translation RMS per axis: X={rms_trans_per_axis[0]:.3f}, "
                    f"Y={rms_trans_per_axis[1]:.3f}, Z={rms_trans_per_axis[2]:.3f} mm")
        logger.info(f"  Translation Mean Error: {mean_trans:.3f} mm")
        logger.info(f"  Rotation RMS (angle): {rms_rot:.3f}°")
        logger.info(f"  Rotation RMS per axis: Roll={rms_rot_per_axis[0]:.3f}, "
                    f"Pitch={rms_rot_per_axis[1]:.3f}, Yaw={rms_rot_per_axis[2]:.3f}°")
        logger.info(f"  SNR Translation: {snr_trans:.1f} dB")
        logger.info(f"  SNR Rotation: {snr_rot:.1f} dB")

        return metrics

    def visualize_analysis(self, transformations: np.ndarray,
                           sample_rate: float,
                           metrics: Optional[PrecisionMetrics] = None,
                           save_path: Optional[Path] = None,
                           window_title: Optional[str] = None) -> None:
        """
        Create comprehensive visualization of precision analysis.

        Generates six subplots:
            1. Raw vs filtered translation trajectories
            2. Translation residuals with magnitude
            3. Rotation angle residuals
            4. Rotation Euler angle residuals
            5. Translation noise PSD
            6. Translation residual distribution with normal fit
            7. Summary statistics

        Args:
            transformations: Raw transformation data
            sample_rate: Sampling rate in Hz
            metrics: Pre-computed metrics (optional)
            save_path: Path to save figure
            window_title: Optional name for the figure window
        """
        if metrics is None:
            metrics = self.analyze_precision(transformations, sample_rate)

        # Filter data for visualization
        filtered = self.filter_transformations(transformations, sample_rate)
        trans_residuals, rot_residuals, rot_euler_residuals = self.compute_residuals(transformations, filtered)

        # Create time array
        time = np.arange(len(transformations)) / sample_rate

        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12))
        if window_title is not None:
            fig.canvas.manager.set_window_title(window_title)  # type: ignore
        gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)

        # 1. Raw vs Filtered Trajectories (Translation)
        ax1 = fig.add_subplot(gs[0, :])
        raw_trans = transformations[:, :3, 3]
        filt_trans = filtered[:, :3, 3]

        for i, (axis, color) in enumerate(zip(['X', 'Y', 'Z'], ['r', 'g', 'b'])):
            ax1.plot(time, raw_trans[:, i], color=color, alpha=0.3, label=f'Translation {axis} raw')
            ax1.plot(time, filt_trans[:, i], color=color, linewidth=2, label=f'Translation {axis} filtered')

        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Position (mm)')
        ax1.set_title('Raw vs Filtered Translation Components')
        ax1.legend(ncol=6, loc='upper right', fontsize=8)
        ax1.grid(True, alpha=0.3)

        # 2. Translation Residuals
        ax2 = fig.add_subplot(gs[1, :])
        for i, (axis, color) in enumerate(zip(['X', 'Y', 'Z'], ['r', 'g', 'b'])):
            ax2.plot(time, trans_residuals[:, i], color=color, alpha=0.7, label=f'Translation {axis}')

        # Add magnitude
        trans_mag = np.linalg.norm(trans_residuals, axis=1)
        ax2.plot(time, trans_mag, 'k--', alpha=0.5, linewidth=2, label='Translation Magnitude')

        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Residual (mm)')
        ax2.set_title(f'Translation Residuals (RMS magnitude = {metrics.rms_translation:.3f} mm)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Rotation Residuals (angle magnitude)
        ax3 = fig.add_subplot(gs[2, :2])
        ax3.plot(time, rot_residuals, 'k', alpha=0.7, label='Rotation Angle Magnitude')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Residual (degrees)')
        ax3.set_title(f'Rotation Angle Residuals (RMS = {metrics.rms_rotation:.3f}°)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 3b. Euler angle residuals
        ax3b = fig.add_subplot(gs[2, 2])
        for i, (axis, color) in enumerate(zip(['Roll', 'Pitch', 'Yaw'], ['r', 'g', 'b'])):
            ax3b.plot(time, rot_euler_residuals[:, i], color=color, alpha=0.7,
                      label=f'Rotation {axis} ({metrics.rms_rotation_per_axis[i]:.2f}°)')
        ax3b.set_xlabel('Time (s)')
        ax3b.set_ylabel('Euler Residual (degrees)')
        ax3b.set_title('Rotation Residuals by Euler Axis')
        ax3b.legend(fontsize=8)
        ax3b.grid(True, alpha=0.3)

        # 4. Power Spectral Density - Translation
        ax4 = fig.add_subplot(gs[3, 0])
        ax4.semilogy(metrics.power_spectrum_freq, metrics.power_spectrum_trans, 'b', label='Translation Noise')
        ax4.axvline(self.cutoff_frequency, color='r', linestyle='--', label=f'Cutoff ({self.cutoff_frequency} Hz)')
        ax4.set_xlabel('Frequency (Hz)')
        ax4.set_ylabel('PSD (mm²/Hz)')
        ax4.set_title('Translation Noise Power Spectral Density')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim(0, sample_rate / 2)

        # 5. Histogram of Translation Residuals
        ax5 = fig.add_subplot(gs[3, 1])
        residual_magnitude = np.linalg.norm(trans_residuals, axis=1)
        n, bins, _ = ax5.hist(residual_magnitude, bins=50, density=True, alpha=0.7, color='blue',
                              label='Translation Data')

        # Fit normal distribution
        mu, sigma = norm.fit(residual_magnitude)
        x = np.linspace(0, residual_magnitude.max(), 100)
        ax5.plot(x, norm.pdf(x, mu, sigma), 'r-', linewidth=2,
                 label=f'Normal fit\nμ={mu:.3f} mm, σ={sigma:.3f} mm')

        ax5.set_xlabel('Translation Residual Magnitude (mm)')
        ax5.set_ylabel('Probability Density')
        ax5.set_title('Distribution of Translation Residuals')
        ax5.legend()
        ax5.grid(True, alpha=0.3)

        # 6. Summary Statistics Box
        ax6 = fig.add_subplot(gs[3, 2])
        ax6.axis('off')

        summary_text = f"""Precision Analysis Summary

            Translation:
              RMS Error (magnitude): {metrics.rms_translation:.4f} mm
              RMS per axis: X={metrics.rms_translation_per_axis[0]:.4f} mm, 
                             Y={metrics.rms_translation_per_axis[1]:.4f} mm, 
                             Z={metrics.rms_translation_per_axis[2]:.4f} mm
              Mean Error: {metrics.mean_translation_error:.4f} mm
              Max Error: {metrics.max_translation_error:.4f} mm
              SNR: {metrics.snr_translation:.2f} dB
            
            Rotation:
              RMS Error (angle): {metrics.rms_rotation:.4f}°
              RMS per axis: Roll={metrics.rms_rotation_per_axis[0]:.4f}°,
                             Pitch={metrics.rms_rotation_per_axis[1]:.4f}°,
                             Yaw={metrics.rms_rotation_per_axis[2]:.4f}°
              Mean Error: {metrics.mean_rotation_error:.4f}°
              Max Error: {metrics.max_rotation_error:.4f}°
              SNR: {metrics.snr_rotation:.2f} dB
            
            Filter Settings:
              Cutoff: {self.cutoff_frequency} Hz
              Sample Rate: {sample_rate} Hz
              Effective Order: 8 (4×2 filtfilt)"""

        ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
                 fontsize=9, verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.suptitle('Jaw Tracking Precision Analysis', fontsize=16)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved figure to: {save_path}")

        plt.show()

    @staticmethod
    def export_metrics(metrics: PrecisionMetrics,
                       output_path: Union[str, Path],
                       metadata: Optional[Dict] = None) -> None:
        """
        Export metrics to CSV file.

        Creates a human-readable CSV with all precision metrics.

        Args:
            metrics: Computed precision metrics
            output_path: Path for output CSV file
            metadata: Optional metadata dictionary containing unit information
        """
        output_path = Path(output_path)

        # Create metrics dictionary
        data = {
            'Metric': [
                'Translation RMS (magnitude) (mm)',
                'Translation RMS X (mm)',
                'Translation RMS Y (mm)',
                'Translation RMS Z (mm)',
                'Translation Mean Error (mm)',
                'Translation Max Error (mm)',
                'Translation SNR (dB)',
                'Rotation RMS (angle) (degrees)',
                'Rotation RMS Roll (degrees)',
                'Rotation RMS Pitch (degrees)',
                'Rotation RMS Yaw (degrees)',
                'Rotation Mean Error (degrees)',
                'Rotation Max Error (degrees)',
                'Rotation SNR (dB)'
            ],
            'Value': [
                metrics.rms_translation,
                metrics.rms_translation_per_axis[0],
                metrics.rms_translation_per_axis[1],
                metrics.rms_translation_per_axis[2],
                metrics.mean_translation_error,
                metrics.max_translation_error,
                metrics.snr_translation,
                metrics.rms_rotation,
                metrics.rms_rotation_per_axis[0],
                metrics.rms_rotation_per_axis[1],
                metrics.rms_rotation_per_axis[2],
                metrics.mean_rotation_error,
                metrics.max_rotation_error,
                metrics.snr_rotation
            ]
        }

        # Add metadata information if available
        if metadata:
            if 'original_unit' in metadata:
                data['Metric'].append('Original Data Unit')
                data['Value'].append(metadata['original_unit'])
            if 'unit' in metadata:
                data['Metric'].append('Analysis Unit')
                data['Value'].append(metadata['unit'])

        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, float_format='%.4f')

        logger.info(f"Exported metrics to: {output_path}")


def analyze_multiple_trials(hdf5_files: List[Union[str, Path]],
                            cutoff_frequency: Union[float, List[float]] = 5.0,
                            output_dir: Optional[Path] = None,
                            analyze_spectrum: bool = True,
                            analyze_cutoff: bool = False) -> pd.DataFrame:
    """
    Analyze precision across multiple trials/files.

    This function processes multiple HDF5 files and generates:
        - Individual precision analyses
        - Frequency spectrum plots (optional)
        - Cutoff frequency analyses (optional)
        - Summary statistics across all trials

    Args:
        hdf5_files: List of HDF5 files to analyze
        cutoff_frequency: Cutoff frequency for low-pass filter (Hz)
        output_dir: Directory to save results
        analyze_spectrum: Whether to generate frequency spectrum plots
        analyze_cutoff: Whether to perform cutoff frequency analysis

    Returns:
        DataFrame with aggregated metrics for all trials
    """
    # Support per-file cutoff frequencies
    if isinstance(cutoff_frequency, list):
        if len(cutoff_frequency) == len(hdf5_files):
            cutoff_list = cutoff_frequency
        elif len(cutoff_frequency) == 1:
            cutoff_list = cutoff_frequency * len(hdf5_files)
        else:
            raise ValueError("cutoff_frequency must be a single value or a list of the same length as hdf5_files")
    else:
        cutoff_list = [cutoff_frequency] * len(hdf5_files)

    all_metrics = []

    for file_path, cutoff in zip(hdf5_files, cutoff_list):
        logger.info(f"\nAnalyzing: {file_path} (cutoff: {cutoff} Hz)")
        analyzer = JawMotionPrecisionAnalyzer(cutoff)
        try:
            # Load data
            transformations, sample_rate, metadata = analyzer.load_hdf5_data(file_path)

            # Analyze frequency spectrum if requested
            if analyze_spectrum and output_dir:
                spectrum_path = output_dir / Path(f"{Path(file_path).stem}_frequency_spectrum.png")
                analyzer.compute_frequency_spectrum(transformations, sample_rate,
                                                    plot=True, save_path=spectrum_path,
                                                    window_title=Path(file_path).stem)

            # Analyze cutoff frequency if requested
            if analyze_cutoff and output_dir:
                cutoff_path = output_dir / Path(f"{Path(file_path).stem}_cutoff_analysis.png")
                analyzer.visualize_cutoff_analysis(transformations, sample_rate,
                                                   save_path=cutoff_path, window_title=Path(file_path).stem)

            # Analyze precision
            metrics = analyzer.analyze_precision(transformations, sample_rate)

            # Store results
            result = {
                'File': Path(file_path).name,
                'Translation_RMS_mm': metrics.rms_translation,
                'Translation_Mean_mm': metrics.mean_translation_error,
                'Translation_Max_mm': metrics.max_translation_error,
                'Rotation_RMS_deg': metrics.rms_rotation,
                'Rotation_Mean_deg': metrics.mean_rotation_error,
                'Rotation_Max_deg': metrics.max_rotation_error,
                'Translation_SNR_dB': metrics.snr_translation,
                'Rotation_SNR_dB': metrics.snr_rotation,
                'Sample_Rate_Hz': sample_rate,
                'Num_Frames': len(transformations),
                'Cutoff_Hz': cutoff
            }
            all_metrics.append(result)

            # Save individual visualization if output directory provided
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

                fig_path = output_dir / Path(f"{Path(file_path).stem}_precision_analysis.png")
                analyzer.visualize_analysis(transformations, sample_rate, metrics, fig_path, Path(file_path).stem)

                # Export individual metrics
                metrics_path = output_dir / Path(f"{Path(file_path).stem}_metrics.csv")
                analyzer.export_metrics(metrics, metrics_path)

        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            continue

    # Create summary DataFrame
    df = pd.DataFrame(all_metrics)

    if output_dir and len(df) > 0:
        summary_path = output_dir / "precision_analysis_summary.csv"
        df.to_csv(summary_path, index=False, float_format='%.4f')
        logger.info(f"\nSaved summary to: {summary_path}")

    # Print summary statistics
    if len(df) > 0:
        logger.info("\n" + "=" * 60)
        logger.info("PRECISION ANALYSIS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Analyzed {len(df)} files with cutoff frequency {cutoff_frequency} Hz")
        logger.info("\nTranslation Precision:")
        logger.info(f"  Mean RMS: {df['Translation_RMS_mm'].mean():.3f} ± {df['Translation_RMS_mm'].std():.3f} mm")
        logger.info(f"  Range: {df['Translation_RMS_mm'].min():.3f} - {df['Translation_RMS_mm'].max():.3f} mm")
        logger.info("\nRotation Precision:")
        logger.info(f"  Mean RMS: {df['Rotation_RMS_deg'].mean():.3f} ± {df['Rotation_RMS_deg'].std():.3f}°")
        logger.info(f"  Range: {df['Rotation_RMS_deg'].min():.3f} - {df['Rotation_RMS_deg'].max():.3f}°")
        logger.info("=" * 60)

    return df


def main():
    """
    Command-line interface for precision analysis.

    Examples:
        # Analyze single file with default settings
        python precision_analysis.py jaw_motion.h5

        # Analyze with custom cutoff and save results
        python precision_analysis.py jaw_motion.h5 --cutoff 4.0 --output-dir results/

        # Analyze with frequency spectrum and cutoff analysis
        python precision_analysis.py jaw_motion.h5 --spectrum --cutoff-analysis

        # Batch analysis of multiple files
        python precision_analysis.py *.h5 --cutoff 5.0 --output-dir batch_results/
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze precision of jaw tracking data from HDF5 files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
              %(prog)s jaw_motion.h5                    # Basic analysis
              %(prog)s jaw_motion.h5 --cutoff 4.0      # Custom cutoff frequency
              %(prog)s *.h5 --output-dir results/      # Batch processing
              %(prog)s data.h5 --spectrum --cutoff-analysis  # Full analysis
        """
    )
    parser.add_argument('input', nargs='+', help='Input HDF5 file(s)')
    parser.add_argument('--cutoff', type=float, nargs='+', default=5.0,
                        help='Low-pass filter cutoff frequency/frequencies in Hz. Specify one value to use for all '
                             'files, or N values (N = number of files) for per-file cutoffs. (default: 5.0)')
    parser.add_argument('--output-dir', type=str,
                        help='Directory to save analysis results')
    parser.add_argument('--group', type=str,
                        help='Specific HDF5 group to analyze')
    parser.add_argument('--spectrum', action='store_true',
                        help='Generate frequency spectrum analysis')
    parser.add_argument('--cutoff-analysis', action='store_true',
                        help='Perform cutoff frequency analysis with multiple methods')
    parser.add_argument('--filter-response', action='store_true',
                        help='Analyze and plot filter frequency response')

    args = parser.parse_args()

    if len(args.input) == 1:
        # Single file analysis
        analyzer = JawMotionPrecisionAnalyzer(args.cutoff)

        # Load data
        transformations, sample_rate, metadata = analyzer.load_hdf5_data(
            args.input[0], args.group
        )

        # Filter response analysis if requested
        if args.filter_response:
            analyzer.analyze_filter_response(sample_rate, plot=True)

        # Frequency spectrum analysis if requested
        if args.spectrum:
            save_path = None
            if args.output_dir:
                output_dir = Path(args.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                save_path = output_dir / "frequency_spectrum.png"

            analyzer.compute_frequency_spectrum(transformations, sample_rate,
                                                plot=True, save_path=save_path, window_title=Path(args.input[0]).stem)

        # Cutoff frequency analysis if requested
        if args.cutoff_analysis:
            save_path = None
            if args.output_dir:
                output_dir = Path(args.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                save_path = output_dir / "cutoff_analysis.png"

            analyzer.visualize_cutoff_analysis(transformations, sample_rate,
                                               save_path=save_path, window_title=Path(args.input[0]).stem)

        # Analyze precision
        metrics = analyzer.analyze_precision(transformations, sample_rate)

        # Visualize
        save_path = None
        if args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            save_path = output_dir / "precision_analysis.png"

            # Also save metrics
            metrics_path = output_dir / "precision_metrics.csv"
            analyzer.export_metrics(metrics, metrics_path)

        analyzer.visualize_analysis(transformations, sample_rate, metrics, save_path, Path(args.input[0]).stem)

    else:
        if args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        # Multiple file analysis
        df = analyze_multiple_trials(args.input, args.cutoff, args.output_dir,
                                     analyze_spectrum=args.spectrum,
                                     analyze_cutoff=args.cutoff_analysis)
        print("\nAnalysis Summary:")
        print(df.to_string(index=False))


if __name__ == '__main__':
    main()
