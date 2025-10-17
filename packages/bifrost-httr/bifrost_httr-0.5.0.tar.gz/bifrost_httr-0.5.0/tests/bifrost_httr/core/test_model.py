"""Tests for model.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from bifrost_httr.core.model import compile_stan_model, fit_model, get_inits
from bifrost_httr.models import DEFAULT_MODEL_PATH


def test_get_inits() -> None:
    """Test get_inits function with valid input data."""
    # Test data
    data = {
        "count": [10, 20, 30, 40, 50],
        "total_count": [100, 100, 100, 100, 100],
        "batch_index": [1, 1, 2, 2, 2],
        "n_batch": 2,
    }

    # Get initial values
    inits = get_inits(data)

    # Check return type and keys
    assert isinstance(inits, dict)
    assert set(inits.keys()) == {"log_odds", "mu", "theta_raw"}

    # Check shapes
    assert len(inits["log_odds"]) == len(data["count"])
    assert len(inits["mu"]) == data["n_batch"]
    assert isinstance(inits["theta_raw"], float)

    # Check values are reasonable
    assert np.all(np.isfinite(inits["log_odds"]))
    assert np.all(np.isfinite(inits["mu"]))
    assert inits["theta_raw"] == 0.0


def test_get_inits_edge_cases() -> None:
    """Test get_inits function with edge cases."""
    # Test with zero counts
    data = {
        "count": [0, 0, 0],
        "total_count": [100, 100, 100],
        "batch_index": [1, 1, 1],
        "n_batch": 1,
    }
    inits = get_inits(data)
    assert np.all(np.isfinite(inits["log_odds"]))
    assert np.all(np.isfinite(inits["mu"]))

    # Test with single batch
    data = {
        "count": [10, 20, 30],
        "total_count": [100, 100, 100],
        "batch_index": [1, 1, 1],
        "n_batch": 1,
    }
    inits = get_inits(data)
    assert len(inits["mu"]) == 1


def test_compile_stan_model_default() -> None:
    """Test compile_stan_model with default model."""
    # Mock CmdStanModel to avoid actual compilation
    with patch("bifrost_httr.core.model.cmdstanpy.CmdStanModel") as mock_model:
        mock_model.return_value.exe_file = "/path/to/compiled/model"

        # Mock file operations to avoid actual file operations
        with (
            patch("bifrost_httr.core.model.shutil.copy2") as mock_copy,
            patch.object(Path, "unlink") as mock_unlink,
            patch.object(Path, "exists", return_value=True),
        ):
            exe_path = compile_stan_model()

            # Check that the default model was copied to working directory
            expected_temp_file = Path.cwd() / DEFAULT_MODEL_PATH.name
            mock_copy.assert_called_once_with(
                DEFAULT_MODEL_PATH,
                expected_temp_file,
            )

            # Check that CmdStanModel was called with the temporary file
            mock_model.assert_called_once_with(stan_file=expected_temp_file)

            # Check that temporary file was cleaned up
            mock_unlink.assert_called_once()

            assert isinstance(exe_path, Path)


def test_compile_stan_model_custom() -> None:
    """Test compile_stan_model with custom model file."""
    # Create a temporary Stan file
    custom_model = Path("custom_model.stan")
    custom_model.touch()

    try:
        # Mock CmdStanModel to avoid actual compilation
        with patch("bifrost_httr.core.model.cmdstanpy.CmdStanModel") as mock_model:
            mock_model.return_value.exe_file = "/path/to/compiled/model"
            exe_path = compile_stan_model(custom_model)

            # Check that custom model was used
            mock_model.assert_called_once_with(stan_file=custom_model)
            assert isinstance(exe_path, Path)
    finally:
        # Clean up
        custom_model.unlink()


def test_compile_stan_model_file_not_found() -> None:
    """Test compile_stan_model with non-existent file."""
    with pytest.raises(FileNotFoundError):
        compile_stan_model(Path("non_existent.stan"))


@pytest.fixture
def mock_cmdstan_fit() -> MagicMock:
    """Create a mock CmdStanFit object."""
    mock_fit = MagicMock()

    # Mock diagnose method
    mock_fit.diagnose.return_value = "Split R-hat values satisfactory all parameters."

    # Mock stan_variables method
    mock_fit.stan_variables.return_value = {
        "param1": np.array([1, 2, 3]),
        "param2": np.array([4, 5, 6]),
    }

    # Mock draws_pd method
    mock_fit.draws_pd.return_value = pd.DataFrame(
        {
            "chain__": [1, 2, 3],
            "iter__": [1, 2, 3],
            "draw__": [1, 2, 3],
            "accept_stat__": [0.8, 0.9, 0.85],
            "stepsize__": [0.1, 0.1, 0.1],
            "treedepth__": [5, 6, 5],
            "n_leapfrog__": [10, 12, 11],
            "divergent__": [0, 0, 0],
            "energy__": [10.1, 10.2, 10.3],
        },
    )

    return mock_fit


def test_fit_model(mock_cmdstan_fit: MagicMock) -> None:
    """Test fit_model with mocked CmdStanModel."""
    # Test data
    data = {
        "count": [10, 20, 30],
        "total_count": [100, 100, 100],
        "batch_index": [1, 1, 1],
        "n_batch": 1,
    }

    # Mock CmdStanModel
    with patch("bifrost_httr.core.model.cmdstanpy.CmdStanModel") as mock_model_cls:
        mock_model = mock_model_cls.return_value
        mock_model.sample.return_value = mock_cmdstan_fit

        # Run fit_model
        result = fit_model("path/to/exe", data, seed=42)

        # Check that model was created with correct executable
        mock_model_cls.assert_called_once_with(exe_file="path/to/exe")

        # Check that sample was called with correct parameters
        sample_kwargs = {
            "data": data,
            "chains": 4,
            "parallel_chains": 1,
            "iter_warmup": 500,
            "iter_sampling": 250,
            "thin": 1,
            "save_warmup": False,
            "max_treedepth": 15,
            "adapt_delta": 0.95,
            "seed": 42,
            "show_console": True,
        }

        # Check return value structure
        assert isinstance(result, dict)
        assert set(result.keys()) == {"samples", "diagnostics"}
        assert isinstance(result["samples"], pd.Series)
        assert isinstance(result["diagnostics"], str)


def test_fit_model_multimodal(mock_cmdstan_fit: MagicMock) -> None:
    """Test fit_model when initial fit indicates multimodality."""
    # Modify mock to indicate multimodality in first fit
    mock_cmdstan_fit.diagnose.side_effect = [
        "Some parameters had split R-hat > 1.01",  # First fit
        "Split R-hat values satisfactory all parameters.",  # Second fit
    ]

    # Test data
    data = {
        "count": [10, 20, 30],
        "total_count": [100, 100, 100],
        "batch_index": [1, 1, 1],
        "n_batch": 1,
    }

    # Mock CmdStanModel
    with patch("bifrost_httr.core.model.cmdstanpy.CmdStanModel") as mock_model_cls:
        mock_model = mock_model_cls.return_value
        mock_model.sample.return_value = mock_cmdstan_fit

        # Run fit_model
        result = fit_model("path/to/exe", data, seed=42)

        # Check that sample was called twice with different parameters
        assert mock_model.sample.call_count == 2

        # Check second call had more chains
        _, kwargs = mock_model.sample.call_args
        assert kwargs["chains"] == 40
        assert kwargs["thin"] == 40

        # Check return value
        assert isinstance(result, dict)
        assert set(result.keys()) == {"samples", "diagnostics"}
