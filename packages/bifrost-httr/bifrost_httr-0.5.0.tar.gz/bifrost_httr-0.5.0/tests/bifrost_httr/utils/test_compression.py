"""Tests for compression utilities."""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bifrost_httr.utils.compression import compress_output, get_global_pod


@pytest.fixture
def sample_bifrost_data(tmp_path: Path) -> tuple[Path, Path]:
    """Create sample BIFROST data files for testing.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        Tuple containing:
        - Path to analysis directory
        - Path to summary file
    """
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()
    summary_path = tmp_path / "summary.json"

    # Create sample data for two probes
    probes = ["probe1", "probe2"]
    n_conc = 3
    n_batch = 2
    n_samp = 100

    base_data = {
        "n_samp": n_samp,
        "n_sample": n_conc * n_batch,
        "n_treatment_batch": n_batch,
        "total_count": np.array([1000] * n_conc),
        "n_batch": n_batch,
        "batch_index": np.array([1, 1, 2, 2, 3, 3]),
        "n_conc": n_conc,
        "conc": np.array([1.0, 10.0, 100.0]),
        "conc_index": np.array([1, 1, 2, 2, 3, 3]),
        "max_conc": np.log10(100.0),
    }

    # Create probe-specific data
    for probe in probes:
        probe_data = base_data.copy()
        probe_data.update(
            {
                "diagnostics": "No divergent transitions found",
                "parameters": {"mu": 0.0, "sigma": 1.0},
                "fit": pd.Series(
                    {
                        "pod": np.array([5.0, 7.0, 10.0]),
                        "cds": 0.7,
                        "weights": np.array([0.3, 0.4, 0.3]),
                    },
                ),
                "count": np.array([100, 200, 300]),
            },
        )

        with (analysis_dir / f"{probe}.pkl").open("wb") as f:
            pickle.dump(probe_data, f)

    return analysis_dir, summary_path


def test_get_global_pod() -> None:
    """Test get_global_pod function."""
    # Create test data
    data = pd.Series(
        {
            "max_conc": np.log10(100.0),
            "probes": ["probe1", "probe2"],
            "probe1": {
                "pod": np.array([0.7, 0.85, 1.0]),  # log10([5, 7, 10])
                "cds": 0.7,
                "weights": np.array([0.3, 0.4, 0.3]),
            },
            "probe2": {
                "pod": np.array([0.9, 1.08, 1.18]),  # log10([8, 12, 15])
                "cds": 0.8,
                "weights": np.array([0.3, 0.4, 0.3]),
            },
        },
    )

    # Test without seed
    result = get_global_pod(data)
    assert isinstance(result, dict)
    assert "global_pod" in result
    assert "num_hits" in result
    assert result["global_pod"] > 0
    assert result["global_pod"] < 100.0  # Should be less than max_conc

    # Test with seed
    result_seeded = get_global_pod(data, seed=42)
    assert isinstance(result_seeded, dict)
    assert result_seeded["global_pod"] > 0


def test_compress_output_basic(sample_bifrost_data: tuple[Path, Path]) -> None:
    """Test basic compress_output functionality."""
    analysis_dir, summary_path = sample_bifrost_data

    # Test with default settings
    compress_output(analysis_dir, summary_path)
    assert summary_path.exists()
    assert summary_path.stat().st_size > 0

    # Load and verify the compressed output
    summary = pd.read_json(summary_path, orient="index", compression="zip")
    assert isinstance(summary, pd.DataFrame)
    assert "probes" in summary.index
    assert "global_pod_dict" in summary.index

    # Check probes list - it's stored as a nested array
    probes_data = summary.loc["probes"].to_numpy()[
        0
    ]  # Get the first (and only) element
    assert isinstance(probes_data, list)
    assert len(probes_data) == 2  # Two probes
    assert all(p in probes_data for p in ["probe1", "probe2"])


def test_compress_output_no_compression(sample_bifrost_data: tuple[Path, Path]) -> None:
    """Test compress_output with no_compression=True."""
    analysis_dir, summary_path = sample_bifrost_data

    # Test with no compression
    compress_output(analysis_dir, summary_path, no_compression=True)
    assert summary_path.exists()
    assert summary_path.suffix == ".json"

    # Load and verify the uncompressed output
    summary = pd.read_json(summary_path, orient="index")
    assert isinstance(summary, pd.DataFrame)
    assert "probes" in summary.index


def test_compress_output_with_seed(sample_bifrost_data: tuple[Path, Path]) -> None:
    """Test compress_output with random seed."""
    analysis_dir, summary_path = sample_bifrost_data

    # Test with seed
    compress_output(analysis_dir, summary_path, seed=42)
    assert summary_path.exists()

    # Run again with same seed
    summary_path_2 = summary_path.parent / "summary2.json"
    compress_output(analysis_dir, summary_path_2, seed=42)

    # Load both outputs and compare global_pod_dict
    summary1 = pd.read_json(summary_path, orient="index", compression="zip")
    summary2 = pd.read_json(summary_path_2, orient="index", compression="zip")
    assert summary1.loc["global_pod_dict"].equals(summary2.loc["global_pod_dict"])


def test_compress_output_errors(tmp_path: Path) -> None:
    """Test error handling in compress_output."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    summary_path = tmp_path / "summary.json"

    # Test with directory containing no .pkl files
    with pytest.raises(ValueError, match="No .pkl files found in"):
        compress_output(empty_dir, summary_path)

    # Test with non-existent directory
    with pytest.raises(ValueError, match="No .pkl files found in"):
        compress_output(tmp_path / "nonexistent", summary_path)


def test_compress_output_meta_incluson(tmp_path: Path, sample_bifrost_data) -> None:
    """Test basic compress_output functionality."""
    analysis_dir, summary_path = sample_bifrost_data

    test_substance = "MyChem"
    cell_type = "MyCell"

    # Test with default settings
    compress_output(analysis_dir, summary_path, test_substance, cell_type)

    summary = pd.read_json(summary_path, typ='series', orient="index", compression="zip")

    assert "meta" in summary.index
    assert summary["meta"]["Test substance"] == "MyChem"
    assert summary["meta"]["Cell type"] == "MyCell"