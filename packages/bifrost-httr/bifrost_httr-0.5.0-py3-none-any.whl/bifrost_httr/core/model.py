# Bifrost-HTTr- transcriptomics based dose response analysis
# Copyright (C) 2025 as Unilever Global IP Limited
# Bifrost-HTTr is free software: you can redistribute it and/or modify it under the terms
# of the GNU Lesser General Public License as published by the Free Software Foundation,
# either version 3 of the License. Bifrost-HTTr is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with Bifrost-HTTr.
# If not, see https://www.gnu.org/licenses/ . It is the responsibility of Bifrost-HTTr users to
# familiarise themselves with all dependencies and their associated licenses.

"""Core model definitions and utilities for BIFROST analysis.

This module provides the core model functionality for BIFROST analysis, including:
- Model fitting and sampling
- Model compilation
- Model initialization utilities
"""

import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import cmdstanpy
import numpy as np
import pandas as pd
from scipy.special import logit

from bifrost_httr.models import DEFAULT_MODEL_PATH
from bifrost_httr.utils.logging import get_logger

logger = get_logger(__name__)


def get_inits(data: dict[str, Any]) -> dict[str, Any]:
    """Calculate initial values for the model parameters.

    Args:
        data: Stan input dictionary

    Returns:
        Dictionary of initial values for model parameters

    """
    log_odds = logit(
        (np.array(data["count"]) + 0.5) / (np.array(data["total_count"]) + 1),
    )

    mu = np.empty(data["n_batch"])
    for i, idx in enumerate(np.unique(data["batch_index"])):
        mask = np.array(data["batch_index"]) == idx
        mu[i] = np.mean(log_odds[mask]) + 10

    return {"log_odds": log_odds, "mu": mu, "theta_raw": 0.0}


def compile_stan_model(stan_file: Path | None = None) -> Path:
    """Compile a Stan model file.

    Args:
        stan_file: Optional path to a custom Stan model file. If not provided,
            the default BIFROST model will be used.

    Returns:
        Path to the compiled executable

    Raises:
        FileNotFoundError: If the Stan file does not exist
        cmdstanpy.CompileError: If model compilation fails

    """
    # Use default model if no custom model is provided
    if stan_file is None:
        stan_file = DEFAULT_MODEL_PATH

    if not stan_file.exists():
        error_msg = f"Stan model file not found: {stan_file}"
        raise FileNotFoundError(error_msg)

    # If using the default model, copy it to working directory to avoid
    # storing compiled files in the Python package directory
    working_stan_file = stan_file
    temp_stan_file = None

    if stan_file == DEFAULT_MODEL_PATH:
        # Create a temporary file in the current working directory
        temp_stan_file = Path.cwd() / f"{DEFAULT_MODEL_PATH.name}"
        shutil.copy2(DEFAULT_MODEL_PATH, temp_stan_file)
        working_stan_file = temp_stan_file
        logger.info("Copied default model to working directory: %s", temp_stan_file)

    try:
        logger.info("Compiling Stan model: %s", working_stan_file)
        model = cmdstanpy.CmdStanModel(stan_file=working_stan_file)
        exe_path = Path(model.exe_file)
        logger.info("Compiled model executable: %s", exe_path)
        return exe_path
    finally:
        # Clean up the temporary .stan file if we created one
        if temp_stan_file and temp_stan_file.exists():
            temp_stan_file.unlink()
            logger.info("Cleaned up temporary Stan file: %s", temp_stan_file)


@contextmanager
def suppress_stdout_stderr() -> None:
    """Suppress stdout and stderr output in Python.

    This will suppress all print statements, even if they originate in compiled
    C/Fortran sub-functions. It will not suppress raised exceptions.
    """
    # Open a pair of null files
    null_fds = [os.open(os.devnull, os.O_RDWR) for _ in range(2)]
    # Save the actual stdout (1) and stderr (2) file descriptors
    save_fds = (os.dup(1), os.dup(2))

    try:
        # Assign the null pointers to stdout and stderr
        os.dup2(null_fds[0], 1)
        os.dup2(null_fds[1], 2)
        yield
    finally:
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(save_fds[0], 1)
        os.dup2(save_fds[1], 2)
        # Close the null files
        os.close(null_fds[0])
        os.close(null_fds[1])


def fit_model(
    path_to_executable: str | Path,
    data: dict[str, Any],
    seed: int | None = None,
) -> dict[str, Any]:
    """Fit the BIFROST model using PyStan.

    Args:
        path_to_executable: Path to compiled Stan model
        data: Data object to be passed to the model
        seed: Optional random seed for reproducibility

    Returns:
        Dictionary containing the posterior samples and diagnostics

    """
    # Attempt using standard settings
    model = cmdstanpy.CmdStanModel(exe_file=path_to_executable)
    fit = model.sample(
        data=data,
        chains=4,
        parallel_chains=1,
        iter_warmup=500,
        iter_sampling=1000,
        thin=4,
        inits=get_inits(data),
        save_warmup=False,
        max_treedepth=15,
        adapt_delta=0.95,
        seed=seed,
        show_console=False,
    )

    # Extract diagnostics
    diagnostics = fit.diagnose()

    # Check for multimodality and refit with more chains if detected
    s1 = "Split R-hat values satisfactory all parameters."
    s2 = "Rank-normalized split R-hat values satisfactory for all parameters."
    if s1 not in diagnostics and s2 not in diagnostics:
        fit = model.sample(
            data=data,
            chains=40,
            parallel_chains=1,  # Use a single core since we're parallelising across input files
            iter_warmup=500,
            iter_sampling=1000,
            thin=40,
            inits=get_inits(data),
            save_warmup=False,
            max_treedepth=15,
            adapt_delta=0.95,
            seed=seed,
            show_console=False,
        )

        diagnostics = fit.diagnose()

    # Extract samples
    samples = pd.Series(fit.stan_variables())

    return {"samples": samples, "diagnostics": diagnostics}
