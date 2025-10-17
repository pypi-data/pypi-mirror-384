"""Tests for the visualization data module.

This module contains tests for the BifrostData and ProbeData classes in
bifrost_httr.visualization.data.
"""

import contextlib
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bifrost_httr.visualization.data import BifrostData, ProbeData


@pytest.fixture
def sample_bifrost_data() -> Path:
    """Create a sample BIFROST data file for testing."""
    # Create sample count data
    counts1 = [1000, 1200, 1500, 2000, 2500]  # Matches response values
    counts2 = [1000, 1100, 1300, 1800, 2200]  # Matches response values
    total_counts = [10000, 10000, 10000, 10000, 10000]  # Constant total counts

    # Create x values for response curves (same as conc values)
    x_values = [0.0, 0.1, 1.0, 10.0, 100.0]

    # Create sample diagnostic data
    diagnostics1 = (
        "Treedepth satisfactory\n"
        "No divergent transitions\n"
        "E-BFMI satisfactory\n"
        "effective sample size satisfactory\n"
        "Rank-normalized split R-hat values satisfactory for all parameters\n"
    )

    diagnostics2 = (
        "Treedepth satisfactory\n"
        "No divergent transitions\n"
        "E-BFMI satisfactory\n"
        "effective sample size satisfactory\n"
        "Rank-normalized split R-hat values satisfactory for all parameters\n"
    )

    data = {
        "probes": ["probe1", "probe2"],
        "max_conc": 100.0,
        "n_samp": 1000,
        "conc": x_values,
        "conc_index": [0, 1, 2, 3, 4],
        "total_count": total_counts,
        "probe1": {
            "pod": [5.0, 15.0, 25.0],  # Some sample POD values
            "cds": 0.8,
            "count": counts1,
            "x": x_values,
            "response": [
                [1.0, 1.1, 1.3, 1.7, 2.0],  # Lower CI
                [1.0, 1.2, 1.5, 2.0, 2.5],  # Median
                [1.0, 1.3, 1.7, 2.3, 3.0],  # Upper CI
            ],
            "diagnostics": diagnostics1,
            "response_threshold_lower": 1.0,
            "response_threshold_upper": 2.5,
        },
        "probe2": {
            "pod": [10.0, 20.0],
            "cds": 0.6,
            "count": counts2,
            "x": x_values,
            "response": [
                [1.0, 1.0, 1.2, 1.6, 1.9],  # Lower CI
                [1.0, 1.1, 1.3, 1.8, 2.2],  # Median
                [1.0, 1.2, 1.4, 2.0, 2.5],  # Upper CI
            ],
            "diagnostics": diagnostics2,
            "response_threshold_lower": 1.0,
            "response_threshold_upper": 2.2,
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Clean up the temporary file after the test
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def malformed_bifrost_data() -> Path:
    """Create a malformed BIFROST data file for testing error handling."""
    data = {
        "probes": ["probe1"],
        "max_conc": 100.0,
        "n_samp": 1000,
        # Missing required fields
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Clean up the temporary file after the test
    temp_path.unlink(missing_ok=True)


def test_bifrost_data_initialization(sample_bifrost_data: Path) -> None:
    """Test BifrostData initialization and basic attributes."""
    data = BifrostData(str(sample_bifrost_data))

    # Test basic attributes
    assert isinstance(data.df, pd.Series)
    assert isinstance(data.stats, dict)

    # Test stats contents
    assert set(data.stats.keys()) == {
        "probe",
        "pod",
        "cds",
        "l2fc",
        "max_conc",
        "n_samp",
        "conc",
        "_response_cache",
    }

    # Test specific values
    np.testing.assert_array_equal(data.stats["probe"], ["probe1", "probe2"])
    assert data.stats["max_conc"] == 100.0
    assert data.stats["n_samp"] == 1000
    np.testing.assert_array_equal(data.stats["conc"], [0.0, 0.1, 1.0, 10.0, 100.0])


def test_bifrost_data_initialization_errors(malformed_bifrost_data: Path) -> None:
    """Test error handling in BifrostData initialization."""
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        BifrostData("nonexistent_file.json")

    # Test malformed data
    with pytest.raises(KeyError):
        BifrostData(str(malformed_bifrost_data))


def test_bifrost_data_calculate_summary_statistics(sample_bifrost_data: Path) -> None:
    """Test calculation of summary statistics."""
    data = BifrostData(str(sample_bifrost_data))

    # Test POD means
    expected_pod_means = np.array([15.0, 15.0])  # mean of [5,15,25] and [10,20]
    np.testing.assert_array_almost_equal(data.stats["pod"], expected_pod_means)

    # Test CDS scores - using almost_equal for floating point comparison
    expected_cds = np.array([0.8, 0.6])
    np.testing.assert_array_almost_equal(data.stats["cds"], expected_cds)

    # Test log2 fold changes
    expected_l2fc = np.array(
        [
            np.log2(2.5 / 1.0),  # probe1: log2(max/min)
            np.log2(2.2 / 1.0),  # probe2: log2(max/min)
        ],
    )
    np.testing.assert_array_almost_equal(data.stats["l2fc"], expected_l2fc)


def test_bifrost_data_filter_summary_statistics(sample_bifrost_data: Path) -> None:
    """Test filtering of summary statistics based on CDS threshold."""
    data = BifrostData(str(sample_bifrost_data))

    # Filter with threshold that should only keep probe1
    filtered = data.filter_summary_statistics(0.7)
    assert len(filtered["probe"]) == 1
    assert filtered["probe"][0] == "probe1"
    assert filtered["cds"][0] == 0.8

    # Filter with threshold that should keep both probes
    filtered = data.filter_summary_statistics(0.5)
    assert len(filtered["probe"]) == 2
    np.testing.assert_array_equal(filtered["probe"], ["probe1", "probe2"])

    # Filter with threshold that should keep no probes
    filtered = data.filter_summary_statistics(0.9)
    assert len(filtered["probe"]) == 0


def test_bifrost_data_fit_pod_histogram(sample_bifrost_data: Path) -> None:
    """Test fitting of POD histogram."""
    # Create sample data
    pod_samples = np.array([1.0, 2.0, 2.0, 3.0, 3.0, 3.0])
    n_samp = 10

    data = BifrostData(str(sample_bifrost_data))
    weights, bin_edges = data.fit_pod_histogram(pod_samples, n_samp)

    # Test that weights sum to probability of response
    assert np.isclose(np.sum(weights), len(pod_samples) / n_samp)

    # Test handling of empty/invalid data
    weights, bin_edges = data.fit_pod_histogram(np.array([]), n_samp)
    assert weights is None
    assert bin_edges is None

    # Test handling of infinite values
    pod_samples_with_inf = np.array([1.0, 2.0, np.inf, 3.0])
    weights, bin_edges = data.fit_pod_histogram(pod_samples_with_inf, n_samp)
    assert weights is not None
    assert bin_edges is not None
    assert len(pod_samples_with_inf[~np.isinf(pod_samples_with_inf)]) == 3


def test_bifrost_data_create_summary_table_data(sample_bifrost_data: Path) -> None:
    """Test creation of summary table data."""
    data = BifrostData(str(sample_bifrost_data))

    # Create sample weights in the correct format
    weights = {
        "probe": np.array(["probe1", "probe2"]),
        "weight": np.array([0.6, 0.4]),
    }

    # Test without sorting
    table_data = data.create_summary_table_data(
        ["probe1", "probe2"],
        weights,
        "µM",
        sort_by_abs_fc=False,
    )

    assert isinstance(table_data, dict)
    assert "probe1" in table_data
    assert "probe2" in table_data

    # Test with sorting
    table_data_sorted = data.create_summary_table_data(
        ["probe1", "probe2"],
        weights,
        "µM",
        sort_by_abs_fc=True,
    )

    assert isinstance(table_data_sorted, dict)
    assert len(table_data_sorted) == 2


def test_bifrost_data_aggregate_probe_diagnostics(sample_bifrost_data: Path) -> None:
    """Test aggregation of probe diagnostics."""
    data = BifrostData(str(sample_bifrost_data))

    # Test with CDS threshold applied
    diagnostics = data.aggregate_probe_diagnostics(0.7, "µM", apply_cds_threshold=True)
    assert isinstance(diagnostics, dict)
    assert len(diagnostics) == 1  # Only probe1 should pass the threshold
    assert "probe1" in diagnostics

    # Test without CDS threshold
    diagnostics = data.aggregate_probe_diagnostics(0.7, "µM", apply_cds_threshold=False)
    assert isinstance(diagnostics, dict)
    assert len(diagnostics) == 2  # Both probes should be included
    assert "probe1" in diagnostics
    assert "probe2" in diagnostics

    # Verify diagnostic data structure
    for diag in diagnostics.values():
        assert isinstance(diag, dict)
        assert "CDS" in diag
        assert "Mean PoD" in diag
        assert "Treedepth" in diag
        assert "Divergences" in diag
        assert "E-BFMI" in diag
        assert "ESS" in diag
        assert "R-hat" in diag


def test_probe_data_initialization(sample_bifrost_data: Path) -> None:
    """Test ProbeData initialization and basic properties."""
    bifrost_data = BifrostData(str(sample_bifrost_data))
    probe_data = ProbeData(
        bifrost_data.df,
        "probe1",
        "µM",
        bifrost_data,
    )

    # Test basic properties
    assert probe_data.cds == 0.8
    assert probe_data.mean_pod == 15.0

    # Test response data
    treatment_x, treatment_y, control_y, response_x, response = (
        probe_data.get_response_data()
    )

    # Test treatment concentrations (excludes control at index 0)
    # conc_index[treatment_mask] - 1 gives [0, 1, 2, 3] which selects from conc
    expected_treatment_x = 10 ** np.array([0.0, 0.1, 1.0, 10.0])
    np.testing.assert_array_almost_equal(treatment_x, expected_treatment_x)

    # Test treatment response (normalized counts)
    expected_treatment_y = (
        np.array([1200, 1500, 2000, 2500]) / 10000 * 10000
    )  # Using median_total_count
    np.testing.assert_array_almost_equal(treatment_y, expected_treatment_y)

    # Test control response
    expected_control_y = np.array([1000]) / 10000 * 10000  # Using median_total_count
    np.testing.assert_array_almost_equal(control_y, expected_control_y)

    # Test response curve x values
    expected_response_x = 10 ** np.array([0.0, 0.1, 1.0, 10.0, 100.0])
    np.testing.assert_array_almost_equal(response_x, expected_response_x)

    # Test response curve values
    expected_response = np.array(
        [
            [1.0, 1.1, 1.3, 1.7, 2.0],  # Lower CI
            [1.0, 1.2, 1.5, 2.0, 2.5],  # Median
            [1.0, 1.3, 1.7, 2.3, 3.0],  # Upper CI
        ],
    )
    np.testing.assert_array_almost_equal(response, expected_response)


def test_probe_data_initialization_errors(sample_bifrost_data: Path) -> None:
    """Test error handling in ProbeData initialization."""
    bifrost_data = BifrostData(str(sample_bifrost_data))

    # Test non-existent probe
    with pytest.raises(KeyError):
        ProbeData(bifrost_data.df, "nonexistent_probe", "µM", bifrost_data)


def test_probe_data_pod_percentiles(sample_bifrost_data: Path) -> None:
    """Test POD percentiles calculation."""
    bifrost_data = BifrostData(str(sample_bifrost_data))
    probe_data = ProbeData(
        bifrost_data.df,
        "probe1",
        "µM",
        bifrost_data,
    )

    # Test POD percentiles
    percentiles = probe_data.pod_percentiles
    assert percentiles is not None

    # Unpack the percentiles tuple
    pod_values, percentile_indices, percentile_values, percentile_labels = percentiles

    # Test that we got the expected components
    assert isinstance(pod_values, np.ndarray)
    assert isinstance(percentile_indices, list)
    assert isinstance(percentile_values, list)
    assert isinstance(percentile_labels, list)

    # Test that the values make sense
    assert len(pod_values) > 0
    assert len(percentile_indices) == len(percentile_values)
    assert len(percentile_indices) == len(percentile_labels)


def test_probe_data_create_probe_plot(sample_bifrost_data: Path) -> None:
    """Test creation of probe plot."""
    bifrost_data = BifrostData(str(sample_bifrost_data))
    probe_data = ProbeData(
        bifrost_data.df,
        "probe1",
        "µM",
        bifrost_data,
    )

    # Test plot creation
    plot_html = probe_data.create_probe_plot()
    assert isinstance(plot_html, str)
    assert len(plot_html) > 0
    assert "plotly" in plot_html.lower()  # Should contain plotly-related content


def test_probe_data_get_diagnostic_data(sample_bifrost_data: Path) -> None:
    """Test retrieval of probe diagnostic data."""
    bifrost_data = BifrostData(str(sample_bifrost_data))
    probe_data = ProbeData(
        bifrost_data.df,
        "probe1",
        "µM",
        bifrost_data,
    )

    # Test with CDS threshold applied
    diagnostics = probe_data.get_diagnostic_data(0.7, apply_cds_threshold=True)
    assert isinstance(diagnostics, dict)
    assert len(diagnostics) > 0
    assert "probe1" in diagnostics

    # Verify diagnostic data structure
    probe_diag = diagnostics["probe1"]
    assert "CDS" in probe_diag
    assert "Mean PoD" in probe_diag
    assert "Treedepth" in probe_diag
    assert "Divergences" in probe_diag
    assert "E-BFMI" in probe_diag
    assert "ESS" in probe_diag
    assert "R-hat" in probe_diag

    # Test without CDS threshold
    diagnostics = probe_data.get_diagnostic_data(0.7, apply_cds_threshold=False)
    assert isinstance(diagnostics, dict)
    assert len(diagnostics) > 0
    assert "probe1" in diagnostics

    # Test with CDS threshold that excludes the probe
    diagnostics = probe_data.get_diagnostic_data(0.9, apply_cds_threshold=True)
    assert isinstance(diagnostics, dict)
    assert len(diagnostics) == 0


def teardown_module() -> None:
    """Clean up temporary files after tests."""
    # Clean up any .json files in the temporary directory
    temp_dir = Path(tempfile.gettempdir())
    for f in temp_dir.glob("*.json"):
        with contextlib.suppress(OSError):
            f.unlink()
