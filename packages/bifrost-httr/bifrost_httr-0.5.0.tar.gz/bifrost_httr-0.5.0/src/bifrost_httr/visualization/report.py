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
"""MultiQC report generation for BIFROST analysis.

This module provides the BifrostMultiQCReport class for generating comprehensive
MultiQC reports from BIFROST analysis results, including summary tables, plots,
and diagnostic information.
"""

import os
from pathlib import Path
from typing import Any, Optional, Union  # noqa: F401

import multiqc
import numpy as np
from multiqc.plots import scatter, table

from bifrost_httr.core.statistics import (
    calculate_global_pod,
    get_probe_weights_from_global_pod,
)
from bifrost_httr.utils.logging import get_logger

from .data import BifrostData, ProbeData
from .template_loader import get_template_loader

# Configure logging
logger = get_logger(__name__)


class BifrostMultiQCReport:
    """Generate comprehensive MultiQC reports for BIFROST analysis results.

    This class provides functionality to create detailed HTML reports using MultiQC,
    visualizing and summarizing BIFROST high-throughput transcriptomics analysis results.
    The reports include:

    1. Summary statistics and global metrics
    2. Interactive concentration-response plots
    3. Point of Departure (PoD) analysis results
    4. Fold change analysis for up/down regulated probes
    5. Concentration-Dependency Score (CDS) statistics
    6. Diagnostic information and quality metrics

    The generated reports feature:
    - Interactive plots (optional)
    - Customizable thresholds and filtering
    - Comprehensive probe-level statistics
    - Publication-ready visualizations
    - Exportable HTML format with embedded data

    Example:
        >>> report = BifrostMultiQCReport(
        ...     bifrost_data,
        ...     test_substance="Compound X",
        ...     cell_type="HepaRG",
        ...     timepoint="24h",
        ...     conc_units="µM",
        ... )
        >>> report.create_report()

    """

    def __init__(
        self,
        bifrost_data: BifrostData,
        **kwargs: str | float | bool,
    ) -> None:
        """Initialize a BIFROST MultiQC report generator.

        Args:
            bifrost_data: Processed BIFROST data object.
            **kwargs: Additional report configuration parameters:
                test_substance (str): Name of the test substance
                cell_type (str): Type of cell used
                timepoint (str): Exposure duration
                conc_units (str): Concentration units
                output_name (str): Output report filename
                interactive_plots (bool): Whether to force interactive plots
                n_fold_change_probes (float): Number of up/down regulated probes to show
                cds_threshold (float): CDS threshold for filtering
                n_lowest_means (float): Number of lowest mean PoD probes to show
                n_pod_stats (float): Number of probes in PoD statistics table
                plot_height (float): Height of concentration-response plots
                pod_vs_fc_height (float): Height of PoD vs Fold Change plot
                no_cds_threshold (bool): Whether to skip CDS threshold filtering
                custom_templates (str): Path to custom template YAML file

        """
        self.data = bifrost_data
        for k, v in kwargs.items():
            setattr(self, k, v)

        # Initialize template loader with custom templates if provided
        custom_template_file = kwargs.get("custom_templates")
        self.template_loader = get_template_loader(custom_template_file)

    def format_pod(self, pod: float, max_dose: float) -> str:
        """Format PoD value for display.

        Args:
            pod: PoD value to format.
            max_dose: Maximum dose value for comparison.

        Returns:
            Formatted string representation of PoD value.

        """
        if pod < max_dose:
            return self.format_float(10**pod)
        return f">{self.format_float(10 ** pod)}"

    def format_float(self, x: float) -> str:
        """Format float to string with two significant figures.

        Args:
            x: Float value to format.

        Returns:
            String representation of float with two significant figures.

        """
        return f'{float(f"{x:.2g}"):g}'

    def _format_probe_description(
        self,
        probe: str,
        *,
        include_fold_change: bool = False,
    ) -> str:
        """Format probe description using templates.

        Args:
            probe: Probe ID.
            include_fold_change: Whether to include fold change information.

        Returns:
            Formatted probe description string.

        """
        cds = self.data.df[probe]["cds"]
        mean_pod = self.format_float(10 ** np.mean(self.data.df[probe]["pod"]))

        if include_fold_change:
            log2_fc = self.data.stats["l2fc"][self.data.stats["probe"] == probe][0]
            return self.template_loader.get_template(
                "probe_description_with_fc",
            ).format(
                cds=cds,
                mean_pod=mean_pod,
                conc_units=self.conc_units,
                log2_fc=log2_fc,
            )
        return self.template_loader.get_template("probe_description").format(
            cds=cds,
            mean_pod=mean_pod,
            conc_units=self.conc_units,
        )

    def _get_common_table_headers(
        self,
        fold_change_description: str = "Maximum fold change in expression",
    ) -> dict[str, dict[str, Any]]:
        """Get common table headers for probe summary tables.

        Args:
            fold_change_description: Description for the fold change column.

        Returns:
            Dictionary of table headers with consistent formatting.

        """
        return {
            "CDS": {
                "title": "CDS",
                "description": "Concentration-Dependency Score",
            },
            "Mean PoD": {
                "title": f"Mean PoD ({self.conc_units})",
                "description": "Mean point of departure",
            },
            "Log2 Fold Change": {
                "title": "Log2 Fold Change",
                "description": fold_change_description,
            },
            "Global PoD Weight": {
                "title": "Global PoD Weight",
                "description": "Weight in global PoD calculation",
            },
            "Response Range": {
                "title": "Response Range",
                "description": "Range of response thresholds",
            },
        }

    def _get_module_name_with_cds(
        self,
        base_name: str,
        *,
        apply_cds_threshold: bool,
    ) -> str:
        """Generate module name with conditional CDS filtering suffix.

        Args:
            base_name: Base module name.
            apply_cds_threshold: Whether CDS threshold filtering is applied.

        Returns:
            Module name with conditional CDS suffix.

        """
        cds_suffix = f" (CDS > {self.cds_threshold})" if apply_cds_threshold else ""
        return f"{base_name}{cds_suffix}"

    def _get_module_info_with_cds(
        self,
        base_info: str,
        *,
        apply_cds_threshold: bool,
    ) -> str:
        """Generate module info with conditional CDS filtering suffix.

        Args:
            base_info: Base module info.
            apply_cds_threshold: Whether CDS threshold filtering is applied.

        Returns:
            Module info with conditional CDS suffix.

        """
        cds_suffix = (
            f" (filtered by CDS > {self.cds_threshold})" if apply_cds_threshold else ""
        )
        return f"{base_info}{cds_suffix}"

    def _get_plot_elements_description(
        self,
        cds_threshold: float,
        *,
        apply_cds_threshold: bool = False,
    ) -> str:
        """Generate the common plot elements description used across multiple sections.

        This is an internal method used for generating plot descriptions in the report.

        Inputs:
            self.cds_threshold (float): The CDS threshold value used for filtering
            self.conc_units (str): Concentration units for display

        Args:
            cds_threshold: The CDS threshold value to include in description
            apply_cds_threshold: Whether CDS threshold filtering is applied

        Returns:
            HTML string containing the plot elements description with:
            - Treatment data points (black X markers)
            - Control levels (horizontal grey dashed lines)
            - Response curve with credible intervals (red bands)
            - PoD distribution (purple bands)
            - Mean PoD (purple vertical line)
            - CDS information

        """
        cds_info = (
            " with threshold = " + str(cds_threshold) if apply_cds_threshold else ""
        )
        return self.template_loader.get_template("plot_elements").format(
            cds_info=cds_info,
        )

    def _create_table_plot(
        self,
        data: dict[str, dict[str, str]],
        headers: dict[str, dict[str, Any]],
        table_id: str,
        title: str,
        *,
        sort_by_abs_fc: bool = False,
    ) -> table.plot:
        """Create a MultiQC table plot with common configuration.

        This is an internal method used for creating table plots in the report.

        Inputs:
            self.plot_height (int): Height of plots in pixels
            self.interactive_plots (bool): Whether to force interactive plots

        Args:
            data: Dictionary mapping probe IDs to their data dictionaries
            headers: Dictionary defining column headers and their properties:
                - title: Display name for the column
                - description: Tooltip text
                - format: Optional format string
                - cond_formatting_rules: Optional conditional formatting rules
            table_id: Unique identifier for the table
            title: Display title for the table
            sort_by_abs_fc: Whether to sort by absolute fold change

        Returns:
            MultiQC table plot object configured with:
            - Common styling and layout
            - Optional sorting by absolute fold change
            - Column headers with descriptions
            - Conditional formatting if specified
            - Interactive features if enabled

        Note:
            If sort_by_abs_fc is True, adds a hidden _abs_fc column for sorting

        """
        pconfig = {
            "id": table_id,
            "title": title,
            "namespace": "BIFROST",
            "no_violin": True,
            "scale": False,  # Disable automatic scaling and coloring
            "sort_rows": False,  # Disable automatic sorting
            "col1_header": "Probe",  # This will label the first column as "Metric"
        }

        if sort_by_abs_fc:
            # Add _abs_fc to headers with supported options only
            headers["_abs_fc"] = {
                "title": "_abs_fc",
                "hidden": True,
                "description": "Absolute fold change (for sorting)",
                "placement": 0,  # Ensure it's the first column for sorting
            }

        return table.plot(data=data, headers=headers, pconfig=pconfig)

    def create_report(self) -> None:  # noqa: C901, PLR0915, PLR0912
        """Generate the complete BIFROST MultiQC report.

        This method orchestrates the creation of all report sections and components,
        including summary statistics, plots, and diagnostic information.

        Inputs:
            self.data (BifrostData): Processed BIFROST data
            self.test_substance (str): Name of the test substance
            self.cell_type (str): Type of cell used
            self.timepoint (str): Exposure duration
            self.conc_units (str): Concentration units
            self.output_name (str): Output report filename
            self.interactive_plots (bool): Whether to force interactive plots
            self.n_fold_change_probes (int): Number of up/down regulated probes to show
            self.cds_threshold (float): CDS threshold for filtering
            self.n_lowest_means (int): Number of lowest mean PoD probes to show
            self.n_pod_stats (int): Number of probes in PoD statistics table
            self.plot_height (int): Height of concentration-response plots
            self.pod_vs_fc_height (int): Height of PoD vs Fold Change plot
            self.no_cds_threshold (bool): Whether to skip CDS threshold filtering

        The report includes:
        1. Introduction and overview
        2. Summary statistics table
        3. PoD vs Fold Change plot
        4. Concentration-response plots for:
            - Probes with non-zero global PoD weight
            - Most up/down regulated probes
            - Probes with lowest mean PoD
        5. Probe-level PoD statistics table
        6. Diagnostic summary table

        Raises:
            Exception: If report generation fails

        """
        logger.info(
            "Starting report generation for %s on %s",
            self.test_substance,
            self.cell_type,
        )

        # Convert no_cds_threshold to apply_cds_threshold (inverted logic)
        apply_cds_threshold = not self.no_cds_threshold

        # Configure MultiQC for interactive plots if requested
        if self.interactive_plots:
            os.environ["MULTIQC_PLOTS_FORCE_INTERACTIVE"] = "true"

        # Initialize MultiQC
        multiqc.reset()
        multiqc.config.plots_force_flat = not self.interactive_plots
        multiqc.config.skip_generalstats = True
        multiqc.config.skip_plots = False
        multiqc.config.skip_cleanup = True

        # Verify interactive plots configuration after initialization
        if self.interactive_plots:
            multiqc.config.plots_force_interactive = True

        # Create summary table
        logger.info("Creating summary table...")
        # Create summary table - format data as a dictionary of samples (metrics)
        summary_data = {
            "Global PoD": {
                "Value": f"{self.format_float(calculate_global_pod(self.data.stats, data_type='stats')['global_pod'])} {self.conc_units}",
            },
            "Maximum tested concentration": {
                "Value": f"{self.format_float(10**self.data.stats['max_conc'])} {self.conc_units}",
            },
            "Number of probes analyzed": {"Value": str(len(self.data.stats["probe"]))},
            "Number of hits": {
                "Value": str(
                    int(
                        calculate_global_pod(self.data.stats, data_type="stats")[
                            "num_hits"
                        ],
                    ),
                ),
            },
            f"Number of CDS>{self.cds_threshold} / CDS=1.0": {
                "Value": str(int(np.sum(self.data.stats["cds"] > self.cds_threshold))),
            },
            "Number of CDS=1.0": {
                "Value": str(int(np.sum(self.data.stats["cds"] == 1.0))),
            },
        }

        # Add minimum responding probe(s)
        global_pod_results = calculate_global_pod(self.data.stats, data_type="stats")
        weights = get_probe_weights_from_global_pod(global_pod_results)
        valid_probes = weights["probe"][weights["probe"] != "Max. conc."]
        if len(valid_probes) > 0:
            # Sort by weight and get the top probe
            order = np.argsort(weights["weight"][weights["probe"] != "Max. conc."])[
                ::-1
            ]
            top_probe = valid_probes[order][0]
            top_weight = weights["weight"][weights["probe"] != "Max. conc."][order][0]
            top_cds = weights["cds"][weights["probe"] != "Max. conc."][order][0]
            top_pod = weights["min_mean"][weights["probe"] != "Max. conc."][order][0]

            summary_data["Minimum responding probe"] = {
                "Value": f"{top_probe}, weight={self.format_float(top_weight)}, CDS={self.format_float(top_cds)}, Mean PoD={self.format_float(top_pod)} {self.conc_units}",
            }

        # Add largest fold changes
        if len(self.data.stats["l2fc"]) > 0:
            max_fc_idx = np.argmax(self.data.stats["l2fc"])
            min_fc_idx = np.argmin(self.data.stats["l2fc"])
            summary_data["Largest fold increase"] = {
                "Value": self.data.stats["probe"][max_fc_idx],
            }
            summary_data["Largest fold decrease"] = {
                "Value": self.data.stats["probe"][min_fc_idx],
            }

        # Add summary table to report
        summary_table = self._create_table_plot(
            data=summary_data,
            headers={"Value": {"title": "Value"}},
            table_id="bifrost_summary",
            title="BIFROST Analysis Summary",
        )

        # Check if there are any qualifying probes for the PoD vs fold change plot
        filtered_stats = self.data.filter_summary_statistics(self.cds_threshold)
        has_qualifying_probes = len(filtered_stats["l2fc"]) > 0

        # Prepare plot or no-data content
        pod_vs_fc_plot = None
        pod_vs_fc_content = None

        if has_qualifying_probes:
            # Create PoD vs fold-change plot data
            pod_vs_fc_data = {
                "Probe": [
                    {  # Empty string as dataset name to avoid showing in tooltips
                        "x": float(x),  # Convert numpy float to Python float
                        "y": float(y),  # Convert numpy float to Python float
                        "text": str(text),  # Convert numpy string to Python string
                        "name": str(text),  # Add name for hover text
                        "annotate": False,  # Turn off automatic sample labelling
                    }
                    for x, y, text in zip(
                        10 ** filtered_stats["pod"],
                        filtered_stats["l2fc"],
                        filtered_stats["probe"],
                        strict=False,
                    )
                ],
            }

            # Calculate y-axis limits
            ymin, ymax = (
                min(filtered_stats["l2fc"].min(), -2) - 1,
                max(filtered_stats["l2fc"].max(), 2) + 1,
            )

            # Calculate x-axis maximum
            xmax = (
                10 ** np.array(filtered_stats["conc"]).max() * 2
            )  # Double the max concentration for padding

            # Calculate x-axis clim min
            x_clipmin = min(10 ** np.array(filtered_stats["conc"]).min() / 2,
                            10 ** np.array(filtered_stats["pod"]).min() / 2)

            # Create scatter plot using MultiQC's scatter plot type
            pod_vs_fc_plot = scatter.plot(
                pod_vs_fc_data,
                pconfig={
                    "id": "pod_vs_fc",
                    "title": f'PoD vs Fold Change{" (CDS > " + str(self.cds_threshold) + ")" if apply_cds_threshold else ""}',
                    "xlab": f"Mean PoD | Response ({self.conc_units})",
                    "ylab": "Max./min. log2 fold-change",
                    "xlog": True,
                    "xmin": 0,  # Set axis minimum to 0
                    "xmax": xmax,  # Set axis maximum based on data
                    "x_clipmin": x_clipmin,  # Clip data points below 0.01
                    "x_clipmax": xmax,  # Clip data points above 100
                    "ymin": ymin,  # Set y-axis minimum
                    "ymax": ymax,  # Set y-axis maximum
                    "marker_size": 5,
                    "marker_line_width": 1,
                    "color": "black",  # Use color instead of marker_line_color
                    "opacity": 1.0,  # Set full opacity
                    "showlegend": False,  # Hide legend
                    "height": self.pod_vs_fc_height,  # Make plot taller to accommodate labels
                    "x_lines": [  # Add vertical lines using x_lines
                        {
                            "value": float(
                                calculate_global_pod(
                                    self.data.stats,
                                    data_type="stats",
                                )["global_pod"],
                            ),
                            "color": "#FF0000",  # Red
                            "width": 1,
                            "dash": "solid",
                            "label": "Global PoD",
                        },
                    ]
                    + [
                        {
                            "value": float(conc),
                            "color": "#D3D3D3",  # Light gray
                            "width": 1,
                            "dash": "dash",
                        }
                        for conc in 10 ** np.array(filtered_stats["conc"])
                    ],
                    "y_lines": [  # Add horizontal line at y=0
                        {
                            "value": 0,
                            "color": "#CCCCCC",  # Light gray
                            "width": 1,
                            "dash": "dash",
                        },
                    ],
                },
            )
        else:
            # Create no-data message content
            pod_vs_fc_content = self.template_loader.get_template(
                "pod_vs_fc_no_data",
            ).format(
                cds_filter_reason=(
                    " with CDS > " + str(self.cds_threshold)
                    if apply_cds_threshold
                    else ""
                ),
                cds_threshold=self.cds_threshold,
            )

        # Create main BIFROST module for introduction and summary
        main_module = multiqc.BaseMultiqcModule(
            name="General",
            anchor="bifrost",
            href="https://github.com/your-repo/bifrost",
            info="BIFROST HTTr Analysis Report",
        )

        # Add introduction to main module
        main_module.add_section(
            name="Introduction",
            anchor="bifrost_intro",
            content=self.template_loader.get_template("introduction").format(
                cell_type=self.cell_type,
                timepoint=self.timepoint,
                test_substance=self.test_substance,
            ),
        )

        # Add summary section to main module
        main_module.add_section(
            name="Summary Statistics",
            anchor="bifrost_summary",
            plot=summary_table,
            description=self.template_loader.get_template(
                "summary_stats_description",
            ).format(
                cds_threshold=self.cds_threshold,
            ),
        )

        # Add PoD vs fold-change section to main module
        if has_qualifying_probes:
            main_module.add_section(
                name="PoD vs Fold Change",
                anchor="bifrost_pod_vs_fc",
                plot=pod_vs_fc_plot,
                description=self.template_loader.get_template(
                    "pod_vs_fc_description",
                ).format(
                    cds_info=(
                        " for probes with CDS > " + str(self.cds_threshold)
                        if apply_cds_threshold
                        else ""
                    ),
                    cds_threshold_note=(
                        self.template_loader.get_template("cds_threshold_note").format(
                            cds_threshold=self.cds_threshold,
                        )
                        if apply_cds_threshold
                        else ""
                    ),
                ),
            )
        else:
            main_module.add_section(
                name="PoD vs Fold Change",
                anchor="bifrost_pod_vs_fc",
                content=pod_vs_fc_content,
            )

        # Create module for plot elements guide
        plot_guide_module = multiqc.BaseMultiqcModule(
            name="Concentration/ Response Plot Guide",
            anchor="bifrost_plot_guide",
        )

        # Add plot elements guide section
        plot_guide_module.add_section(
            anchor="bifrost_plot_elements",
            content=self.template_loader.get_template("plot_elements_guide").format(
                plot_elements=self._get_plot_elements_description(
                    cds_threshold=self.cds_threshold,
                    apply_cds_threshold=apply_cds_threshold,
                ),
                conc_units=self.conc_units,
            ),
        )

        # Create module for weighted plots
        weighted_module = multiqc.BaseMultiqcModule(
            name=self._get_module_name_with_cds(
                "Probes with Non-zero Global PoD Weight",
                apply_cds_threshold=apply_cds_threshold,
            ),
            anchor="bifrost_weighted",
            info=self._get_module_info_with_cds(
                "Concentration-response plots for probes contributing to global PoD",
                apply_cds_threshold=apply_cds_threshold,
            ),
        )

        # Create module for fold change plots
        fc_module = multiqc.BaseMultiqcModule(
            name="Fold Change Plots",
            anchor="bifrost_fc_plots",
            info="Concentration-response plots for probes with the largest fold changes",
        )

        # Create module for lowest means plots
        lowest_means_module = multiqc.BaseMultiqcModule(
            name=self._get_module_name_with_cds(
                "Lowest Mean PoD Plots",
                apply_cds_threshold=apply_cds_threshold,
            ),
            anchor="bifrost_lowest_means_plots",
            info=self._get_module_info_with_cds(
                "Concentration-response plots for probes with lowest mean PoD",
                apply_cds_threshold=apply_cds_threshold,
            ),
        )

        # Add plots for probes with non-zero global PoD weight to weighted module
        valid_probes = weights["probe"][weights["probe"] != "Max. conc."]
        probes_to_plot = valid_probes[
            np.argsort(weights["weight"][weights["probe"] != "Max. conc."])
        ]
        logger.info(
            "Found %d probes with non-zero global PoD weight",
            len(probes_to_plot),
        )

        if len(probes_to_plot) > 0:
            # Add overview section
            weighted_module.add_section(
                name="Overview",
                anchor="bifrost_weighted_overview",
                content=self.template_loader.get_template("weighted_overview").format(),
            )

            # Create summary table for weighted probes
            weighted_table_data = self.data.create_summary_table_data(
                probes_to_plot,
                weights,
                self.conc_units,
                sort_by_abs_fc=True,
            )
            weighted_summary_table = self._create_table_plot(
                data=weighted_table_data,
                headers=self._get_common_table_headers(),
                table_id="bifrost_weighted_summary",
                title="Summary Statistics for Probes with Non-zero Global PoD Weight",
                sort_by_abs_fc=True,
            )

            # Add summary table to weighted module
            weighted_module.add_section(
                name="Probe Summary Statistics",
                anchor="bifrost_weighted_summary",
                plot=weighted_summary_table,
                description=self.template_loader.get_template("probe_summary").format(
                    probe_type="probes contributing to the global PoD calculation",
                    sort_description="their weight in the global PoD calculation",
                ),
            )

            for probe in probes_to_plot:
                probe_data = ProbeData(
                    self.data.df,
                    probe,
                    self.conc_units,
                    bifrost_data=self.data,
                )
                conc_response_plot = probe_data.create_probe_plot()
                weighted_module.add_section(
                    name=probe,
                    anchor=f"bifrost_weighted_{probe}",
                    content=conc_response_plot,
                    description=self._format_probe_description(probe),
                )
        else:
            # Add no-data message when no probes qualify
            weighted_module.add_section(
                name="Overview",
                anchor="bifrost_weighted_overview",
                content=self.template_loader.get_template("no_data").format(
                    section_name="Probes Contributing to Global PoD",
                    section_name_lower="non-zero global PoD weight",
                    cds_filter_reason=(
                        " with CDS > " + str(self.cds_threshold)
                        if apply_cds_threshold
                        else ""
                    ),
                ),
            )

        # Add overview section to fold change module
        fc_module.add_section(
            name="Overview",
            anchor="bifrost_fc_overview",
            content=self.template_loader.get_template("fc_overview").format(
                cds_info=" that meet the CDS threshold" if apply_cds_threshold else "",
                selection_criteria=self.template_loader.get_template(
                    "probe_selection_criteria",
                ).format(
                    num_probes=self.n_fold_change_probes,
                    selection_description="the most extreme fold changes",
                    selection_criteria=(
                        " that meet the CDS threshold:" if apply_cds_threshold else ":"
                    ),
                    cds_criteria=(
                        self.template_loader.get_template("cds_criteria_list").format(
                            cds_threshold=self.cds_threshold,
                        )
                        if apply_cds_threshold
                        else ""
                    ),
                    cds_filter=(
                        self.template_loader.get_template("cds_filter_note").format(
                            cds_threshold=self.cds_threshold,
                        )
                        if apply_cds_threshold
                        else ""
                    ),
                    filtered_probes=(
                        "these filtered probes" if apply_cds_threshold else "all probes"
                    ),
                    ranking_description="the most extreme fold changes",
                ),
            ),
        )

        # Process fold change data - no CDS filtering for fold change plots
        stats = self.data.stats  # Use unfiltered stats for fold changes
        has_fold_changes = len(stats["l2fc"]) > 0
        up_probes = []
        down_probes = []

        if has_fold_changes:
            # Sort by absolute fold change magnitude
            abs_fc = np.abs(stats["l2fc"])
            index = np.argsort(abs_fc)[::-1]  # Sort in descending order

            # Get probes with largest absolute fold changes (no CDS filtering)
            up_mask = stats["l2fc"][index] > 0
            down_mask = stats["l2fc"][index] < 0
            up_probes = stats["probe"][index][up_mask][: self.n_fold_change_probes]
            down_probes = stats["probe"][index][down_mask][: self.n_fold_change_probes]

            logger.info(
                "Found %d upregulated and %d downregulated probes (no CDS filtering)",
                len(up_probes),
                len(down_probes),
            )

        # Handle upregulated probes section
        if len(up_probes) > 0:
            # Add section header with template
            fc_module.add_section(
                name="Most Upregulated Probes",
                anchor="bifrost_fc_up",
                content=self.template_loader.get_template("upregulated_probes").format(
                    n_fold_change_probes=self.n_fold_change_probes,
                ),
            )

            # Create summary table for upregulated probes
            up_table_data = self.data.create_summary_table_data(
                up_probes,
                weights,
                self.conc_units,
                sort_by_abs_fc=True,
            )
            up_summary_table = self._create_table_plot(
                data=up_table_data,
                headers=self._get_common_table_headers(
                    "Maximum positive fold change in expression",
                ),
                table_id="bifrost_fc_up_summary",
                title="Summary Statistics for Most Upregulated Probes",
                sort_by_abs_fc=True,
            )

            # Add summary table to upregulated section
            fc_module.add_section(
                name="Upregulated Probes Summary",
                anchor="bifrost_fc_up_summary",
                plot=up_summary_table,
                description=self.template_loader.get_template("probe_summary").format(
                    probe_type="the most upregulated probes",
                    sort_description="their fold change magnitude",
                ),
            )

            # Add individual probe plots
            for probe in up_probes:
                probe_data = ProbeData(
                    self.data.df,
                    probe,
                    self.conc_units,
                    bifrost_data=self.data,
                )
                conc_response_plot = probe_data.create_probe_plot()
                fc_module.add_section(
                    name=probe,
                    anchor=f"bifrost_fc_up_{probe}",
                    content=conc_response_plot,
                    description=self._format_probe_description(
                        probe,
                        include_fold_change=True,
                    ),
                )
        else:
            # Add no-data message for upregulated probes
            fc_module.add_section(
                name="Most Upregulated Probes",
                anchor="bifrost_fc_up",
                content=self.template_loader.get_template("fc_no_data").format(
                    direction="Upregulated",
                    direction_adj="positive",
                    direction_desc="increased",
                ),
            )

        # Handle downregulated probes section
        if len(down_probes) > 0:
            # Add section header with template
            fc_module.add_section(
                name="Most Downregulated Probes",
                anchor="bifrost_fc_down",
                content=self.template_loader.get_template(
                    "downregulated_probes",
                ).format(
                    n_fold_change_probes=self.n_fold_change_probes,
                ),
            )

            # Create summary table for downregulated probes
            down_table_data = self.data.create_summary_table_data(
                down_probes,
                weights,
                self.conc_units,
                sort_by_abs_fc=True,
            )
            down_summary_table = self._create_table_plot(
                data=down_table_data,
                headers=self._get_common_table_headers(
                    "Maximum negative fold change in expression",
                ),
                table_id="bifrost_fc_down_summary",
                title="Summary Statistics for Most Downregulated Probes",
                sort_by_abs_fc=True,
            )

            # Add summary table to downregulated section
            fc_module.add_section(
                name="Downregulated Probes Summary",
                anchor="bifrost_fc_down_summary",
                plot=down_summary_table,
                description=self.template_loader.get_template("probe_summary").format(
                    probe_type="the most downregulated probes",
                    sort_description="their fold change magnitude",
                ),
            )

            # Add individual probe plots
            for probe in down_probes:
                probe_data = ProbeData(
                    self.data.df,
                    probe,
                    self.conc_units,
                    bifrost_data=self.data,
                )
                conc_response_plot = probe_data.create_probe_plot()
                fc_module.add_section(
                    name=probe,
                    anchor=f"bifrost_fc_down_{probe}",
                    content=conc_response_plot,
                    description=self._format_probe_description(
                        probe,
                        include_fold_change=True,
                    ),
                )
        else:
            # Add no-data message for downregulated probes
            fc_module.add_section(
                name="Most Downregulated Probes",
                anchor="bifrost_fc_down",
                content=self.template_loader.get_template("fc_no_data").format(
                    direction="Downregulated",
                    direction_adj="negative",
                    direction_desc="decreased",
                ),
            )

        # Get probes for lowest means module
        n_probe = len(self.data.stats["probe"])
        if apply_cds_threshold:
            mask = self.data.stats["cds"] > self.cds_threshold
            probes_to_plot = self.data.stats["probe"][mask][
                np.argsort(self.data.stats["pod"][mask])
            ][: min(np.sum(mask), self.n_lowest_means)]
        else:
            probes_to_plot = self.data.stats["probe"][
                np.argsort(self.data.stats["pod"])
            ][: min(n_probe, self.n_lowest_means)]
        logger.info(
            "Found %d probes with lowest means to plot",
            len(probes_to_plot),
        )

        if len(probes_to_plot) > 0:
            # Add overview section with selection criteria
            lowest_means_module.add_section(
                name="Overview",
                anchor="bifrost_lowest_means_overview",
                content=self.template_loader.get_template(
                    "lowest_means_overview",
                ).format(
                    selection_criteria=self.template_loader.get_template(
                        "probe_selection_criteria",
                    ).format(
                        num_probes=self.n_lowest_means,
                        selection_description="the lowest mean PoD values",
                        selection_criteria=(
                            " that meet the CDS threshold:"
                            if apply_cds_threshold
                            else ":"
                        ),
                        cds_criteria=(
                            self.template_loader.get_template(
                                "cds_criteria_list",
                            ).format(
                                cds_threshold=self.cds_threshold,
                            )
                            if apply_cds_threshold
                            else ""
                        ),
                        cds_filter=(
                            self.template_loader.get_template("cds_filter_note").format(
                                cds_threshold=self.cds_threshold,
                            )
                            if apply_cds_threshold
                            else ""
                        ),
                        filtered_probes=(
                            "these filtered probes"
                            if apply_cds_threshold
                            else "all probes"
                        ),
                        ranking_description="the lowest mean PoD values",
                    ),
                ),
            )

            # Create summary table for lowest means probes
            lowest_means_table_data = self.data.create_summary_table_data(
                probes_to_plot,
                weights,
                self.conc_units,
                sort_by_abs_fc=True,
            )
            lowest_means_summary_table = self._create_table_plot(
                data=lowest_means_table_data,
                headers=self._get_common_table_headers(),
                table_id="bifrost_lowest_means_summary",
                title="Summary Statistics for Most Sensitive Probes (CDS > 0.5)",
                sort_by_abs_fc=True,
            )

            # Add summary table to lowest means module
            lowest_means_module.add_section(
                name="Probe Summary Statistics",
                anchor="bifrost_lowest_means_summary",
                plot=lowest_means_summary_table,
                description=self.template_loader.get_template(
                    "lowest_means_summary_description",
                ).format(
                    cds_threshold=self.cds_threshold,
                ),
            )

            # Add individual probe plots
            for probe in probes_to_plot:
                probe_data = ProbeData(
                    self.data.df,
                    probe,
                    self.conc_units,
                    bifrost_data=self.data,
                )
                conc_response_plot = probe_data.create_probe_plot()
                lowest_means_module.add_section(
                    name=probe,
                    anchor=f"bifrost_lowest_means_{probe}",
                    content=conc_response_plot,
                    description=self._format_probe_description(probe),
                )
        else:
            # Add no-data message when no probes qualify
            lowest_means_module.add_section(
                name="Overview",
                anchor="bifrost_lowest_means_overview",
                content=self.template_loader.get_template("no_data").format(
                    section_name="Probes with Valid PoD Estimates",
                    section_name_lower="valid PoD estimates",
                    cds_filter_reason=(
                        " with CDS > " + str(self.cds_threshold)
                        if apply_cds_threshold
                        else ""
                    ),
                ),
            )

        # Create diagnostic table data with parsed checks
        diagnostic_data = self.data.aggregate_probe_diagnostics(
            self.cds_threshold,
            self.conc_units,
            apply_cds_threshold=apply_cds_threshold,
        )

        # Create module for diagnostics
        diag_module = multiqc.BaseMultiqcModule(
            name="Diagnostic Summary",
            anchor="bifrost_diagnostics",
            info="Model diagnostics and quality checks",
        )

        if len(diagnostic_data) > 0:
            # Create diagnostic table
            diagnostic_table = self._create_table_plot(
                data={
                    k: {
                        sk: v[sk]
                        for sk in [
                            "CDS_str",
                            "Mean PoD_str",
                            "Treedepth",
                            "Divergences",
                            "E-BFMI",
                            "ESS",
                            "R-hat",
                            "High R-hat Parameters",
                            "Response Range",
                            "_sort_score",
                        ]
                    }
                    for k, v in diagnostic_data.items()
                },
                headers={
                    "CDS_str": {
                        "title": "CDS",
                        "format": "{:.3f}",
                        "description": f"Concentration-Dependency Score (probability of response below max concentration, threshold = {self.cds_threshold})",
                        "cond_formatting_rules": {
                            "pass": [
                                {"gt": self.cds_threshold},
                            ],  # Highlight probes with CDS > threshold
                        },
                    },
                    "Mean PoD_str": {
                        "title": f"Mean PoD ({self.conc_units})",
                        "description": 'Mean point of departure (effect concentration). "No response" indicates no valid PoD samples.',
                        "cond_formatting_rules": {
                            "warn": [
                                {"s_eq": "No response"},
                            ],  # Highlight probes with no response
                        },
                    },
                    "Treedepth": {
                        "title": "Treedepth",
                        "description": "Sampler transitions treedepth check",
                        "cond_formatting_rules": {
                            "pass": [{"s_eq": "✓"}],  # Green for pass
                            "fail": [{"s_eq": "✗"}],  # Red for fail
                        },
                    },
                    "Divergences": {
                        "title": "Divergences",
                        "description": "Check for divergent transitions",
                        "cond_formatting_rules": {
                            "pass": [{"s_eq": "✓"}],  # Green for pass
                            "fail": [{"s_eq": "✗"}],  # Red for fail
                        },
                    },
                    "E-BFMI": {
                        "title": "E-BFMI",
                        "description": "HMC potential energy check",
                        "cond_formatting_rules": {
                            "pass": [{"s_eq": "✓"}],  # Green for pass
                            "fail": [{"s_eq": "✗"}],  # Red for fail
                        },
                    },
                    "ESS": {
                        "title": "ESS",
                        "description": "Effective sample size check",
                        "cond_formatting_rules": {
                            "pass": [{"s_eq": "✓"}],  # Green for pass
                            "fail": [{"s_eq": "✗"}],  # Red for fail
                        },
                    },
                    "R-hat": {
                        "title": "R-hat",
                        "description": "Gelman-Rubin convergence diagnostic",
                        "cond_formatting_rules": {
                            "pass": [{"s_eq": "✓"}],  # Green for pass
                            "fail": [{"s_eq": "✗"}],  # Red for fail
                        },
                    },
                    "High R-hat Parameters": {
                        "title": "# Parameters with R-hat > 1.01",
                        "description": "Number of parameters with high R-hat values",
                    },
                    "Response Range": {
                        "title": "Response Range",
                        "description": "Range of response thresholds",
                    },
                    "_sort_score": {
                        "title": "_sort_score",
                        "hidden": True,  # Hide the sorting column from display
                    },
                },
                table_id="bifrost_diagnostics_table",
                title="Probe Diagnostic Summary",
            )

            # Add diagnostic table to diag module
            diag_module.add_section(
                name="Diagnostic Table",
                anchor="bifrost_diagnostics_table",
                plot=diagnostic_table,
                description=self.template_loader.get_template(
                    "diagnostics_table",
                ).format(
                    cds_threshold=self.cds_threshold,
                ),
            )
        else:
            # Add no-data message when no probes have diagnostic information
            diag_module.add_section(
                name="Diagnostic Table",
                anchor="bifrost_diagnostics_table",
                content=self.template_loader.get_template("no_data").format(
                    section_name="Diagnostic Information Available",
                    section_name_lower="diagnostic information",
                    cds_filter_reason=(
                        " with CDS > " + str(self.cds_threshold)
                        if apply_cds_threshold
                        else ""
                    ),
                ),
            )

        # Create module for PoD statistics
        stats_module = multiqc.BaseMultiqcModule(
            name=self._get_module_name_with_cds(
                "Probe-level PoD Statistics",
                apply_cds_threshold=apply_cds_threshold,
            ),
            anchor="bifrost_stats",
            info=self._get_module_info_with_cds(
                "Detailed statistics for probes",
                apply_cds_threshold=apply_cds_threshold,
            ),
        )

        # Add PoD statistics table to stats module
        if n_probe > 0:
            # Get probes and sort by PoD
            if apply_cds_threshold:
                cds_mask = self.data.stats["cds"] > self.cds_threshold
                probes = self.data.stats["probe"][cds_mask][
                    np.argsort(self.data.stats["pod"][cds_mask])
                ][: self.n_pod_stats]
                cds = self.data.stats["cds"][cds_mask][
                    np.argsort(self.data.stats["pod"][cds_mask])
                ][: self.n_pod_stats]
            else:
                probes = self.data.stats["probe"][np.argsort(self.data.stats["pod"])][
                    : self.n_pod_stats
                ]
                cds = self.data.stats["cds"][np.argsort(self.data.stats["pod"])][
                    : self.n_pod_stats
                ]
            logger.info(
                "Found %d probes to include in PoD statistics table",
                len(probes),
            )

            if len(probes) > 0:
                # Create table data
                table_data = {}
                for probe, cds_val in zip(probes, cds, strict=False):
                    # Get POD samples and calculate extensions needed
                    pod_samples = np.array(self.data.df[probe]["pod"])
                    n_pod_samples = len(pod_samples)
                    n_extend = self.data.stats["n_samp"] - n_pod_samples

                    # Filter out infinite values
                    pod_samples = pod_samples[~np.isinf(pod_samples)]

                    # Extend with max_conc values
                    extended_pod_samples = np.concatenate(
                        (
                            pod_samples,
                            [self.data.stats["max_conc"] for _ in range(n_extend)],
                        ),
                    )
                    pod_percentiles = np.percentile(
                        extended_pod_samples,
                        q=(5, 25, 50, 75, 95),
                    )

                    # Format PoD values
                    pod_values = [
                        self.format_pod(pod_val, self.data.stats["max_conc"])
                        for pod_val in pod_percentiles
                    ]

                    # Add row to table data
                    table_data[probe] = {
                        "CDS": self.format_float(cds_val),
                        "5th percentile": pod_values[0],
                        "25th percentile": pod_values[1],
                        "50th percentile": pod_values[2],
                        "75th percentile": pod_values[3],
                        "95th percentile": pod_values[4],
                    }

                # Create table plot
                pod_stats_table = table.plot(
                    data=table_data,
                    headers={
                        "CDS": {
                            "title": "CDS",
                            "format": "{:.3f}",
                            "description": f'Concentration-Dependency Score{" (threshold = " + str(self.cds_threshold) + ")" if apply_cds_threshold else ""}',
                        },
                        "5th percentile": {
                            "title": f"5th percentile ({self.conc_units})",
                            "description": "5th percentile of PoD distribution",
                        },
                        "25th percentile": {
                            "title": f"25th percentile ({self.conc_units})",
                            "description": "25th percentile of PoD distribution",
                        },
                        "50th percentile": {
                            "title": f"50th percentile ({self.conc_units})",
                            "description": "Median of PoD distribution",
                        },
                        "75th percentile": {
                            "title": f"75th percentile ({self.conc_units})",
                            "description": "75th percentile of PoD distribution",
                        },
                        "95th percentile": {
                            "title": f"95th percentile ({self.conc_units})",
                            "description": "95th percentile of PoD distribution",
                        },
                    },
                    pconfig={
                        "id": "bifrost_stats_table",
                        "title": f'Probe-level PoD Statistics{" (CDS > " + str(self.cds_threshold) + ")" if apply_cds_threshold else ""}',
                        "namespace": "BIFROST",
                        "no_violin": True,
                        "scale": False,  # Disable automatic scaling and coloring
                        "sort_rows": False,
                        "col1_header": "Probe",  # Label first column as Probe
                    },
                )

                # Add table to section
                stats_module.add_section(
                    name="PoD Statistics Table",
                    anchor="bifrost_stats_table",
                    plot=pod_stats_table,
                    description=self.template_loader.get_template(
                        "pod_stats_table",
                    ).format(
                        cds_info=(
                            " with CDS > " + str(self.cds_threshold)
                            if apply_cds_threshold
                            else ""
                        ),
                        cds_threshold=(
                            " with threshold = " + str(self.cds_threshold)
                            if apply_cds_threshold
                            else ""
                        ),
                        conc_units=self.conc_units,
                        n_pod_stats=self.n_pod_stats,
                    ),
                )
            else:
                # Add no-data message when no probes qualify
                stats_module.add_section(
                    name="PoD Statistics Table",
                    anchor="bifrost_stats_table",
                    content=self.template_loader.get_template("no_data").format(
                        section_name="Probes with Valid PoD Statistics",
                        section_name_lower="valid PoD statistics",
                        cds_filter_reason=(
                            " with CDS > " + str(self.cds_threshold)
                            if apply_cds_threshold
                            else ""
                        ),
                    ),
                )

        # Add all modules to report
        multiqc.report.modules.extend(
            [
                main_module,
                plot_guide_module,
                weighted_module,
                fc_module,
                lowest_means_module,
                stats_module,
                diag_module,
            ],
        )

        # Write report
        logger.info("Generating report...")

        multiqc.config.verbose = True
        multiqc.write_report(
            output_dir=Path(self.output_name).parent,
            filename=Path(self.output_name).name,
            title=f"BIFROST HTTr Analysis - {self.test_substance} ({self.cell_type})",
            report_comment=f"Analysis of {self.test_substance} on {self.cell_type} cells after {self.timepoint} exposure",
            force=True,
        )

        logger.info("Report generation complete")
        if not self.interactive_plots:
            logger.info(
                "Note: Consider using --interactive-plots for faster rendering with large datasets",
            )
