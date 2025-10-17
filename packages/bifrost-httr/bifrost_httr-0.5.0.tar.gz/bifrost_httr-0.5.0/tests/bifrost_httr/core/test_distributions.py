"""Tests for the distributions module."""

import numpy as np
import pytest

from bifrost_httr.core.distributions import BetaLogistic


@pytest.fixture
def sample_distribution() -> BetaLogistic:
    """Create a sample BetaLogistic distribution for testing.

    This creates a distribution with reasonable parameters that should
    exhibit both left and right skewness.
    """
    return BetaLogistic(mu=0.0, sigma=1.0, a=2.0, b=3.0)


def test_initialization() -> None:
    """Test initialization of BetaLogistic distribution."""
    # Test with valid parameters
    dist = BetaLogistic(mu=0.0, sigma=1.0, a=2.0, b=3.0)
    assert isinstance(dist, BetaLogistic)
    assert dist.mu == 0.0
    assert dist.sigma == 1.0
    assert dist.a == 2.0
    assert dist.b == 3.0

    # Test that m and s are computed correctly
    assert isinstance(dist.m, float)
    assert isinstance(dist.s, float)
    assert not np.isnan(dist.m)
    assert not np.isnan(dist.s)


def test_cdf_scalar(sample_distribution: BetaLogistic) -> None:
    """Test CDF computation with scalar input."""
    # Test basic properties
    assert sample_distribution.cdf(-np.inf) == 0.0
    assert sample_distribution.cdf(np.inf) == 1.0

    # Test monotonicity
    x_values = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    cdf_values = [sample_distribution.cdf(x) for x in x_values]
    assert np.all(np.diff(cdf_values) >= 0)  # Should be monotonically increasing


def test_cdf_array(sample_distribution: BetaLogistic) -> None:
    """Test CDF computation with array input."""
    x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    cdf_values = sample_distribution.cdf(x)

    # Test output type and shape
    assert isinstance(cdf_values, np.ndarray)
    assert cdf_values.shape == x.shape

    # Test values are in [0,1]
    assert np.all((cdf_values >= 0) & (cdf_values <= 1))


def test_ppf_scalar(sample_distribution: BetaLogistic) -> None:
    """Test PPF (inverse CDF) computation with scalar input."""
    # Test basic properties
    q_values = [0.1, 0.25, 0.5, 0.75, 0.9]
    for q in q_values:
        x = sample_distribution.ppf(q)
        # Check that PPF(CDF(x)) ≈ x
        assert np.abs(sample_distribution.cdf(x) - q) < 1e-6


def test_ppf_edge_cases(sample_distribution: BetaLogistic) -> None:
    """Test PPF computation with edge cases."""
    # Test values very close to 0 and 1
    small_q = 1e-6
    large_q = 1 - small_q

    x_small = sample_distribution.ppf(small_q)
    x_large = sample_distribution.ppf(large_q)

    assert (
        sample_distribution.cdf(x_small) <= small_q * 1.1
    )  # Allow 10% error for numerical stability
    assert (
        sample_distribution.cdf(x_large) >= large_q * 0.9
    )  # Allow 10% error for numerical stability


def test_pdf_scalar(sample_distribution: BetaLogistic) -> None:
    """Test PDF computation with scalar input."""
    # Test basic properties
    x_values = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    pdf_values = [sample_distribution.pdf(x) for x in x_values]

    # PDF should be non-negative
    assert np.all(np.array(pdf_values) >= 0)

    # PDF should integrate to approximately 1
    x_fine = np.linspace(-10, 10, 1000)
    pdf_fine = sample_distribution.pdf(x_fine)
    integral = np.trapezoid(pdf_fine, x_fine)
    assert np.abs(integral - 1.0) < 1e-2


def test_pdf_array(sample_distribution: BetaLogistic) -> None:
    """Test PDF computation with array input."""
    x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    pdf_values = sample_distribution.pdf(x)

    # Test output type and shape
    assert isinstance(pdf_values, np.ndarray)
    assert pdf_values.shape == x.shape

    # Test values are non-negative
    assert np.all(pdf_values >= 0)


def test_logpdf_scalar(sample_distribution: BetaLogistic) -> None:
    """Test log PDF computation with scalar input."""
    x_values = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])

    # Compare with log of PDF
    for x in x_values:
        logpdf = sample_distribution.logpdf(x)
        pdf = sample_distribution.pdf(x)
        assert np.abs(logpdf - np.log(pdf)) < 1e-10


def test_logpdf_array(sample_distribution: BetaLogistic) -> None:
    """Test log PDF computation with array input."""
    x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    logpdf_values = sample_distribution.logpdf(x)

    # Test output type and shape
    assert isinstance(logpdf_values, np.ndarray)
    assert logpdf_values.shape == x.shape

    # Compare with log of PDF values
    pdf_values = sample_distribution.pdf(x)
    assert np.allclose(logpdf_values, np.log(pdf_values))


def test_distribution_properties(sample_distribution: BetaLogistic) -> None:
    """Test statistical properties of the distribution."""
    # Generate samples using PPF
    q = np.linspace(0.01, 0.99, 1000)
    np.array([sample_distribution.ppf(qi) for qi in q])

    # Test symmetry for symmetric parameters
    symmetric_dist = BetaLogistic(mu=0.0, sigma=1.0, a=2.0, b=2.0)
    q_symmetric = np.linspace(0.01, 0.99, 1000)
    samples_symmetric = np.array([symmetric_dist.ppf(qi) for qi in q_symmetric])

    # For symmetric distribution, mean should be close to mu
    assert np.abs(np.mean(samples_symmetric)) < 0.1  # Allow some numerical error
