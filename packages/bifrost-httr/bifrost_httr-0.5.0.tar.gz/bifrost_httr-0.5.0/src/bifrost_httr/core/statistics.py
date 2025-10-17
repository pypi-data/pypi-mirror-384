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

"""Statistical functions for BIFROST analysis."""

from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import gmean

from .distributions import BetaLogistic


def get_response_window(samples: dict[str, Any]) -> dict[str, Any]:
    """Calculate response window for calculating PoDs.

    Args:
        samples: Dictionary of parameter samples

    Returns:
        Updated samples dictionary with response window

    """
    rtl = np.array(
        [
            BetaLogistic(0, s, a, b).ppf(0.05)
            for s, a, b in zip(
                samples["sigma"],
                samples["a"],
                samples["b"],
                strict=False,
            )
        ],
    )
    rtu = np.array(
        [
            BetaLogistic(0, s, a, b).ppf(0.95)
            for s, a, b in zip(
                samples["sigma"],
                samples["a"],
                samples["b"],
                strict=False,
            )
        ],
    )

    samples["rtl"] = rtl
    samples["rtu"] = rtu

    return samples


def get_bifrost_covariance(
    data: dict[str, Any],
    samples: dict[str, Any],
    conc: np.ndarray | None = None,
    *,
    add_sigma: bool = True,
) -> np.ndarray:
    """Compute the BIFROST kernel for the supplied concentration arrays.

    Args:
        data: Dictionary of concentration-response data
        samples: Dictionary of parameter estimates
        conc: Optional array of concentrations to extrapolate to
        add_sigma: Whether to add the sigma term to the covariance

    Returns:
        Covariance matrix

    """
    n_samp = len(samples["theta"])
    if conc is None:
        Sigma = np.zeros((n_samp, data["n_conc"], data["n_conc"]))
        for i in range(data["n_conc"]):
            ci = data["conc"][i]

            if add_sigma:
                Sigma[:, i, i] += (
                    np.square(samples["sigma"]) / data["n_treatment_batch"]
                )

            theta = samples["theta"]
            beta = samples["beta"]
            gamma = samples["gamma"]
            Sigma[:, i, i] += (
                gamma**2 / (1 + np.exp(np.log(19) * (ci - beta) / (theta - beta))) ** 2
            )

            for j in range(i):
                cj = data["conc"][j]
                rho = samples["rho"]

                Sigma[:, i, j] += (
                    gamma**2
                    / (1 + np.exp(np.log(19) * (ci - beta) / (theta - beta)))
                    / (1 + np.exp(np.log(19) * (cj - beta) / (theta - beta)))
                    * np.exp(-0.5 * ((ci - cj) / rho) ** 2)
                )

                # Fill opposite diagonal
                Sigma[:, j, i] = Sigma[:, i, j]

    else:
        n = len(conc)
        Sigma = np.zeros((n_samp, n, data["n_conc"]))
        for i in range(n):
            ci = conc[i]
            for j in range(data["n_conc"]):
                cj = data["conc"][j]
                theta = samples["theta"]
                beta = samples["beta"]
                gamma = samples["gamma"]
                rho = samples["rho"]

                Sigma[:, i, j] += (
                    gamma**2
                    / (1 + np.exp(np.log(19) * (ci - beta) / (theta - beta)))
                    / (1 + np.exp(np.log(19) * (cj - beta) / (theta - beta)))
                    * np.exp(-0.5 * ((ci - cj) / rho) ** 2)
                )

    return Sigma


def calc_pod_sample(
    conc: np.ndarray,
    response: np.ndarray,
    lower_limit: float,
    upper_limit: float,
) -> float:
    """Calculate the PoD given a sample of the curve describing the mean response.

    Args:
        conc: Array of concentrations at which the curve has been evaluated
        response: Array containing sample for mean response
        lower_limit: Lower limit of the distribution for the control response
        upper_limit: Upper limit of the distribution for the control response

    Returns:
        Sample for the PoD based on the supplied sample of the concentration-response

    """
    # Determine which direction of largest change
    abs_response_up = np.abs(np.max(response))
    abs_response_down = np.abs(np.min(response))

    response_direction = "up" if abs_response_up > abs_response_down else "down"

    pod = np.inf
    if response_direction == "up" and np.max(response) > upper_limit:
        index = np.argmax(response)
        for i in range(index):
            if response[index - i] < upper_limit:
                pod = (
                    upper_limit * (conc[index - (i - 1)] - conc[index - i])
                    - (
                        response[index - i] * conc[index - (i - 1)]
                        - response[index - (i - 1)] * conc[index - i]
                    )
                ) / (response[index - (i - 1)] - response[index - i])
                break

    elif response_direction == "down" and np.min(response) < lower_limit:
        index = np.argmin(response)
        for i in range(index):
            if response[index - i] > lower_limit:
                pod = (
                    lower_limit * (conc[index - (i - 1)] - conc[index - i])
                    - (
                        response[index - i] * conc[index - (i - 1)]
                        - response[index - (i - 1)] * conc[index - i]
                    )
                ) / (response[index - (i - 1)] - response[index - i])
                break

    return pod


def interpolate_treatment_effect(
    data: dict[str, Any],
    samples: dict[str, Any],
) -> pd.Series:
    """Calculate the posterior predictive mean effect of the treatment.

    Args:
        data: Dictionary of concentration-response data
        samples: Dictionary of parameter estimates

    Returns:
        Series containing interpolated treatment effects

    """
    n_x = 100
    x = np.linspace(
        min(np.min(data["conc"]), np.min(samples["theta"])),
        np.max(data["conc"]),
        n_x,
    )
    Sigma = get_bifrost_covariance(data, samples)
    Sigma_inv = np.array([np.linalg.inv(i) for i in Sigma])
    Sigma_extrapolation = get_bifrost_covariance(data, samples, x)
    treatment_response = np.array(
        [
            St.dot(Sinv).dot(tr)
            for St, Sinv, tr in zip(
                Sigma_extrapolation,
                Sigma_inv,
                samples["treatment_response"],
                strict=False,
            )
        ],
    )

    # Calculate PoDs
    rtl, rtu = samples["rtl"], samples["rtu"]

    pod = np.array(
        [
            calc_pod_sample(x, i, u, v)
            for i, u, v in zip(treatment_response, rtl, rtu, strict=False)
        ],
    ).astype("float")
    cds = np.sum(~np.isinf(pod)) / len(pod)
    pod = pod[~np.isinf(pod)]

    # Convert treatment response to expected count
    median_total_count = np.median(data["total_count"])
    log_odds = np.array(
        [
            i + j - 10
            for i, j in zip(
                np.mean(samples["mu"], axis=1),
                treatment_response,
                strict=False,
            )
        ],
    )
    prob = expit(log_odds)
    expected_count = prob * median_total_count
    expected_count_percentiles = np.percentile(
        expected_count,
        q=(2.5, 50, 97.5),
        axis=0,
    )

    return pd.Series(
        {
            "x": x,
            "response": expected_count_percentiles,
            "response_threshold_lower": gmean(
                expit(np.mean(samples["mu"], axis=1) + rtl - 10) * median_total_count,
            ),
            "response_threshold_upper": gmean(
                expit(np.mean(samples["mu"], axis=1) + rtu - 10) * median_total_count,
            ),
            "pod": pod,
            "cds": cds,
        },
    )


def get_confidence_threshold_probability_density(
    x: np.ndarray,
    threshold_lower: float = 0.5,
    threshold_upper: float = 1.0,
    param_a: float = 0.38387606,
    param_b: float = -5.40387609,
    param_c: float = 2.8775016,
) -> np.ndarray:
    """Evaluate the probability density for the function describing uncertainty in CDS threshold.

    This function calculates the probability density for a beta-logistic distribution
    that models uncertainty in the CDS (Concentration-Dependency Score) threshold.

    Args:
        x: Array of values at which to calculate density
        threshold_lower: Lower threshold boundary (default: 0.5)
        threshold_upper: Upper threshold boundary (default: 1.0)
        param_a: Distribution parameter a (default: 0.38387606)
        param_b: Distribution parameter b (default: -5.40387609)
        param_c: Distribution parameter c (default: 2.8775016)

    Returns:
        Array of corresponding probability densities

    Note:
        This function is used in global PoD calculations to weight different
        CDS threshold values according to their uncertainty.

    """
    dq = np.zeros(len(x))
    index = np.where((x > threshold_lower) & (x < threshold_upper))[0]

    if len(index) > 0:
        tl, tu, a, b, c = threshold_lower, threshold_upper, param_a, param_b, param_c
        g = ((x[index] - tl) / (tu - tl)) ** (-1 / c) - 1
        dg = -(((x[index] - tl) / (tu - tl)) ** (-1 / c - 1)) / (c * (tu - tl))
        h = b - np.log(g) / a
        dh = -dg / (a * g)
        dq[index] = np.exp(-h) / (1 + np.exp(-h)) ** 2 * dh

    return dq


def get_minimum_pod_means(
    pod_means: np.ndarray,
    cds: np.ndarray,
    probe_ids: np.ndarray,
    cds_thresholds: np.ndarray,
    max_conc: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute minimum PoD means for each CDS threshold value.

    This function finds the probe with the minimum PoD mean for each CDS threshold,
    considering only probes that meet or exceed the threshold.

    Args:
        pod_means: Array of PoD mean values for each probe
        cds: Array of CDS values for each probe
        probe_ids: Array of probe identifiers (strings)
        cds_thresholds: Array of CDS threshold values to evaluate
        max_conc: Maximum concentration value (used as fallback)

    Returns:
        Tuple containing:
            - min_means: Array of minimum PoD mean values for each threshold
            - min_probes: Array of probe IDs corresponding to minimum means
            - min_cds: Array of CDS values for the minimum probes

    Note:
        When no probes meet a threshold, 'Max. conc.' is used as the probe identifier
        and max_conc is used as the PoD value.

    """
    min_means = np.full(len(cds_thresholds), max_conc, dtype=np.float64)
    min_probes = np.full(len(cds_thresholds), "Max. conc.", dtype=object)
    min_cds = np.full(len(cds_thresholds), 0.0, dtype=np.float64)

    for i, threshold in enumerate(cds_thresholds):
        mask = cds >= threshold
        if np.sum(mask) > 0:
            pod_subset = pod_means[mask]
            probe_subset = probe_ids[mask]
            cds_subset = cds[mask]

            index = np.argmin(pod_subset)
            min_means[i] = pod_subset[index]
            min_probes[i] = probe_subset[index]
            min_cds[i] = cds_subset[index]

    return min_means, min_probes, min_cds


def calculate_global_pod(
    data_source: pd.Series | dict[str, np.ndarray | float | int],
    data_type: str = "summary",
    seed: int | None = None,
    quantile_step: float = 0.025,
    threshold_params: dict[str, float] | None = None,
) -> dict[str, float | np.ndarray | int]:
    """Calculate global Point of Departure (PoD) from probe-level statistics.

    This function computes the global PoD by aggregating probe-level PoD distributions
    using a weighted approach based on CDS (Concentration-Dependency Score) thresholds.

    Args:
        data_source: Either a BIFROST summary Series or a statistics dictionary
        data_type: Type of data source - "summary" for pd.Series, "stats" for dict
        seed: Optional random seed for reproducibility
        quantile_step: Step size for CDS threshold quantiles (default: 0.025)
        threshold_params: Optional dictionary of threshold probability density parameters

    Returns:
        Dictionary containing:
            - global_pod: Calculated global PoD value (float)
            - num_hits: Expected number of hits (int)
            - means: Array of minimum PoD means for each threshold
            - probes: Array of probe IDs corresponding to minimum means
            - weights: Array of weights used in calculation
            - quantiles: Array of CDS threshold quantiles
            - cds: Array of CDS values for minimum probes

    Raises:
        ValueError: If data_type is not recognized or required data is missing
        KeyError: If required keys are missing from input data

    Note:
        This function consolidates the global PoD calculation logic from multiple
        modules while preserving type safety and compatibility with existing code.

    """
    if seed is not None:
        np.random.seed(seed)

    # Set default threshold parameters if not provided
    if threshold_params is None:
        threshold_params = {}

    # Extract data based on source type
    if data_type == "summary":
        if not isinstance(data_source, pd.Series):
            error_msg = "data_source must be pd.Series when data_type='summary'"
            raise ValueError(error_msg)

        df = data_source

        # Extract probe information
        if "probes" not in df:
            error_msg = "'probes' key missing from summary data"
            raise KeyError(error_msg)

        probes = np.array(df["probes"], dtype=str)

        # Extract PoD means and CDS values
        pod_means = np.array(
            [
                np.mean(df[probe]["pod"]) if len(df[probe]["pod"]) > 0 else np.nan
                for probe in probes
            ],
            dtype=np.float64,
        )

        cds = np.array([df[probe]["cds"] for probe in probes], dtype=np.float64)
        max_conc = float(df["max_conc"])

    elif data_type == "stats":
        if not isinstance(data_source, dict):
            error_msg = "data_source must be dict when data_type='stats'"
            raise ValueError(error_msg)

        stats = data_source

        # Validate required keys
        required_keys = ["probe", "pod", "cds", "max_conc"]
        missing_keys = [key for key in required_keys if key not in stats]
        if missing_keys:
            error_msg = f"Missing required keys in stats data: {missing_keys}"
            raise KeyError(error_msg)

        probes = np.array(stats["probe"], dtype=str)
        pod_means = np.array(stats["pod"], dtype=np.float64)
        cds = np.array(stats["cds"], dtype=np.float64)
        max_conc = float(stats["max_conc"])

    else:
        error_msg = f"Unsupported data_type: {data_type}. Must be 'summary' or 'stats'"
        raise ValueError(error_msg)

    # Generate CDS threshold quantiles using linspace to avoid floating point precision issues
    num_points = round((1.0 - 0.5) / quantile_step) + 1
    quantiles = np.linspace(0.5, 1.0, num_points)

    # Get minimum PoD means for each threshold
    min_means, min_probes, min_cds = get_minimum_pod_means(
        pod_means,
        cds,
        probes,
        quantiles,
        max_conc,
    )

    # Calculate probability density weights
    weights = get_confidence_threshold_probability_density(
        quantiles,
        **threshold_params,
    )
    weight_sum = np.sum(weights)

    if weight_sum == 0:
        error_msg = "Sum of weights is zero - check threshold parameters"
        raise ValueError(error_msg)

    # Calculate weighted global PoD (in log10 space, then transform back)
    global_pod = 10 ** (np.sum(min_means * weights) / weight_sum)

    # Calculate number of hits at each confidence threshold
    num_hits = np.array(
        [np.sum(cds >= threshold) for threshold in quantiles],
        dtype=int,
    )
    expected_num_hits = np.round(np.sum(num_hits * weights) / weight_sum)

    # Prepare results dictionary
    return {
        "global_pod": float(global_pod),
        "num_hits": expected_num_hits,
        "means": min_means,
        "probes": min_probes,
        "weights": weights,
        "quantiles": quantiles,
        "cds": min_cds,
    }


def get_probe_weights_from_global_pod(
    global_pod_results: dict[str, float | np.ndarray | int],
) -> dict[str, np.ndarray]:
    """Compute weights for individual probes contributing to global PoD.

    This function aggregates the weights from the global PoD calculation to determine
    how much each unique probe contributes to the final global PoD value.

    Args:
        global_pod_results: Dictionary from calculate_global_pod() containing:
            - probes: Array of probe identifiers
            - means: Array of minimum means for each probe
            - weights: Array of weights used in calculation
            - cds: Array of CDS values for each probe

    Returns:
        Dictionary containing:
            - probe: Array of unique probe identifiers (sorted by weight)
            - weight: Array of weights for each probe (sorted descending)
            - min_mean: Array of minimum means for each probe (back-transformed)
            - cds: Array of CDS values for each probe

    Raises:
        KeyError: If required keys are missing from input dictionary

    Note:
        Results are sorted by weight (descending order), with the most influential
        probes listed first.

    """
    required_keys = ["probes", "means", "weights", "cds"]
    missing_keys = [key for key in required_keys if key not in global_pod_results]
    if missing_keys:
        error_msg = f"Missing required keys in global_pod_results: {missing_keys}"
        raise KeyError(error_msg)

    # Get unique probes and aggregate their contributions
    unique_probes = np.unique(global_pod_results["probes"])

    # Filter out the 'Max. conc.' placeholder
    valid_probes = unique_probes[unique_probes != "Max. conc."]

    if len(valid_probes) == 0:
        # Return empty result if no valid probes
        return {
            "probe": np.array([], dtype=str),
            "weight": np.array([], dtype=np.float64),
            "min_mean": np.array([], dtype=np.float64),
            "cds": np.array([], dtype=np.float64),
        }

    # Calculate aggregated values for each unique probe
    means = np.array(
        [
            global_pod_results["means"][global_pod_results["probes"] == probe][0]
            for probe in valid_probes
        ],
        dtype=np.float64,
    )

    # Back-transform means from log10 space
    means = np.power(10, means)

    cds_values = np.array(
        [
            global_pod_results["cds"][global_pod_results["probes"] == probe][0]
            for probe in valid_probes
        ],
        dtype=np.float64,
    )

    # Aggregate weights for each probe
    total_weight = np.sum(global_pod_results["weights"])
    weights = np.array(
        [
            np.sum(global_pod_results["weights"][global_pod_results["probes"] == probe])
            / total_weight
            for probe in valid_probes
        ],
        dtype=np.float64,
    )

    # Sort by weight (descending order)
    sort_indices = np.argsort(weights)[::-1]

    return {
        "probe": valid_probes[sort_indices],
        "weight": weights[sort_indices],
        "min_mean": means[sort_indices],
        "cds": cds_values[sort_indices],
    }
