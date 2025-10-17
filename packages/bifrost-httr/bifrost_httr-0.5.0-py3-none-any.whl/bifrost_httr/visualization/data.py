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

"""Data management and visualization for BIFROST analysis.

This module provides classes for managing and visualizing BIFROST data:
- BifrostData: Core data management and calculations
- ProbeData: Probe-specific data processing and visualization
"""

from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from bifrost_httr.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)


class BifrostData:
    """Helper class to manage BIFROST data and calculations.

    This class handles loading and processing of BIFROST summary data, including
    calculation of summary statistics, global PoD, and probe weights.

    Attributes:
        df (pd.Series): BIFROST summary data containing probe information
        stats (Dict[str, Union[np.ndarray, float, int]]): Dictionary containing:
            - probe: Array of probe identifiers
            - pod: Array of PoD means for each probe
            - cds: Array of CDS scores for each probe
            - l2fc: Array of log2 fold changes for each probe
            - max_conc: Maximum tested concentration
            - n_samp: Number of samples
            - conc: Array of concentration values
            - _response_cache: Dictionary mapping probe IDs to response arrays

    """

    def __init__(self, summary_file: str) -> None:
        """Initialize BifrostData with summary file.

        Args:
            summary_file: Path to the summary JSON file. Can be compressed (.zip)

        Raises:
            FileNotFoundError: If summary file doesn't exist
            ValueError: If summary file is malformed

        """
        compression = "zip" if summary_file.endswith(".zip") else None
        self.df = pd.read_json(
            summary_file,
            typ="series",
            orient="index",
            compression=compression,
            dtype_backend="numpy_nullable",
        )
        self.stats = self.calculate_summary_statistics()

    def calculate_summary_statistics(self) -> dict[str, np.ndarray | float | int]:
        """Calculate summary statistics for BIFROST analysis.

        This method computes various summary statistics including PoD mean, log2 fold-change
        extrema, and CDS scores for each probe in the dataset.

        Inputs:
            self.df (pd.Series): BIFROST summary data containing probe information, loaded
                during class initialization. Contains keys:
                - probes: List of probe identifiers
                - max_conc: Maximum tested concentration
                - n_samp: Number of samples
                - conc: Array of concentration values
                - For each probe: pod, cds, response arrays

        Returns:
            Dictionary containing:
                - probe: Array of probe identifiers
                - pod: Array of PoD means for each probe
                - cds: Array of CDS scores for each probe
                - l2fc: Array of log2 fold changes for each probe
                - max_conc: Maximum tested concentration
                - n_samp: Number of samples
                - conc: Array of concentration values
                - _response_cache: Dictionary mapping probe IDs to response arrays

        Raises:
            KeyError: If required keys are missing from self.df
            ValueError: If probe data is malformed

        """
        df = self.df
        probes = np.array(df["probes"])
        max_conc = df["max_conc"]
        n_samp = df["n_samp"]
        conc = df["conc"]
        pod = np.array(
            [
                np.mean(df[i]["pod"]) if len(df[i]["pod"]) > 0 else np.nan
                for i in probes
            ],
        )
        cds = np.array([df[i]["cds"] for i in probes])
        l2fc = np.empty(probes.shape[0], dtype="float")
        response_cache = {probe: np.array(df[probe]["response"][1]) for probe in probes}
        for i, probe in enumerate(probes):
            y = response_cache[probe]
            index = np.argmax(np.abs(np.log2(y / y[0])))
            l2fc[i] = np.log2(y[index] / y[0])

        return {
            "probe": probes,
            "pod": pod,
            "cds": cds,
            "l2fc": l2fc,
            "max_conc": max_conc,
            "n_samp": n_samp,
            "conc": conc,
            "_response_cache": response_cache,
        }

    def filter_summary_statistics(self, cds_threshold: float) -> dict[str, np.ndarray]:
        """Filter summary statistics based on CDS threshold.

        Inputs:
            self.stats (Dict[str, Union[np.ndarray, float, int]]): Summary statistics dictionary
                containing probe data, computed by calculate_summary_statistics(). Contains keys:
                - probe: Array of probe identifiers
                - pod: Array of PoD means for each probe
                - cds: Array of CDS scores for each probe
                - l2fc: Array of log2 fold changes for each probe

        Args:
            cds_threshold: Minimum CDS value to keep in filtered results.

        Returns:
            Filtered dictionary with same structure as self.stats, containing only entries where
            CDS >= cds_threshold.

        Raises:
            KeyError: If required keys are missing from self.stats

        """
        df = self.stats
        mask = df["cds"] >= cds_threshold
        filtered_df = df.copy()
        for key in ["probe", "pod", "cds", "l2fc"]:
            filtered_df[key] = df[key][mask]
        return filtered_df

    def fit_pod_histogram(
        self,
        pod_samples: np.ndarray,
        n_samp: int,
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        """Create histogram approximation of PoD distribution.

        Args:
            pod_samples: Array of samples from the PoD distribution
            n_samp: Maximum number of possible samples

        Returns:
            Tuple containing:
                - weights: Array of histogram weights (or None if no valid samples)
                - bin_edges: Array of histogram bin edges (or None if no valid samples)

        Note:
            If pod_samples contains infinite values, n_samp is set to the length of pod_samples.

        """
        if np.isinf(pod_samples).any():
            n_samp = len(pod_samples)
        pod_samples = pod_samples[~np.isinf(pod_samples)]
        n_pod_samples = len(pod_samples)
        if n_pod_samples == 0:
            return None, None
        prob_response = n_pod_samples / n_samp
        counts, bin_edges = np.histogram(pod_samples, bins=int(np.sqrt(n_pod_samples)))
        bin_size = bin_edges[1:] - bin_edges[:-1]
        bin_weights = counts * bin_size
        total_weight = np.sum(bin_weights)
        weights = counts / total_weight * prob_response
        return weights, bin_edges

    def create_summary_table_data(
        self,
        probes: list[str],
        weights: dict[str, np.ndarray],
        conc_units: str,
        *,
        sort_by_abs_fc: bool = False,
    ) -> dict[str, dict[str, str]]:
        """Create summary table data for a list of probes.

        Inputs:
            self.df (pd.Series): BIFROST summary data containing probe information
            self.stats (Dict[str, Union[np.ndarray, float, int]]): Summary statistics dictionary
                containing probe data, computed by calculate_summary_statistics(). Contains keys:
                - probe: Array of probe identifiers
                - l2fc: Array of log2 fold changes for each probe

        Args:
            probes: List of probe identifiers
            weights: Dictionary containing probe weights with keys:
                - probe: Array of probe identifiers
                - weight: Array of weights for each probe
            conc_units: String specifying concentration units
            sort_by_abs_fc: Whether to sort probes by absolute fold change

        Returns:
            Dictionary mapping probe IDs to their summary statistics

        """
        # First create all data without any sorting
        data = {}
        for probe in probes:
            # Calculate all probe statistics
            mean_pod = np.mean(self.df[probe]["pod"])
            weight = (
                weights["weight"][weights["probe"] == probe][0]
                if probe in weights["probe"]
                else 0.0
            )
            l2fc = self.stats["l2fc"][self.stats["probe"] == probe][0]

            # Store all data for this probe
            data[probe] = {
                "_abs_fc": abs(l2fc),  # Keep as float for potential sorting
                "CDS": f"{self.df[probe]['cds']:.3f}",
                "Mean PoD": f"{10**mean_pod:.2g} {conc_units}",
                "Log2 Fold Change": f"{l2fc:.2f}",
                "Global PoD Weight": f"{weight:.3f}",
                "Response Range": f"{self.df[probe]['response_threshold_lower']:.1f} - {self.df[probe]['response_threshold_upper']:.1f}",
            }

        # Then sort if requested, creating a new dictionary with sorted probes
        if sort_by_abs_fc:
            data = {
                probe: {**data[probe], "_abs_fc": f"{data[probe]['_abs_fc']:.3f}"}
                for probe in sorted(
                    data.keys(),
                    key=lambda x: data[x]["_abs_fc"],
                    reverse=True,
                )
            }
        else:
            # Just convert _abs_fc to string without sorting
            data = {
                probe: {**data[probe], "_abs_fc": f"{data[probe]['_abs_fc']:.3f}"}
                for probe in data
            }

        return data

    def aggregate_probe_diagnostics(
        self,
        cds_threshold: float,
        conc_units: str,
        *,
        apply_cds_threshold: bool = True,
    ) -> dict[str, dict[str, Any]]:
        """Aggregate diagnostic data across all probes.

        Inputs:
            self.df (pd.Series): BIFROST summary data containing probe information
            self.stats (Dict[str, Union[np.ndarray, float, int]]): Summary statistics dictionary
                containing probe data, computed by calculate_summary_statistics(). Contains keys:
                - probe: Array of probe identifiers
                - max_conc: Maximum tested concentration

        Args:
            cds_threshold: The CDS threshold value
            conc_units: String specifying concentration units
            apply_cds_threshold: Whether to apply CDS threshold filtering

        Returns:
            Dictionary mapping probe IDs to their diagnostic data

        """
        diagnostic_data = {}
        for probe in self.df["probes"]:
            probe_data = ProbeData(self.df, probe, conc_units, bifrost_data=self)
            probe_diag_data = probe_data.get_diagnostic_data(
                cds_threshold,
                apply_cds_threshold=apply_cds_threshold,
            )
            diagnostic_data.update(probe_diag_data)
        return diagnostic_data


class ProbeData:
    """Helper class to manage probe data and calculations.

    This class handles probe-specific data processing and visualization, including
    concentration-response plots and diagnostic information.

    Attributes:
        df (pd.Series): BIFROST summary data containing probe information
        probe (str): Probe identifier
        conc_units (str): Concentration units for display
        bifrost_data (BifrostData): Reference to parent BifrostData instance
        _cache (Dict[str, Any]): Cache for computed values including:
            - cds: CDS value for the probe
            - mean_pod: Mean PoD if CDS > 0
            - pod_percentiles: Tuple of (percentiles, percentile_values, widths, labels)
            - response_data: Tuple of (treatment_x, treatment_y, control_y, response_x, response)

    """

    def __init__(
        self,
        df: pd.Series,
        probe: str,
        conc_units: str,
        bifrost_data: "BifrostData",
    ) -> None:
        """Initialize ProbeData with probe information.

        Args:
            df: BIFROST summary data containing probe information
            probe: Probe identifier
            conc_units: Concentration units for display
            bifrost_data: Reference to parent BifrostData instance

        Raises:
            KeyError: If probe data is missing from summary
            ValueError: If probe data is malformed

        """
        self.df = df
        self.probe = probe
        self.conc_units = conc_units
        self.bifrost_data = bifrost_data
        self._cache = {}
        # Pre-calculate commonly used values
        self._cache["cds"] = float(df[probe]["cds"])
        if self._cache["cds"] > 0:
            self._cache["mean_pod"] = np.mean(df[probe]["pod"])
            self._cache["pod_percentiles"] = self._calculate_pod_percentiles()

    def _calculate_pod_percentiles(
        self,
    ) -> tuple[np.ndarray, list[int], list[float], list[str]] | None:
        """Calculate PoD percentiles and related data if CDS > 0.

        Returns:
            Tuple containing:
                - pod_percentiles: Array of PoD percentile values
                - percentiles: List of percentile values (1, 5, 10, 25, 75, 90, 95, 99)
                - pod_widths: List of widths for percentile bands
                - pod_percentile_labels: List of labels for each percentile

            Returns None if CDS <= 0

        """
        if self._cache["cds"] <= 0:
            return None
        percentiles = [1, 5, 10, 25, 75, 90, 95, 99]
        pod_percentiles = np.percentile(self.df[self.probe]["pod"], percentiles)
        pod_widths = [1, 1.5, 2, 2.5, 2.5, 2, 1.5, 1]
        pod_percentile_labels = [f"PoD {p}th percentile" for p in percentiles]
        return (pod_percentiles, percentiles, pod_widths, pod_percentile_labels)

    @property
    def cds(self) -> float:
        """Get CDS value for the probe.

        Returns:
            Concentration-Dependency Score (CDS) value

        """
        return self._cache["cds"]

    @property
    def mean_pod(self) -> float | None:
        """Calculate mean PoD if CDS > 0.

        Returns:
            Mean PoD value if CDS > 0, None otherwise

        """
        return self._cache.get("mean_pod")

    @property
    def pod_percentiles(
        self,
    ) -> tuple[np.ndarray, list[int], list[float], list[str]] | None:
        """Calculate PoD percentiles and related data if CDS > 0.

        Returns:
            Tuple containing:
                - pod_percentiles: Array of PoD percentile values
                - percentiles: List of percentile values
                - pod_widths: List of widths for percentile bands
                - pod_percentile_labels: List of labels for each percentile

            Returns None if CDS <= 0

        """
        return self._cache.get("pod_percentiles")

    def get_response_data(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Get response data for plotting.

        Inputs:
            self.df (pd.Series): BIFROST summary data containing probe information
            self.probe (str): Probe identifier
            self._cache (Dict[str, Any]): Cache for computed values

        Returns:
            Tuple containing:
                - treatment_x: Array of treatment concentrations
                - treatment_y: Array of normalized treatment counts
                - control_y: Array of normalized control counts
                - response_x: Array of x-values for response curve
                - response: Array of response curve values

        Note:
            Results are cached in self._cache["response_data"] for efficiency

        """
        if "response_data" not in self._cache:
            # Pre-calculate arrays to avoid repeated calculations
            conc = 10 ** np.array(
                self.df["conc"],
            )  # Convert log10 concentrations to actual values
            conc_index = np.array(self.df["conc_index"])
            count = np.array(self.df[self.probe]["count"])
            total_count = np.array(self.df["total_count"])
            median_total_count = np.median(total_count)

            # Use boolean masks for faster indexing
            treatment_mask = conc_index > 0
            control_mask = conc_index == 0

            # Calculate all values at once
            treatment_x = conc[conc_index[treatment_mask] - 1]
            treatment_y = (
                count[treatment_mask] / total_count[treatment_mask]
            ) * median_total_count
            control_y = (
                count[control_mask] / total_count[control_mask]
            ) * median_total_count
            response_x = 10 ** np.array(
                self.df[self.probe]["x"],
            )  # Convert log10 x values to actual values
            response = np.array(self.df[self.probe]["response"])

            self._cache["response_data"] = (
                treatment_x,
                treatment_y,
                control_y,
                response_x,
                response,
            )
        return self._cache["response_data"]

    def create_probe_plot(self) -> str:
        """Create a concentration-response plot for this probe using Plotly.

        This method generates an interactive HTML plot showing:
        - Treatment data points
        - Control levels
        - Response curve with credible intervals
        - PoD distribution (if CDS > 0)
        - Mean PoD (if CDS > 0)

        Inputs:
            self.df (pd.Series): BIFROST summary data containing probe information
            self.probe (str): Probe identifier
            self.conc_units (str): Concentration units for display
            self.bifrost_data (BifrostData): Reference to parent BifrostData instance
            self._cache (Dict[str, Any]): Cache for computed values including:
                - cds: CDS value for the probe
                - mean_pod: Mean PoD if CDS > 0
                - response_data: Tuple of response data arrays

        Returns:
            HTML string containing the interactive plot

        Note:
            The plot is styled consistently with other BIFROST plots and includes
            hover information and interactive features.

        """
        # Create plot
        logger.info("Creating concentration-response plot for probe %s", self.probe)

        treatment_x, treatment_y, control_y, response_x, response = (
            self.get_response_data()
        )

        ymax = float(
            max(np.max(treatment_y), np.max(control_y), np.max(response[2])) * 1.1,
        )

        fig = go.Figure()

        if self._cache["cds"] > 0:
            mean_pod = self.mean_pod
            # Use BifrostData instance for histogram calculation
            weights, bin_edges = self.bifrost_data.fit_pod_histogram(
                np.array(self.df[self.probe]["pod"]),
                self.df["n_samp"],
            )

            if weights is not None and bin_edges is not None:
                bin_edges = 10**bin_edges
                weights = weights / np.max(weights) * 0.5 * self._cache["cds"]

                shapes = []
                for i, weight in enumerate(weights):
                    shapes.append(
                        {
                            "type": "rect",
                            "line": {"color": "rgba(102, 51, 153, 0)"},
                            "fillcolor": f"rgba(102, 51, 153, {weight})",
                            "layer": "below",
                            "x0": bin_edges[i],
                            "x1": bin_edges[i + 1],
                            "xref": "x",
                            "y0": 0,
                            "y1": 1,
                            "yref": "paper",
                        },
                    )
                fig.update_layout(shapes=shapes)

        for i, y in enumerate(control_y):
            fig.add_hline(
                y=y,
                line={"color": "#CCCCCC", "width": 0.6, "dash": "dash"},
                name="Solvent control" if i == 0 else None,
                showlegend=i == 0,
                layer="below",
            )

        if self._cache["cds"] > 0:
            fig.add_vline(
                x=float(10**mean_pod),
                line={"color": "#663399", "width": 1.5, "dash": "solid"},
                name="Mean PoD | Response",
                showlegend=True,
            )

        fig.add_trace(
            go.Scatter(
                x=response_x,
                y=response[0],
                mode="lines",
                line={"color": "#FF8080", "width": 1.5, "dash": "dash"},
                name="90% credible interval",
                showlegend=True,
            ),
        )

        fig.add_trace(
            go.Scatter(
                x=response_x,
                y=response[2],
                mode="lines",
                line={"color": "#FF8080", "width": 1.5, "dash": "dash"},
                fill="tonexty",
                fillcolor="rgba(255, 128, 128, 0.1)",
                name=None,
                showlegend=False,
            ),
        )

        fig.add_trace(
            go.Scatter(
                x=response_x,
                y=response[1],
                mode="lines",
                line={"color": "#FF0000", "width": 1.5},
                name="Median response",
                showlegend=True,
            ),
        )

        fig.add_trace(
            go.Scatter(
                x=treatment_x,
                y=treatment_y,
                mode="markers",
                marker={
                    "symbol": "x",
                    "size": 7,
                    "color": "#000000",
                    "line": {"width": 0.3},
                },
                name="Treatment data",
                showlegend=True,
                hovertemplate=(
                    f"Concentration: %{{x:.2g}} {self.conc_units}<br>"
                    "Normalized count: %{y:.2f}<br>"
                    "<extra></extra>"
                ),
            ),
        )

        fig.update_layout(
            xaxis={
                "title": {
                    "text": f"Concentration ({self.conc_units})",
                    "font": {"size": 12},
                },
                "type": "log",
                "showgrid": True,
                "gridcolor": "#E5E5E5",
                "gridwidth": 1,
                "showline": True,
                "linewidth": 1,
                "linecolor": "#000000",
                "range": [
                    np.log10(float(10 ** (self.df["conc"][0] - 1))),
                    np.log10(float(10 ** (self.df["conc"][-1] + 1))),
                ],
            },
            yaxis={
                "title": {"text": "Normalised count", "font": {"size": 12}},
                "showgrid": True,
                "gridcolor": "#E5E5E5",
                "gridwidth": 1,
                "showline": True,
                "linewidth": 1,
                "linecolor": "#000000",
                "range": [0, ymax],
            },
            showlegend=True,
            legend={
                "yanchor": "bottom",
                "y": -0.3,
                "xanchor": "center",
                "x": 0.5,
                "font": {"size": 11},
                "bgcolor": "rgba(255, 255, 255, 0.8)",
                "orientation": "h",
            },
            margin={"l": 60, "r": 20, "t": 40, "b": 80},
            height=400,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font={"family": "Arial, sans-serif", "size": 11},
            uirevision=True,
            hovermode="closest",
            hoverdistance=10,
            spikedistance=10,
        )

        plot_html = fig.to_html(
            full_html=False,
            include_plotlyjs="cdn",
            config={
                "responsive": True,
                "displayModeBar": True,
                "staticPlot": False,
                "showTips": True,
                "showLink": False,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": f"bifrost_plot_{self.probe}",
                    "height": 400,
                    "width": None,
                    "scale": 2,
                },
            },
        )

        logger.info("Completed concentration-response plot for %s", self.probe)
        return plot_html

    def get_diagnostic_data(
        self,
        cds_threshold: float,
        *,
        apply_cds_threshold: bool = True,
    ) -> dict[str, dict[str, Any]]:
        """Create diagnostic data for this single probe.

        This method generates diagnostic information including:
        - CDS and PoD values
        - Model convergence checks (Treedepth, Divergences, E-BFMI, ESS, R-hat)
        - Response range
        - Regularization recommendations

        Inputs:
            self.df (pd.Series): BIFROST summary data containing probe information
            self.probe (str): Probe identifier
            self.conc_units (str): Concentration units for display
            self._cache (Dict[str, Any]): Cache for computed values including:
                - cds: CDS value for the probe
                - mean_pod: Mean PoD if CDS > 0

        Args:
            cds_threshold: The CDS threshold value
            apply_cds_threshold: Whether to apply CDS threshold filtering

        Returns:
            Dictionary containing diagnostic data for this probe, with keys:
                - CDS: CDS value
                - CDS_str: Formatted CDS string
                - Mean PoD: Mean PoD value
                - Mean PoD_str: Formatted PoD string
                - Treedepth: Check result (✓/✗)
                - Divergences: Check result (✓/✗)
                - E-BFMI: Check result (✓/✗)
                - ESS: Check result (✓/✗)
                - R-hat: Check result (✓/✗)
                - High R-hat Parameters: Number of parameters with R-hat > 1.01
                - Response Range: Range of response thresholds
                - Needs Regularization: Warning if regularization needed (⚠️/✓)
                - _sort_score: Score for sorting probes by biological relevance

        Note:
            Returns empty dictionary if apply_cds_threshold is True and CDS <= cds_threshold

        """
        if apply_cds_threshold and self._cache["cds"] <= cds_threshold:
            return {}

        diag_text = self.df[self.probe]["diagnostics"]

        # Parse individual checks
        checks = {
            "Treedepth": "✓" if "Treedepth satisfactory" in diag_text else "✗",
            "Divergences": "✓" if "No divergent transitions" in diag_text else "✗",
            "E-BFMI": "✓" if "E-BFMI satisfactory" in diag_text else "✗",
            "ESS": "✓" if "effective sample size satisfactory" in diag_text else "✗",
            "R-hat": (
                "✓"
                if "Rank-normalized split R-hat values satisfactory for all parameters"
                in diag_text
                else "✗"
            ),
        }

        # Calculate biological relevance score
        cds = self._cache["cds"]
        mean_pod = self.mean_pod if self.mean_pod is not None else float("inf")

        bio_score = 1 if cds > cds_threshold else 0
        if not np.isinf(mean_pod):
            bio_score += (self.df["max_conc"] - mean_pod) / self.df["max_conc"]

        # Extract R-hat parameters if present
        rhat_params = []
        if "R-hat greater than 1.01" in diag_text:
            start_idx = diag_text.find("greater than 1.01:") + len("greater than 1.01:")
            end_idx = diag_text.find("Such high values")
            if start_idx > 0 and end_idx > start_idx:
                params_text = diag_text[start_idx:end_idx].strip()
                rhat_params = [p.strip() for p in params_text.split() if p.strip()]

        # Check for regularization recommendation
        needs_regularization = (
            "You should consider regularizating your model with additional prior information or a more effective parameterization"
            in diag_text
        )

        # Format Mean PoD
        if not np.isnan(mean_pod):
            mean_pod_value = 10**mean_pod
            mean_pod_str = f"{mean_pod_value:.2g} {self.conc_units}"
        else:
            mean_pod_value = float("inf")
            mean_pod_str = "No response"

        # Return diagnostic data
        return {
            self.probe: {
                "CDS": float(cds),
                "CDS_str": f"{cds:.3f}",
                "Mean PoD": mean_pod_value,
                "Mean PoD_str": mean_pod_str,
                "Treedepth": checks["Treedepth"],
                "Divergences": checks["Divergences"],
                "E-BFMI": checks["E-BFMI"],
                "ESS": checks["ESS"],
                "R-hat": checks["R-hat"],
                "High R-hat Parameters": str(len(rhat_params)) if rhat_params else "0",
                "Response Range": f"{self.df[self.probe]['response_threshold_lower']:.1f} - {self.df[self.probe]['response_threshold_upper']:.1f}",
                "Needs Regularization": "⚠️" if needs_regularization else "✓",
                "_sort_score": bio_score,
            },
        }
