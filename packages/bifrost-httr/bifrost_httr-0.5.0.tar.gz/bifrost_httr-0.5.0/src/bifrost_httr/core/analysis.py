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

"""Core analysis functions for BIFROST."""

import json
import pickle
from multiprocessing import Pool
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .model import fit_model, suppress_stdout_stderr
from .statistics import get_response_window, interpolate_treatment_effect

# Thresholds for biological significance
CDS_SIGNIFICANCE_THRESHOLD = 0.5
CDS_HIGH_CONFIDENCE = 0.8
CDS_MODERATE_CONFIDENCE = 0.5
CDS_LOW_CONFIDENCE = 0.3
CDS_VERY_LOW_CONFIDENCE = 0.1

# Maximum number of convergence issues for acceptable model
MAX_ACCEPTABLE_CONVERGENCE_ISSUES = 2


def _categorize_by_thresholds(
    value: float,
    thresholds: list[float],
    labels: list[str],
) -> str:
    """Helper function to categorize a numeric value using thresholds."""
    bin_index = np.digitize(value, thresholds)
    return labels[min(bin_index, len(labels) - 1)]


def generate_results_summary(
    data: dict[str, Any],
    samples: dict[str, Any],
    fit_results: pd.Series,
    diagnostics: str,
) -> dict[str, Any]:
    """Generate a JSON-serializable summary of key scientific conclusions.

    This creates consistent categorical classifications for BIFROST results,
    using CDS > 0.5 as the primary threshold for biological significance.
    Designed to be deterministic for reproducible snapshots.

    Args:
        data: Input data dictionary
        samples: MCMC samples dictionary (unused but kept for API consistency)
        fit_results: Fitted response curve results
        diagnostics: Diagnostic string from Stan

    Returns:
        Dictionary containing categorized scientific conclusions

    """
    # Extract core metrics
    pod_samples = fit_results["pod"]
    cds_value = float(fit_results["cds"])
    response_curves = fit_results["response"]

    # PoD analysis
    finite_pods = pod_samples[np.isfinite(pod_samples)] if len(pod_samples) > 0 else []
    detection_rate = (
        len(finite_pods) / len(pod_samples) if len(pod_samples) > 0 else 0.0
    )

    # Response analysis
    max_response = float(np.max(response_curves))
    min_response = float(np.min(response_curves))
    max_abs_response = max(abs(max_response), abs(min_response))

    # Threshold analysis
    threshold_lower = float(fit_results["response_threshold_lower"])
    threshold_upper = float(fit_results["response_threshold_upper"])
    exceeds_threshold = max_response > threshold_upper or min_response < threshold_lower

    # Categorize CDS (biological significance)
    cds_exceeds_threshold = cds_value > CDS_SIGNIFICANCE_THRESHOLD
    cds_category = _categorize_by_thresholds(
        cds_value,
        [
            CDS_VERY_LOW_CONFIDENCE,
            CDS_LOW_CONFIDENCE,
            CDS_SIGNIFICANCE_THRESHOLD,
            CDS_HIGH_CONFIDENCE,
        ],
        ["very_low", "low", "moderate", "high", "very_high"],
    )

    # Categorize detection rate (statistical power)
    signal_strength = _categorize_by_thresholds(
        detection_rate,
        [0.1, 0.5, 0.7, 0.9],
        ["very_low", "low", "moderate", "high", "very_high"],
    )

    # Effect direction
    if abs(max_response) > abs(min_response):
        effect_direction = "up"
    elif abs(min_response) > abs(max_response):
        effect_direction = "down"
    else:
        effect_direction = "none"

    # Effect magnitude (with CDS-informed adjustment)
    base_magnitude = _categorize_by_thresholds(
        max_abs_response,
        [10, 50, 100],
        ["minimal", "small", "moderate", "large"],
    )

    # Adjust magnitude based on CDS confidence
    if cds_value < CDS_LOW_CONFIDENCE and base_magnitude in ["moderate", "large"]:
        effect_magnitude = "small"
    elif cds_value < CDS_VERY_LOW_CONFIDENCE and base_magnitude != "minimal":
        effect_magnitude = "minimal"
    else:
        effect_magnitude = base_magnitude

    # Convergence assessment
    convergence_issues = []
    if "R-hat greater than 1.01" in diagnostics:
        convergence_issues.append("high_rhat")
    if (
        "divergent transitions found" in diagnostics
        and "No divergent transitions found" not in diagnostics
    ):
        convergence_issues.append("divergent_transitions")
    if "Treedepth satisfactory" not in diagnostics:
        convergence_issues.append("max_treedepth")
    if "E-BFMI satisfactory" not in diagnostics:
        convergence_issues.append("low_bfmi")
    if "effective sample size satisfactory" not in diagnostics:
        convergence_issues.append("low_ess")

    if len(convergence_issues) == 0:
        convergence_status = "excellent"
    elif len(convergence_issues) == 1 and "high_rhat" in convergence_issues:
        convergence_status = "acceptable"
    elif len(convergence_issues) <= MAX_ACCEPTABLE_CONVERGENCE_ISSUES:
        convergence_status = "issues_detected"
    else:
        convergence_status = "poor"

    # Overall interpretation confidence
    if cds_value > CDS_HIGH_CONFIDENCE and convergence_status in [
        "excellent",
        "acceptable",
    ]:
        interpretation_confidence = "high"
    elif cds_value > CDS_SIGNIFICANCE_THRESHOLD and convergence_status != "poor":
        interpretation_confidence = "moderate"
    else:
        interpretation_confidence = _categorize_by_thresholds(
            cds_value,
            [CDS_LOW_CONFIDENCE],
            ["very_low", "low"],
        )

    return {
        "scientific_conclusions": {
            "cds_exceeds_threshold": bool(cds_exceeds_threshold),
            "effect_direction": str(effect_direction),
            "effect_magnitude": str(effect_magnitude),
            "effect_exceeds_threshold": bool(exceeds_threshold),
            "cds_category": str(cds_category),
            "interpretation_confidence": str(interpretation_confidence),
        },
        "pod_analysis": {
            "detection_rate": float(round(detection_rate, 6)),
            "statistical_signal_strength": str(signal_strength),
        },
        "response_analysis": {
            "response_shape": (
                list(response_curves.shape)
                if hasattr(response_curves, "shape")
                else None
            ),
            "max_absolute_response_nearest_100": float(
                round(max_abs_response / 100) * 100,
            ),
        },
        "model_quality": {
            "convergence_status": str(convergence_status),
            "convergence_issues": (
                list(convergence_issues) if convergence_issues else []
            ),
            "has_regularization_warning": bool(
                "regularizating your model" in diagnostics,
            ),
        },
        "sample_metadata": {
            "n_concentrations": int(data["n_conc"]),
            "n_batches": int(data["n_batch"]),
            "n_samples_total": int(data["n_sample"]),
            "mcmc_samples": int(data["n_samp"]),
        },
    }


def run_concentration_response_analysis(
    files_to_process: list[str | Path],
    model_executable: str | Path,
    number_of_cores: int,
    fit_dir: str | Path | None = None,
    seed: int | None = None,
) -> None:
    """Fit Stan model for dataset specified by chemical and cell type.

    Args:
        files_to_process: List of probe .pkl files to process
        model_executable: Path to the compiled Stan model executable
        number_of_cores: Number of cores to use
        fit_dir: Optional directory to contain model fits
        seed: Optional random seed for reproducibility

    Raises:
        ValueError: If fit_dir is not a string
        FileNotFoundError: If any input file does not exist

    """
    # Define path to directory to contain model fits
    if fit_dir is None:
        path_to_fits = Path("Fits")
    elif isinstance(fit_dir, (str | Path)):
        path_to_fits = Path(fit_dir) / "Fits"
    else:
        error_msg = (
            "Directory to contain model fits must be specified as a string or Path"
        )
        raise ValueError(error_msg)

    # Create directory if it does not exist
    path_to_fits.mkdir(parents=True, exist_ok=True)

    # Check all inputs are present
    for f in files_to_process:
        if not Path(f).is_file():
            error_msg = f"Data file '{f}' does not exist"
            raise FileNotFoundError(error_msg)

    # Create list of arguments to pass to standard_analysis function
    fitting_args = [
        (
            str(model_executable),
            i,
            path_to_fits / f"{Path(i).stem}.pkl",
            number_of_cores,
            seed,
        )
        for i in files_to_process
    ]

    with Pool(number_of_cores) as p:
        p.map(standard_analysis, fitting_args)


def standard_analysis(paths: tuple[str | Path, ...]) -> None:
    """Fit model and generate plotting data using provided functions.

    Args:
        paths: Tuple containing paths to:
            - model executable
            - data file
            - fit file
            - number of cores (unused)
            - optional seed for reproducibility

    """
    path_to_executable, path_to_data, path_to_fit, _, seed = paths

    with Path(path_to_data).open("rb") as f:
        data = pickle.load(f)

    # Generate posterior samples
    with suppress_stdout_stderr():
        fit_dict = fit_model(path_to_executable, data, seed)

        # Generate model fits
        gen_plotting_data(
            data,
            fit_dict["samples"],
            path_to_fit,
            fit_dict["diagnostics"],
        )


def gen_plotting_data(
    data: dict[str, Any],
    samples: dict[str, Any],
    path_to_output: str | Path,
    diagnostics: str,
) -> None:
    """Generate dose response curves for the BIFROST model.

    Args:
        data: Data used to estimate model parameters
        samples: Posterior samples from the model fit
        path_to_output: Path to which the plotting data will be stored
        diagnostics: Diagnostic string for the fit

    Raises:
        ValueError: If path_to_output contains invalid characters
        FileNotFoundError: If parent directory of path_to_output does not exist
    """
    # Convert path_to_output to Path object and validate
    output_path = Path(path_to_output)

    # Ensure parent directory exists
    if not output_path.parent.exists():
        error_msg = f"Directory {output_path.parent} does not exist"
        raise FileNotFoundError(error_msg)

    # Calculate response window and add to samples
    samples = get_response_window(samples)

    # Add expected samples values to data file
    data["n_samp"] = len(samples["theta"])
    data["max_conc"] = np.max(data["conc"])

    # Extract samples
    data["parameters"] = {}
    for p in samples.keys():
        if samples[p].ndim == 1:
            data["parameters"][p] = np.mean(samples[p])
        else:
            data["parameters"][p] = np.mean(samples[p], axis=0)

    # Interpolate treatment effects and add to data file
    data["fit"] = interpolate_treatment_effect(data, samples)

    # Add diagnostics
    data["diagnostics"] = diagnostics

    # Save the full pickle file using pathlib.Path operations
    with output_path.open("wb") as f:
        pickle.dump(data, f)

    # Generate and save JSON summary
    json_summary = generate_results_summary(data, samples, data["fit"], diagnostics)
    json_path = output_path.with_suffix(".json")
    with json_path.open("w") as f:
        json.dump(json_summary, f, indent=2)
