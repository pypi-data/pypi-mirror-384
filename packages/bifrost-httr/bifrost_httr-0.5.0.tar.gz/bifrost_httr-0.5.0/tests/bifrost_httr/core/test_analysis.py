"""Tests for the analysis module.

This test suite covers the core analysis functionality of the BIFROST package,
focusing on concentration response analysis and data processing. The tests use
a combination of mocking and fixtures to isolate the components being tested.

Key testing strategies used:
1. Mock functions for external dependencies (e.g., model fitting, interpolation)
2. Fixtures for common test data to ensure consistency
3. Temporary directories (via pytest's tmp_path) for file I/O tests
4. Edge case testing for error handling and boundary conditions
"""

import pickle
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from bifrost_httr.core.analysis import (
    gen_plotting_data,
    run_concentration_response_analysis,
    standard_analysis,
)


def mock_standard_analysis(paths: tuple[str | Path, ...]) -> None:
    """Mock function for standard_analysis that can be pickled.

    This function is defined at module level (not inside a test) because
    functions used with multiprocessing must be picklable. Inner functions
    or lambdas cannot be pickled.
    """
    # Extract paths from the tuple
    _, _, path_to_fit, _, _ = paths

    # Create an empty output file
    with Path(path_to_fit).open("wb") as f:
        pickle.dump({"test": "data"}, f)


@pytest.fixture
def sample_data() -> dict[str, np.ndarray | int]:
    """Create sample data for testing.

    Returns a dictionary with typical concentration-response data structure:
    - conc: Concentration levels
    - n_conc: Number of concentrations
    - n_rep: Number of replicates
    - n_time: Number of time points
    - y: Response data array (shape: concentrations x replicates x timepoints)
    - total_count: Total counts per concentration
    """
    return {
        "conc": np.array([0.1, 1.0, 10.0]),
        "n_conc": 3,
        "n_rep": 2,
        "n_time": 5,
        "y": np.random.normal(size=(3, 2, 5)),
        "total_count": np.array([1000, 1000, 1000]),
        "n_batch": 2,
        "n_sample": 6,
        "n_samp": 1000,
    }


@pytest.fixture
def sample_samples() -> dict[str, np.ndarray]:
    """Create sample posterior samples for testing.

    Returns a dictionary simulating MCMC samples from a Stan model with:
    - lp__: Log probability values
    - mu, sigma: Location and scale parameters
    - a, b: Slope and intercept parameters
    - treatment_response: Response values per concentration
    - theta, beta, gamma, rho: Additional model parameters

    Each parameter has 100 samples to simulate a typical MCMC chain.
    """
    n_samples = 100
    return {
        "mu": np.random.normal(size=(n_samples, 3)),
        "sigma": np.abs(np.random.normal(size=n_samples)),
        "a": np.random.normal(size=n_samples),
        "b": np.random.normal(size=n_samples),
        "log_odds": np.random.normal(size=n_samples),
        "treatment_response": np.random.normal(size=(n_samples, 3)),
        "theta": np.random.normal(size=n_samples),
        "beta": np.random.normal(size=n_samples),
        "gamma": np.random.normal(size=n_samples),
        "rho": np.random.normal(size=n_samples),
    }


def test_run_concentration_response_analysis_invalid_fit_dir() -> None:
    """Test that invalid fit_dir raises ValueError.

    This test verifies that the function properly validates its input parameters
    by checking that a non-string, non-Path fit_dir argument raises an error.
    """
    with pytest.raises(
        ValueError,
        match="Directory to contain model fits must be specified as a string or Path",
    ):
        run_concentration_response_analysis(
            files_to_process=["test.pkl"],
            model_executable="model.exe",
            number_of_cores=1,
            fit_dir=123,  # Invalid type
        )


def test_run_concentration_response_analysis_missing_file() -> None:
    """Test that missing input file raises FileNotFoundError.

    Verifies that the function properly checks for file existence before
    attempting to process them.
    """
    with pytest.raises(FileNotFoundError):
        run_concentration_response_analysis(
            files_to_process=["nonexistent.pkl"],
            model_executable="model.exe",
            number_of_cores=1,
        )


def test_run_concentration_response_analysis_success(tmp_path: Path) -> None:
    """Test successful execution of concentration response analysis.

    This test:
    1. Creates a temporary pickle file with test data
    2. Patches the standard_analysis function to avoid actual computation
    3. Verifies that the output directory is created as expected

    The tmp_path fixture provides a temporary directory that is automatically
    cleaned up after the test.
    """
    # Create a temporary pickle file with sample data
    data_file = tmp_path / "test_data.pkl"
    with data_file.open("wb") as f:
        pickle.dump({"test": "data"}, f)

    # Run the analysis with the mock function
    with patch("bifrost_httr.core.analysis.standard_analysis", mock_standard_analysis):
        run_concentration_response_analysis(
            files_to_process=[str(data_file)],
            model_executable="model.exe",
            number_of_cores=1,
            fit_dir=tmp_path,
        )

    # Check that output directory exists
    assert (tmp_path / "Fits").exists()


@patch("bifrost_httr.core.analysis.fit_model")
@patch("bifrost_httr.core.analysis.get_response_window")
@patch("bifrost_httr.core.analysis.interpolate_treatment_effect")
def test_standard_analysis(
    mock_interpolate: MagicMock,
    mock_response_window: MagicMock,
    mock_fit_model: MagicMock,
    tmp_path: Path,
) -> None:
    """Test standard analysis function.

    This test uses multiple patches to isolate the standard_analysis function:
    1. mock_fit_model: Simulates the Stan model fitting
    2. mock_response_window: Simulates response window calculation
    3. mock_interpolate: Simulates treatment effect interpolation

    The test verifies that:
    1. Input data is properly processed
    2. Output files are created
    3. Output data contains all expected parameters
    """
    # Create simple test data
    test_data = {
        "conc": np.array([1.0, 2.0, 3.0]),
        "total_count": np.array([100, 100, 100]),
        "n_conc": 3,
        "n_batch": 2,
        "n_sample": 6,
        "n_samp": 1000,
    }

    # Create input data file
    input_file = tmp_path / "input.pkl"
    with input_file.open("wb") as f:
        pickle.dump(test_data, f)

    # Create output file path
    output_file = tmp_path / "output.pkl"

    # Set up mock returns
    mock_samples = {
        "mu": np.array([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]),
        "sigma": np.array([0.1, 0.2]),
        "a": np.array([0.1, 0.2]),
        "b": np.array([0.3, 0.4]),
        "log_odds": np.array([0.0, 0.1]),
        "treatment_response": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
        "theta": np.array([1.0, 1.1]),
        "beta": np.array([0.5, 0.6]),
        "gamma": np.array([0.7, 0.8]),
        "rho": np.array([0.9, 1.0]),
        "rtl": np.array([0.1, 0.2]),
        "rtu": np.array([1.8, 1.9]),
    }

    mock_fit_model.return_value = {
        "samples": mock_samples,
        "diagnostics": "Test diagnostics",
    }

    mock_response_window.return_value = mock_samples
    mock_interpolate.return_value = pd.Series(
        {
            "x": np.array([1, 2, 3]),
            "response": np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
            "response_threshold_lower": 0.5,
            "response_threshold_upper": 1.5,
            "pod": np.array([1.0, 2.0]),
            "cds": 0.8,
        },
    )

    # Run standard analysis
    standard_analysis(
        (
            "model.exe",
            str(input_file),
            str(output_file),
            1,
            42,
        ),
    )

    # Verify output file was created
    assert output_file.exists()

    # Load and check output
    with output_file.open("rb") as f:
        output_data = pickle.load(f)

    assert "fit" in output_data
    assert "diagnostics" in output_data
    assert output_data["diagnostics"] == "Test diagnostics"
    assert "parameters" in output_data

    # Check that all parameters were processed
    expected_params = [
        "mu",
        "sigma",
        "a",
        "b",
        "log_odds",
        "treatment_response",
        "theta",
        "beta",
        "gamma",
        "rho",
        "rtl",
        "rtu",
    ]
    for param in expected_params:
        assert param in output_data["parameters"]


@patch("bifrost_httr.core.analysis.get_response_window")
@patch("bifrost_httr.core.analysis.interpolate_treatment_effect")
def test_gen_plotting_data(
    mock_interpolate: MagicMock,
    mock_response_window: MagicMock,
    tmp_path: Path,
    sample_data: dict[str, np.ndarray | int],
    sample_samples: dict[str, np.ndarray],
) -> None:
    """Test generation of plotting data.

    This test verifies that the plotting data generation:
    1. Correctly processes input data and samples
    2. Creates output files with the expected structure
    3. Properly calculates summary statistics

    Uses fixtures for input data to ensure consistency across tests.
    """
    # Mock the response window calculation
    mock_samples = sample_samples.copy()
    mock_samples["rtl"] = np.random.normal(size=100)
    mock_samples["rtu"] = np.random.normal(size=100)
    mock_response_window.return_value = mock_samples

    # Mock the interpolation
    mock_interpolate.return_value = pd.Series(
        {
            "x": np.linspace(0, 10, 100),
            "response": np.random.normal(size=(3, 100)),
            "response_threshold_lower": 0.5,
            "response_threshold_upper": 1.5,
            "pod": np.random.normal(size=50),
            "cds": 0.8,
        },
    )

    output_path = tmp_path / "test_output.pkl"
    diagnostics = "Test diagnostics"

    gen_plotting_data(sample_data, sample_samples, output_path, diagnostics)

    # Check if file was created
    assert output_path.exists()

    # Load and verify the output
    with output_path.open("rb") as f:
        output_data = pickle.load(f)

    assert output_data["n_samp"] == len(sample_samples["theta"])
    assert output_data["max_conc"] == np.max(sample_data["conc"])
    assert "parameters" in output_data
    assert "fit" in output_data
    assert output_data["diagnostics"] == diagnostics


@patch("bifrost_httr.core.analysis.get_response_window")
@patch("bifrost_httr.core.analysis.interpolate_treatment_effect")
def test_gen_plotting_data_edge_cases(
    mock_interpolate: MagicMock,
    mock_response_window: MagicMock,
    tmp_path: Path,
    sample_data: dict[str, np.ndarray | int],
    sample_samples: dict[str, np.ndarray],
) -> None:
    """Test generation of plotting data with edge cases.

    This test covers three important edge cases:
    1. Empty samples: Verifies handling of empty input arrays
    2. Mismatched dimensions: Tests robustness to incorrect array shapes
    3. Non-numeric data: Ensures proper error handling for invalid data types

    The test uses a custom mock_response_window_func to simulate edge case
    scenarios and verifies that the function either handles them gracefully
    or raises appropriate errors.
    """

    def mock_response_window_func(
        samples: dict[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        """Mock function that returns empty response windows."""
        samples = samples.copy()
        samples["rtl"] = np.array([])
        samples["rtu"] = np.array([])
        return samples

    mock_response_window.side_effect = mock_response_window_func

    # Mock the interpolation to return a simple series
    mock_interpolate.return_value = pd.Series(
        {
            "x": [1, 2, 3],
            "pod": np.array([]),
            "cds": 0.0,
            "response": np.array([[0.0]]),  # Non-empty array with a single value
            "response_threshold_lower": 0.5,
            "response_threshold_upper": 1.5,
        },
    )

    # Test with empty samples
    empty_samples = {
        "mu": np.array([[]]),
        "sigma": np.array([]),
        "a": np.array([]),
        "b": np.array([]),
        "log_odds": np.array([]),
        "treatment_response": np.array([[]]),
        "theta": np.array([]),
        "beta": np.array([]),
        "gamma": np.array([]),
        "rho": np.array([]),
    }

    output_path = tmp_path / "empty_samples.pkl"
    gen_plotting_data(sample_data, empty_samples, output_path, "Test")

    # Check if file was created
    assert output_path.exists()

    # Load and verify the output
    with output_path.open("rb") as f:
        output_data = pickle.load(f)

    # Check that parameters contain NaN values
    assert "parameters" in output_data
    for param in output_data["parameters"].values():
        if isinstance(param, np.ndarray):
            if param.size > 0:
                assert np.all(np.isnan(param))
        else:
            assert np.isnan(param)

    # Test with mismatched dimensions
    bad_samples = sample_samples.copy()
    bad_samples["mu"] = np.random.normal(size=(100, 4))  # Wrong shape
    output_path = tmp_path / "bad_samples.pkl"
    gen_plotting_data(sample_data, bad_samples, output_path, "Test")

    # Check if file was created
    assert output_path.exists()

    # Load and verify the output
    with output_path.open("rb") as f:
        output_data = pickle.load(f)

    # Check that parameters were processed
    assert "parameters" in output_data
    assert output_data["parameters"]["mu"].shape == (4,)  # Mean over first dimension

    # Test with non-numeric data
    bad_data = sample_data.copy()
    bad_data["conc"] = np.array(["a", "b", "c"])
    with pytest.raises(TypeError):
        gen_plotting_data(
            bad_data,
            sample_samples,
            tmp_path / "should_not_exist.pkl",
            "Test",
        )


def test_run_concentration_response_analysis_multicore(tmp_path: Path) -> None:
    """Test concentration response analysis with multiple cores.

    This test verifies that:
    1. The function works with different numbers of cores
    2. Processes are properly cleaned up
    3. Results are consistent regardless of core count
    """
    # Create multiple test files
    test_files = []
    for i in range(4):
        data_file = tmp_path / f"test_data_{i}.pkl"
        with data_file.open("wb") as f:
            pickle.dump({"test": f"data_{i}"}, f)
        test_files.append(str(data_file))

    # Test with different core counts
    with patch("bifrost_httr.core.analysis.standard_analysis", mock_standard_analysis):
        for cores in [1, 2, 4]:
            run_concentration_response_analysis(
                files_to_process=test_files,
                model_executable="model.exe",
                number_of_cores=cores,
                fit_dir=tmp_path,
            )

            # Verify all output files exist
            for i in range(4):
                assert (tmp_path / "Fits" / f"test_data_{i}.pkl").exists()


@patch("bifrost_httr.core.analysis.get_response_window")
@patch("bifrost_httr.core.analysis.interpolate_treatment_effect")
def test_gen_plotting_data_invalid_paths(
    mock_interpolate: MagicMock,
    mock_response_window: MagicMock,
    sample_data: dict[str, np.ndarray | int],
    sample_samples: dict[str, np.ndarray],
    tmp_path: Path,
) -> None:
    """Test gen_plotting_data with invalid file paths.

    This test verifies proper error handling for:
    1. Non-existent directories
    2. Invalid path formats
    """
    # Add rtl and rtu to samples
    samples_with_rtl = sample_samples.copy()
    samples_with_rtl["rtl"] = np.array([0.1, 0.2])
    samples_with_rtl["rtu"] = np.array([1.8, 1.9])

    # Set up mocks to prevent hanging
    mock_response_window.return_value = samples_with_rtl
    mock_interpolate.return_value = pd.Series(
        {
            "x": np.array([1, 2, 3]),
            "response": np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
            "response_threshold_lower": 0.5,
            "response_threshold_upper": 1.5,
            "pod": np.array([1.0, 2.0]),
            "cds": 0.8,
        },
    )

    # Test invalid path format - use a platform-agnostic way to create an invalid path
    invalid_path = str(tmp_path / "invalid\0file.pkl")  # Null byte in filename
    with pytest.raises(ValueError, match="embedded null (byte|character)"):
        gen_plotting_data(
            sample_data,
            sample_samples,
            invalid_path,
            "Test",
        )

    # Test non-existent directory using pathlib.Path
    safe_nonexistent = tmp_path / "does_not_exist" / "output.pkl"
    with pytest.raises(FileNotFoundError):
        gen_plotting_data(
            sample_data,
            sample_samples,
            safe_nonexistent,
            "Test",
        )


@patch("bifrost_httr.core.analysis.fit_model")
def test_standard_analysis_with_seed(
    mock_fit_model: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that seed produces reproducible results.

    This test verifies that:
    1. Setting a seed produces consistent results
    2. The seed is properly passed to the Stan model
    3. Different seeds produce different results
    """
    # Create test data
    test_data = {
        "conc": np.array([1.0, 2.0, 3.0]),
        "total_count": np.array([100, 100, 100]),
        "n_conc": 3,  # Required for covariance calculation
        "n_treatment_batch": 2,  # Required for covariance calculation
        "n_batch": 2,
        "n_sample": 6,
        "n_samp": 1000,
    }

    # Create input file
    input_file = tmp_path / "input.pkl"
    with input_file.open("wb") as f:
        pickle.dump(test_data, f)

    # Mock fit_model to return consistent data
    mock_samples = {
        "mu": np.array([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]),
        "sigma": np.array([0.1, 0.2]),
        "a": np.array([0.1, 0.2]),
        "b": np.array([0.3, 0.4]),
        "log_odds": np.array([0.0, 0.1]),
        "treatment_response": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
        "theta": np.array([1.0, 1.1]),
        "beta": np.array([0.5, 0.6]),
        "gamma": np.array([0.7, 0.8]),
        "rho": np.array([0.9, 1.0]),
        "rtl": np.array([0.1, 0.2]),
        "rtu": np.array([1.8, 1.9]),
    }
    mock_fit_model.return_value = {
        "samples": mock_samples,
        "diagnostics": "Test diagnostics",
    }

    # Run analysis with same seed twice
    output_file1 = tmp_path / "output1.pkl"
    output_file2 = tmp_path / "output2.pkl"

    standard_analysis(
        (
            "model.exe",
            str(input_file),
            str(output_file1),
            1,
            42,  # Same seed
        ),
    )

    standard_analysis(
        (
            "model.exe",
            str(input_file),
            str(output_file2),
            1,
            42,  # Same seed
        ),
    )

    # Verify results are identical
    with output_file1.open("rb") as f1, output_file2.open("rb") as f2:
        data1 = pickle.load(f1)
        data2 = pickle.load(f2)

        # Compare each key in the dictionaries
        assert data1.keys() == data2.keys()
        for key in data1:
            if isinstance(data1[key], np.ndarray):
                assert np.array_equal(
                    data1[key],
                    data2[key],
                    equal_nan=True,
                ), f"Arrays not equal for key {key}"
            elif isinstance(data1[key], pd.Series):
                pd.testing.assert_series_equal(
                    data1[key],
                    data2[key],
                    check_dtype=False,
                )
            elif isinstance(data1[key], dict):
                # Compare nested dictionaries
                assert data1[key].keys() == data2[key].keys()
                for subkey in data1[key]:
                    if isinstance(data1[key][subkey], np.ndarray):
                        assert np.array_equal(
                            data1[key][subkey],
                            data2[key][subkey],
                            equal_nan=True,
                        ), f"Arrays not equal for key {key}.{subkey}"
                    elif isinstance(data1[key][subkey], pd.Series):
                        pd.testing.assert_series_equal(
                            data1[key][subkey],
                            data2[key][subkey],
                            check_dtype=False,
                        )
                    else:
                        assert (
                            data1[key][subkey] == data2[key][subkey]
                        ), f"Values not equal for key {key}.{subkey}"
            else:
                assert data1[key] == data2[key], f"Values not equal for key {key}"

    # Verify seed was passed to fit_model
    assert mock_fit_model.call_count == 2  # Called twice
    for call_args in mock_fit_model.call_args_list:
        args, _ = call_args
        assert args[0] == "model.exe"  # First arg should be model executable
        assert args[2] == 42  # Third arg should be seed
        # Verify essential data keys and values
        data_arg = args[1]
        assert "conc" in data_arg
        assert "total_count" in data_arg
        assert "n_conc" in data_arg
        assert "n_treatment_batch" in data_arg
        assert np.array_equal(data_arg["conc"], test_data["conc"])
        assert np.array_equal(data_arg["total_count"], test_data["total_count"])
        assert data_arg["n_conc"] == test_data["n_conc"]
        assert data_arg["n_treatment_batch"] == test_data["n_treatment_batch"]


@patch("bifrost_httr.core.analysis.get_response_window")
@patch("bifrost_httr.core.analysis.interpolate_treatment_effect")
def test_gen_plotting_data_edge_values(
    mock_interpolate: MagicMock,
    mock_response_window: MagicMock,
    tmp_path: Path,
) -> None:
    """Test gen_plotting_data with edge case values.

    This test verifies handling of:
    1. Zero concentrations
    2. Single concentration
    3. Very large/small numbers
    4. NaN/Inf values
    """
    # Test data with edge cases
    edge_data = {
        "conc": np.array([0.0, 1e-10, 1e10]),  # Zero, very small, very large
        "total_count": np.array([100, 100, 100]),
        "n_conc": 3,
        "n_batch": 2,
        "n_sample": 6,
        "n_samp": 1000,
    }

    edge_samples = {
        "mu": np.array([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]),
        "sigma": np.array([0.1, 0.2]),
        "a": np.array([0.1, 0.2]),
        "b": np.array([0.3, 0.4]),
        "log_odds": np.array([0.0, 0.1]),
        "treatment_response": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
        "theta": np.array([1.0, np.inf, np.nan]),  # Include Inf and NaN
        "beta": np.array([0.5, 0.6]),
        "gamma": np.array([0.7, 0.8]),
        "rho": np.array([0.9, 1.0]),
        "rtl": np.array([0.1, 0.2]),
        "rtu": np.array([1.8, 1.9]),
    }

    # Set up mocks
    mock_response_window.return_value = edge_samples
    mock_interpolate.return_value = pd.Series(
        {
            "x": np.array([1, 2, 3]),
            "response": np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
            "response_threshold_lower": 0.5,
            "response_threshold_upper": 1.5,
            "pod": np.array([1.0, 2.0]),
            "cds": 0.8,
        },
    )

    output_path = tmp_path / "edge_cases.pkl"

    # Verify function handles edge cases gracefully
    gen_plotting_data(edge_data, edge_samples, output_path, "Test")

    # Load and check results
    with output_path.open("rb") as f:
        output_data = pickle.load(f)

    # Verify edge cases were handled
    assert np.isfinite(output_data["max_conc"])  # Should handle Inf
    assert not np.any(np.isnan(output_data["parameters"]["mu"]))  # Should handle NaN
    assert output_data["parameters"]["sigma"] > 0  # Should be positive
