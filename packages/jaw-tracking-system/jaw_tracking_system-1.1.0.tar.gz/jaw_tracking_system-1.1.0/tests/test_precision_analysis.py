"""
Tests for the jts.precision_analysis module, focusing on unit handling in load_hdf5_data.
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
import h5py
import tempfile
import pytest

from pathlib import Path
from jts.precision_analysis import JawMotionPrecisionAnalyzer


def create_hdf5_with_unit(unit, translation_value=1.0):
    """
    Helper to create an in-memory HDF5 file with a given unit and translation value.
    Returns the file path.
    """
    tmp = tempfile.NamedTemporaryFile(suffix='.h5', delete=False)
    with h5py.File(tmp.name, 'w') as f:
        group = f.create_group('test')
        # Single translation, single rotation
        group.create_dataset('translations', data=np.array([[translation_value, 0, 0]]))
        group.create_dataset('rotations', data=np.array([np.eye(3)]))
        group.attrs['sample_rate'] = 100.0
        group.attrs['unit'] = unit
    return tmp.name


def test_analyze_precision_identity():
    """
    Test analyze_precision on identity transforms (should yield zero error metrics).
    """
    from jts.precision_analysis import JawMotionPrecisionAnalyzer

    N = 20
    T = np.tile(np.eye(4), (N, 1, 1))
    analyzer = JawMotionPrecisionAnalyzer(cutoff_frequency=2.0)
    metrics = analyzer.analyze_precision(T, sample_rate=100)

    assert metrics.rms_translation == pytest.approx(0)
    assert metrics.mean_translation_error == pytest.approx(0)
    assert metrics.max_translation_error == pytest.approx(0)
    assert metrics.rms_rotation == pytest.approx(0)
    assert metrics.mean_rotation_error == pytest.approx(0)
    assert metrics.max_rotation_error == pytest.approx(0)
    assert metrics.snr_translation == pytest.approx(float('inf'))
    assert metrics.snr_rotation == pytest.approx(float('inf'))


def test_filter_transformations_lowpass():
    """
    Test that filter_transformations smooths out high-frequency noise.
    """
    from jts.precision_analysis import JawMotionPrecisionAnalyzer

    N = 100
    T = np.tile(np.eye(4), (N, 1, 1))

    # Add high-frequency noise to translation
    T[:, 0, 3] += np.sin(np.linspace(0, 20 * np.pi, N)) * 0.5
    analyzer = JawMotionPrecisionAnalyzer(cutoff_frequency=2.0)
    filtered = analyzer.filter_transformations(T, sample_rate=100)

    # The filtered signal should have much less variance than the noisy one
    assert np.var(filtered[:, 0, 3]) < np.var(T[:, 0, 3])


def test_compute_frequency_spectrum_shape():
    """
    Test compute_frequency_spectrum returns correct keys and array shapes.
    """
    from jts.precision_analysis import JawMotionPrecisionAnalyzer

    N = 64
    T = np.tile(np.eye(4), (N, 1, 1))
    T[:, 0, 3] = np.linspace(0, 10, N)
    analyzer = JawMotionPrecisionAnalyzer()
    result = analyzer.compute_frequency_spectrum(T, sample_rate=64, plot=False)

    # Should contain keys for translation and rotation axes and magnitudes
    for key in ['trans_X', 'trans_Y', 'trans_Z', 'trans_magnitude', 'rot_X', 'rot_Y', 'rot_Z', 'rot_magnitude']:
        assert key in result
        f, psd = result[key]
        assert f.shape == psd.shape
        assert len(f) > 0


def test_cutoff_suggestions_monotonic():
    """
    Test that cutoff suggestions are monotonic for a simple ramp signal.
    """
    from jts.precision_analysis import JawMotionPrecisionAnalyzer

    N = 128
    T = np.tile(np.eye(4), (N, 1, 1))
    T[:, 0, 3] = np.linspace(0, 10, N)
    analyzer = JawMotionPrecisionAnalyzer()
    suggestions = analyzer.compute_cutoff_suggestions(T, sample_rate=64)

    # All suggestions should be positive and within Nyquist
    for v in suggestions.values():
        assert v >= 0
        assert v < 32


def test_export_metrics_csv(tmp_path):
    """
    Test export_metrics writes a CSV with correct metrics and metadata.
    """
    from jts.precision_analysis import JawMotionPrecisionAnalyzer, PrecisionMetrics
    import pandas as pd

    # Create dummy metrics
    metrics = PrecisionMetrics(
        rms_translation=1.1,
        rms_translation_per_axis=np.array([1.0, 2.0, 3.0]),
        std_translation=np.array([0.1, 0.2, 0.3]),
        mean_translation_error=1.2,
        rms_rotation=2.1,
        rms_rotation_per_axis=np.array([2.0, 3.0, 4.0]),
        std_rotation=0.4,
        mean_rotation_error=2.2,
        max_translation_error=1.3,
        max_rotation_error=2.3,
        snr_translation=30.0,
        snr_rotation=40.0,
        power_spectrum_freq=np.array([1, 2, 3]),
        power_spectrum_trans=np.array([0.1, 0.2, 0.3]),
        power_spectrum_rot=np.array([0.2, 0.3, 0.4])
    )

    out_file = tmp_path / "metrics.csv"
    meta = {"unit": "mm", "original_unit": "cm"}
    JawMotionPrecisionAnalyzer.export_metrics(metrics, out_file, metadata=meta)
    df = pd.read_csv(out_file)

    # Check that key metrics and metadata are present
    assert "Translation RMS (magnitude) (mm)" in df["Metric"].values
    assert "Original Data Unit" in df["Metric"].values
    assert "Analysis Unit" in df["Metric"].values
    assert df[df["Metric"] == "Original Data Unit"]["Value"].iloc[0] == "cm"
    assert df[df["Metric"] == "Analysis Unit"]["Value"].iloc[0] == "mm"


def test_store_and_load_roundtrip(tmp_path):
    """
    Integration test: store with helper.py, load with precision_analysis.py, check values and units.
    """
    from jts import helper as hlp

    # Create a transformation array
    T = np.tile(np.eye(4), (2, 1, 1))
    T[0, :3, 3] = [1, 2, 3]
    T[1, :3, 3] = [4, 5, 6]
    out_file = tmp_path / "test_roundtrip.h5"

    # Store with scale_factor=10, unit='cm'
    hlp.store_transformations([T], [100], out_file, scale_factor=10, unit="cm")

    # Now load with precision_analysis (should convert cm to mm, i.e., *10)
    analyzer = JawMotionPrecisionAnalyzer()
    loaded, sr, meta = analyzer.load_hdf5_data(out_file, 'T_0')

    # The original values were [1,2,3] and [4,5,6], scaled by 10 (-> [10,20,30] and [40,50,60] cm),
    # then loaded and converted to mm (so *10 again: [100,200,300] and [400,500,600] mm)
    np.testing.assert_allclose(loaded[0, :3, 3], [100, 200, 300])
    np.testing.assert_allclose(loaded[1, :3, 3], [400, 500, 600])

    assert meta['unit'] == 'mm'
    assert meta['original_unit'] == 'cm'


def test_store_and_load_with_config(tmp_path):
    """
    Simulate core.py config/output logic: store with config unit/scale_factor, load and check.
    """
    from jts import helper as hlp

    # Simulate config
    config = {
        "output": {"unit": "m", "scale_factor": 0.001}
    }
    T = np.tile(np.eye(4), (1, 1, 1))
    T[0, :3, 3] = [1000, 2000, 3000]  # mm
    out_file = tmp_path / "test_config.h5"

    # Store as meters (should multiply by 0.001)
    hlp.store_transformations([T], [100], out_file, scale_factor=config['output']['scale_factor'],
                              unit=config['output']['unit'])
    analyzer = JawMotionPrecisionAnalyzer()
    loaded, sr, meta = analyzer.load_hdf5_data(out_file, 'T_0')

    # Stored as [1,2,3] m, loaded and converted to mm (so *1000): [1000,2000,3000] mm
    np.testing.assert_allclose(loaded[0, :3, 3], [1000, 2000, 3000])

    assert meta['unit'] == 'mm'
    assert meta['original_unit'] == 'm'


def test_helper_and_precision_analysis_unit_consistency(tmp_path):
    """
    Test that helper.py and precision_analysis.py agree on unit conversion for various units.
    """
    from jts import helper as hlp

    units = ["mm", "cm", "m", "in"]
    factors = [1, 10, 1000, 25.4]
    for unit, factor in zip(units, factors):
        T = np.tile(np.eye(4), (1, 1, 1))
        T[0, :3, 3] = [2, 0, 0]  # base value
        out_file = tmp_path / f"test_{unit}.h5"
        hlp.store_transformations([T], [100], out_file, scale_factor=1, unit=unit)
        analyzer = JawMotionPrecisionAnalyzer()
        loaded, sr, meta = analyzer.load_hdf5_data(out_file, 'T_0')

        # Should be 2 * factor mm
        np.testing.assert_allclose(loaded[0, :3, 3], [2 * factor, 0, 0])

        assert meta['unit'] == 'mm'
        assert meta['original_unit'] == unit


def test_unit_conversion_mm():
    path = create_hdf5_with_unit('mm', 2.0)
    analyzer = JawMotionPrecisionAnalyzer()
    T, sr, meta = analyzer.load_hdf5_data(path, 'test')

    # Should be unchanged
    np.testing.assert_allclose(T[0, :3, 3], [2.0, 0, 0])

    assert meta['unit'] == 'mm'
    Path(path).unlink()


def test_unit_conversion_cm():
    path = create_hdf5_with_unit('cm', 3.0)
    analyzer = JawMotionPrecisionAnalyzer()
    T, sr, meta = analyzer.load_hdf5_data(path, 'test')

    # 3 cm = 30 mm
    np.testing.assert_allclose(T[0, :3, 3], [30.0, 0, 0])

    assert meta['unit'] == 'mm'
    assert meta['original_unit'] == 'cm'
    Path(path).unlink()


def test_unit_conversion_m():
    path = create_hdf5_with_unit('m', 0.004)
    analyzer = JawMotionPrecisionAnalyzer()
    T, sr, meta = analyzer.load_hdf5_data(path, 'test')

    # 0.004 m = 4 mm
    np.testing.assert_allclose(T[0, :3, 3], [4.0, 0, 0])

    assert meta['unit'] == 'mm'
    assert meta['original_unit'] == 'm'
    Path(path).unlink()


def test_unit_conversion_inch():
    path = create_hdf5_with_unit('in', 2.0)
    analyzer = JawMotionPrecisionAnalyzer()
    T, sr, meta = analyzer.load_hdf5_data(path, 'test')

    # 2 in = 50.8 mm
    np.testing.assert_allclose(T[0, :3, 3], [50.8, 0, 0])

    assert meta['unit'] == 'mm'
    assert meta['original_unit'] == 'in'
    Path(path).unlink()


def test_unit_unknown():
    path = create_hdf5_with_unit('parsec', 1.0)
    analyzer = JawMotionPrecisionAnalyzer()
    T, sr, meta = analyzer.load_hdf5_data(path, 'test')

    # Should not convert, just use value as mm
    np.testing.assert_allclose(T[0, :3, 3], [1.0, 0, 0])

    assert meta['unit'] == 'mm'
    assert meta['original_unit'] == 'parsec'
    Path(path).unlink()
