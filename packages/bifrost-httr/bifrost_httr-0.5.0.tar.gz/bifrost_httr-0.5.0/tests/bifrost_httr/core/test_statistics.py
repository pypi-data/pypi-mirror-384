"""Tests for the statistics module."""

import numpy as np
import pandas as pd
import pytest

from bifrost_httr.core.statistics import (
    calc_pod_sample,
    calculate_global_pod,
    get_confidence_threshold_probability_density,
    get_response_window,
    interpolate_treatment_effect,
)


@pytest.fixture
def sample_response_data() -> dict[str, np.ndarray]:
    """Create sample response data for testing.

    This creates a simple dataset with:
    - 3 concentrations
    - 2 replicates per concentration
    - Known response pattern
    """
    return {
        "sigma": np.array([0.5, 0.7, 0.6]),  # Standard deviations
        "a": np.array([2.0, 2.5, 2.2]),  # Left tail parameters
        "b": np.array([3.0, 3.5, 3.2]),  # Right tail parameters
    }


@pytest.fixture
def sample_pod_data() -> tuple[np.ndarray, np.ndarray]:
    """Create sample data for testing PoD calculations.

    Returns:
        Tuple containing:
        - concentrations array
        - response array with a clear threshold crossing
    """
    conc = np.array([0.1, 1.0, 10.0, 100.0])
    response = np.array([0.1, 0.3, 0.7, 1.2])  # Crosses threshold around conc=10
    return conc, response


@pytest.fixture
def sample_treatment_data() -> dict[str, np.ndarray | int]:
    """Create sample data for testing treatment effect calculations."""
    n_conc = 3
    n_batch = 2

    return {
        "conc": np.array([1.0, 10.0, 100.0]),
        "total_count": np.array([1000, 1000, 1000]),
        "n_conc": n_conc,
        "n_batch": n_batch,
        "n_treatment_batch": n_batch,
    }


@pytest.fixture
def sample_treatment_samples() -> dict[str, np.ndarray]:
    """Create sample MCMC samples for testing treatment effect calculations."""
    n_samples = 100
    n_conc = 3

    return {
        "mu": np.random.normal(0, 0.1, size=(n_samples, n_conc)),
        "sigma": np.random.uniform(0.1, 0.5, size=n_samples),
        "a": np.random.uniform(1.5, 2.5, size=n_samples),
        "b": np.random.uniform(2.5, 3.5, size=n_samples),
        "treatment_response": np.random.normal(0, 0.1, size=(n_samples, n_conc)),
        "theta": np.random.uniform(0.1, 10.0, size=n_samples),
        "beta": np.random.uniform(0.1, 1.0, size=n_samples),
        "gamma": np.random.uniform(0.5, 1.5, size=n_samples),
        "rho": np.random.uniform(0.8, 1.2, size=n_samples),
    }


def test_get_response_window(sample_response_data: dict[str, np.ndarray]) -> None:
    """Test calculation of response windows."""
    # Calculate response windows
    result = get_response_window(sample_response_data)

    # Check that the function returns the expected keys
    assert "rtl" in result
    assert "rtu" in result

    # Check that the arrays have the right shape
    assert result["rtl"].shape == sample_response_data["sigma"].shape
    assert result["rtu"].shape == sample_response_data["sigma"].shape

    # Check that lower threshold is always less than upper threshold
    assert np.all(result["rtl"] < result["rtu"])

    # Check that the windows are roughly symmetric around 0 for symmetric parameters
    symmetric_data = {
        "sigma": np.array([1.0]),
        "a": np.array([2.0]),
        "b": np.array([2.0]),
    }
    symmetric_result = get_response_window(symmetric_data)
    assert (
        np.abs(np.abs(symmetric_result["rtl"]) - np.abs(symmetric_result["rtu"])) < 1e-6
    )


def test_calc_pod_sample(sample_pod_data: tuple[np.ndarray, np.ndarray]) -> None:
    """Test PoD calculation for a single sample."""
    conc, response = sample_pod_data
    lower_limit = 0.2
    upper_limit = 1.0

    # Test upward crossing
    pod = calc_pod_sample(conc, response, lower_limit, upper_limit)
    assert isinstance(pod, float)
    assert not np.isnan(pod)
    assert pod > conc[0]  # PoD should be after first concentration
    assert pod < conc[-1]  # PoD should be before last concentration

    # Test downward crossing
    response_down = -response
    pod_down = calc_pod_sample(conc, response_down, -upper_limit, -lower_limit)
    assert isinstance(pod_down, float)
    assert not np.isnan(pod_down)

    # Test no crossing (should return inf)
    response_no_cross = np.zeros_like(response)
    pod_no_cross = calc_pod_sample(conc, response_no_cross, lower_limit, upper_limit)
    assert np.isinf(pod_no_cross)


def test_get_confidence_threshold_probability_density() -> None:
    """Test calculation of confidence threshold probability density."""
    # Test basic properties
    x = np.linspace(0, 1.5, 1000)
    density = get_confidence_threshold_probability_density(x)

    # Check output type and shape
    assert isinstance(density, np.ndarray)
    assert density.shape == x.shape

    # Check that density is non-negative
    assert np.all(density >= 0)

    # Check that density is zero outside [threshold_lower, threshold_upper]
    assert np.all(density[x <= 0.5] == 0)
    assert np.all(density[x >= 1.0] == 0)

    # Check that density integrates to approximately 1 in valid range
    integral = np.trapezoid(
        density[np.where((x > 0.5) & (x < 1.0))],
        x[np.where((x > 0.5) & (x < 1.0))],
    )
    assert np.abs(integral - 1.0) < 1e-2


def test_interpolate_treatment_effect(
    sample_treatment_data: dict[str, np.ndarray | int],
    sample_treatment_samples: dict[str, np.ndarray],
) -> None:
    """Test calculation of treatment effects."""
    # Add response windows to samples
    samples = get_response_window(sample_treatment_samples)

    # Calculate treatment effects
    result = interpolate_treatment_effect(sample_treatment_data, samples)

    # Check that the function returns a pandas Series
    assert isinstance(result, pd.Series)

    # Check that all required keys are present
    required_keys = [
        "x",
        "response",
        "response_threshold_lower",
        "response_threshold_upper",
        "pod",
        "cds",
    ]
    for key in required_keys:
        assert key in result.index

    # Check that x values span the concentration range
    assert len(result["x"]) == 100  # Default interpolation points
    assert result["x"][0] <= min(sample_treatment_data["conc"])
    assert result["x"][-1] >= max(sample_treatment_data["conc"])

    # Check that response has correct shape (3 percentiles)
    assert result["response"].shape == (3, 100)

    # Check that CDS is between 0 and 1
    assert 0 <= result["cds"] <= 1


def test_calculate_global_pod() -> None:
    """Test calculation of global PoD."""
    # Create test data with log10-transformed PoD values
    max_conc = 100.0
    data = pd.Series(
        {
            "max_conc": np.log10(max_conc),  # Convert to log10 space
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

    # Calculate global PoD
    result = calculate_global_pod(data, data_type="summary")

    # Check that all required keys are present
    required_keys = [
        "global_pod",
        "num_hits",
        "means",
        "probes",
        "weights",
        "quantiles",
        "cds",
    ]
    for key in required_keys:
        assert key in result

    # Check that global_pod is a reasonable value
    assert isinstance(result["global_pod"], float)
    assert result["global_pod"] > 0
    assert result["global_pod"] < max_conc  # Compare with original max_conc

    # Check that num_hits is reasonable
    assert isinstance(result["num_hits"], (int | np.integer | float | np.floating))
    assert result["num_hits"] >= 0
    assert result["num_hits"] <= len(data["probes"])

    # Test with invalid data type
    with pytest.raises(
        ValueError,
        match="Unsupported data_type: invalid. Must be 'summary' or 'stats'",
    ):
        calculate_global_pod(data, data_type="invalid")

    # Test with missing required keys
    invalid_data = pd.Series({"max_conc": 100.0})
    with pytest.raises(KeyError):
        calculate_global_pod(invalid_data, data_type="summary")
