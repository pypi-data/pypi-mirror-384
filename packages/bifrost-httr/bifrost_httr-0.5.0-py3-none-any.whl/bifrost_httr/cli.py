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

"""BIFROST-HTTr CLI - Unified command-line interface for BIFROST-HTTr package.

This module provides a unified command-line interface for the BIFROST-HTTr package,
organizing commands into logical groups for analysis, reporting, and data management.
"""

from pathlib import Path
from typing import (  # noqa: F401 - used in type hints
    Any,
    Optional,
    Union,
)

import click
import pandas as pd

from .core.analysis import run_concentration_response_analysis
from .core.data_processing import (
    generate_bifrost_inputs,
    process_batches,
    process_data,
    validate_config,
    validate_config_file,
    validate_counts_table,
    validate_meta_data,
    validate_output_directory,
)
from .core.model import compile_stan_model
from .utils.compression import compress_output
from .utils.config import convert_meta_data, load_yaml_file
from .utils.logging import get_logger
from .visualization.data import BifrostData
from .visualization.report import BifrostMultiQCReport

# Configure logging automatically when getting logger
logger = get_logger(__name__)


@click.group(name="bifrost-httr")
@click.version_option(package_name="bifrost-httr")
def cli() -> None:
    """BIFROST-HTTr Analysis - Bayesian inference for region of signal threshold."""


@click.command(name="run-analysis")
@click.option(
    "--data-files",
    "-f",
    multiple=True,
    required=True,
    help="List of probe .pkl files to process",
)
@click.option(
    "--model-executable",
    "-m",
    type=click.Path(exists=True),
    help="Path to compiled Stan model executable (optional, will use default model if not provided)",
)
@click.option(
    "--n-cores",
    "-n",
    type=int,
    help="Number of cores to use in multiprocessing",
)
@click.option(
    "--output-dir",
    "-o",
    required=True,
    type=click.Path(),
    help="Directory to store outputs",
)
@click.option("--seed", "-s", type=int, help="Optional random seed for reproducibility")
def run_analysis(
    data_files: tuple[str, ...],
    model_executable: str | None,
    n_cores: int | None,
    output_dir: str,
    seed: int | None,
) -> None:
    """Run concentration-response analysis on BIFROST data files."""
    if not data_files:
        click.echo("Error: No data files specified", err=True)
        return

    # If no model executable is provided, compile the default model
    if model_executable is None:
        model_executable = compile_stan_model()
    else:
        model_executable = Path(model_executable)

    run_concentration_response_analysis(
        files_to_process=data_files,
        model_executable=model_executable,
        number_of_cores=n_cores or 1,
        fit_dir=output_dir,
        seed=seed,
    )


@click.command(name="create-report")
@click.option(
    "--summary-file",
    "-s",
    required=True,
    type=click.Path(exists=True),
    help="Path to the summary JSON file",
)
@click.option(
    "--test-substance",
    "-t",
    required=True,
    help="Name of the test substance",
)
@click.option(
    "--cell-type",
    "-c",
    required=True,
    help="Type of cell used in the test",
)
@click.option(
    "--output-name",
    "-o",
    default="multiqc_report.html",
    help="Name for the output report",
)
@click.option(
    "--timepoint",
    default="24 hours",
    help="Exposure duration within experiment",
)
@click.option(
    "--conc-units",
    type=click.Choice(["uM", "ugml-1", "mgml-1"]),
    default="uM",
    help="Concentration units",
)
@click.option(
    "--interactive-plots",
    is_flag=True,
    help="Force interactive plots (may be faster for large datasets)",
)
@click.option(
    "--n-fold-change-probes",
    type=int,
    default=5,
    help="Number of most up/down regulated probes to show",
)
@click.option(
    "--cds-threshold",
    type=float,
    default=0.5,
    help="Concentration-Dependency Score threshold for filtering probes",
)
@click.option(
    "--n-lowest-means",
    type=int,
    default=10,
    help="Number of lowest mean PoD probes to show",
)
@click.option(
    "--n-pod-stats",
    type=int,
    default=100,
    help="Number of probes to include in PoD statistics table",
)
@click.option(
    "--plot-height",
    type=int,
    default=400,
    help="Height of concentration-response plots in pixels",
)
@click.option(
    "--pod-vs-fc-height",
    type=int,
    default=600,
    help="Height of PoD vs Fold Change plot in pixels",
)
@click.option(
    "--no-cds-threshold",
    is_flag=True,
    help="Do not filter probes by CDS threshold in summary tables and lowest mean PoDs section",
)
@click.option(
    "--custom-templates",
    type=click.Path(exists=True),
    help="Path to custom template YAML file to override default report templates",
)
def create_report(
    summary_file: str,
    test_substance: str,
    cell_type: str,
    output_name: str,
    timepoint: str,
    conc_units: str,
    n_fold_change_probes: int,
    cds_threshold: float,
    n_lowest_means: int,
    n_pod_stats: int,
    plot_height: int,
    pod_vs_fc_height: int,
    custom_templates: str | None,
    *,
    interactive_plots: bool,
    no_cds_threshold: bool,
) -> None:
    """Create Bifrost HTTR reports using MultiQC."""
    data = BifrostData(summary_file)
    report = BifrostMultiQCReport(
        data,
        test_substance=test_substance,
        cell_type=cell_type,
        output_name=output_name,
        timepoint=timepoint,
        conc_units=conc_units,
        interactive_plots=interactive_plots,
        n_fold_change_probes=n_fold_change_probes,
        cds_threshold=cds_threshold,
        n_lowest_means=n_lowest_means,
        n_pod_stats=n_pod_stats,
        plot_height=plot_height,
        pod_vs_fc_height=pod_vs_fc_height,
        no_cds_threshold=no_cds_threshold,
        custom_templates=custom_templates,
    )
    report.create_report()


@click.command(name="compress-output")
@click.option(
    "--fits-dir",
    "-f",
    required=True,
    type=click.Path(exists=True),
    help="Directory containing probe .pkl files to process",
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(),
    help="Path to the output json",
)
@click.option(
    "--test_substance",
    "-t",
    required=False,
    type=str,
    help="Test substance name (as it appears in the HTTr meta data)",
)
@click.option(
    "--cell_type",
    "-c",
    required=False,
    type=str,
    help="Cell type name (as it appears in the HTTr meta data)",
)
@click.option("--seed", "-s", type=int, help="Optional random seed for reproducibility")
@click.option(
    "--no-compression",
    is_flag=True,
    help="Save output as plain JSON without compression",
)
def compress_output_cmd(
    fits_dir: str,
    output: str,
    test_substance: str | None,
    cell_type: str | None,
    seed: int | None,
    *,
    no_compression: bool,
) -> None:
    """Compress intermediate output into a single pandas DataFrame."""
    # Auto-correct filename if compression is enabled but user provided .json extension
    output_path = Path(output)
    if not no_compression and output_path.suffix == ".json":
        # Change .json to .json.zip for compressed output
        corrected_output = output_path.with_suffix(".json.zip")
        click.echo(
            f"Note: Correcting output filename from '{output}' to '{corrected_output}' for compressed output",
        )
        output = str(corrected_output)

    compress_output(fits_dir, output, test_substance, cell_type, seed, no_compression=no_compression)


@click.command(name="prepare-inputs")
@click.option(
    "--meta-data",
    "-m",
    required=True,
    type=click.Path(exists=True),
    help="Path to meta data CSV file",
)
@click.option(
    "--meta-mapper",
    required=False,
    type=click.Path(exists=True),
    help="Optional: Path to meta data mapper YAML file. Not needed if metadata columns already match BIFROST's internal format.",
)
@click.option(
    "--counts",
    "-c",
    required=True,
    type=click.Path(exists=True),
    help="Path to counts CSV file",
)
@click.option(
    "--config",
    required=True,
    type=click.Path(exists=True),
    help="Path to configuration YAML file",
)
@click.option(
    "--batch-key",
    help="Field to use as batch key in the BIFROST model (default: 'N/A' - single batch for all samples)",
)
@click.option(
    "--min-percent-mapped-reads",
    type=float,
    help="Minimum percentage of mapped reads required (default: 50.0)",
)
@click.option(
    "--min-num-mapped-reads",
    type=int,
    help="Minimum number of mapped reads required (default: 100000)",
)
@click.option(
    "--min-avg-treatment-count",
    type=int,
    help="Minimum average treatment count required (default: 5)",
)
@click.option(
    "--batch-matched-controls",
    is_flag=True,
    help="Filter control samples to only those in batches containing treatments (default: False)",
)
@click.option(
    "--output-dir",
    "-o",
    required=True,
    type=click.Path(),
    help="Directory to store outputs",
)
def prepare_inputs(
    meta_data: str,
    meta_mapper: str | None,
    counts: str,
    config: str,
    batch_key: str | None,
    min_percent_mapped_reads: float | None,
    min_num_mapped_reads: int | None,
    min_avg_treatment_count: int | None,
    output_dir: str,
    *,
    batch_matched_controls: bool,
) -> None:
    """Prepare Bifrost inputs from meta data and counts."""
    # Load configuration file
    config_dict = load_yaml_file(config)
    validate_config_file(config_dict)

    # Set default values from config file
    batch_key = batch_key or config_dict.get("Batch key", "N/A")
    min_percent_mapped_reads = min_percent_mapped_reads or config_dict.get(
        "Minimum percent mapped reads",
        50.0,
    )
    min_num_mapped_reads = min_num_mapped_reads or config_dict.get(
        "Minimum number mapped reads",
        100000,
    )
    min_avg_treatment_count = min_avg_treatment_count or config_dict.get(
        "Minimum average treatment count",
        5,
    )

    # Load meta data file and convert if mapper provided
    meta_raw = pd.read_csv(meta_data)
    if meta_mapper:
        meta_data_mapper = load_yaml_file(meta_mapper)
        meta = convert_meta_data(meta_raw, meta_data_mapper)
    else:
        meta = meta_raw
    validate_meta_data(meta)

    # Load counts table
    counts_table = pd.read_csv(counts)
    validate_counts_table(counts_table)

    # Create final config dictionary for BIFROST inputs (CLI values override config file)
    final_config_dict = {
        "Test substances": config_dict["Test substances"],
        "Cell types": config_dict["Cell types"],
        "Additional divider": config_dict.get("Additional divider", "N/A"),
        "Specific filters": config_dict.get("Specific filters", None),
        "Batch key": batch_key,
        "Minimum percent mapped reads": min_percent_mapped_reads,
        "Minimum number mapped reads": min_num_mapped_reads,
        "Minimum average treatment count": min_avg_treatment_count,
        "Batch-matched controls": batch_matched_controls,
    }
    validate_config(final_config_dict)

    # Make directory for storing outputs
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generate_bifrost_inputs(meta, counts_table, final_config_dict, output_dir)


@click.command(name="split-data")
@click.option(
    "--input-file",
    "-i",
    required=True,
    type=click.Path(exists=True),
    help="Path to input data json",
)
@click.option(
    "--output-dir",
    "-o",
    required=True,
    type=click.Path(),
    help="Directory to store outputs",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=0,
    help="Number of files per batch",
)
@click.option(
    "--batch-mode",
    type=click.Choice(["batch", "all"]),
    default="all",
    help='Batch mode: "batch" for individual archives, "all" for single archive',
)
@click.option("--prefix", "-p", required=True, help="Prefix for output files")
@click.option(
    "--archive-mode",
    type=click.Choice(["tar", "directory"]),
    default="tar",
    help='Archive mode: "tar" for .tar.gz archives (default), "directory" for folders of files',
)
@click.option(
    "--test-probes",
    type=int,
    help="Number of probes to sample for testing (optional)",
)
@click.option(
    "--random-seed",
    type=int,
    help="Random seed for reproducible probe selection (default: 5)",
)
def split_data(
    input_file: str,
    output_dir: str,
    batch_size: int,
    batch_mode: str,
    prefix: str,
    archive_mode: str,
    test_probes: int | None,
    random_seed: int | None,
) -> None:
    """Split data into processing batches."""
    # Validate and create output directory
    output_dir = Path(output_dir)
    validate_output_directory(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process the data into pickle files
    process_data(
        input_file_path=input_file,
        path_to_output=output_dir,
        testing_mode=False,
        test_probes=test_probes,
        random_seed=random_seed,
    )

    # Process the pickle files into batches
    data_dir = output_dir / "Data"
    manifest_file = process_batches(
        data_dir,
        output_dir,
        prefix,
        batch_size,
        batch_mode,
        archive_mode,
    )
    click.echo(f"Created manifest file: {manifest_file}")


@click.command(name="compile-model")
@click.argument("stan_file", type=click.Path(exists=True), required=False)
def compile_model(stan_file: str | None) -> None:
    """Compile a Stan model file (uses built-in model if no file specified)."""
    if stan_file is None:
        exe_file = compile_stan_model()
    else:
        exe_file = compile_stan_model(Path(stan_file))
    click.echo(f"Model compiled successfully: {exe_file}")


# Register all commands
cli.add_command(run_analysis)
cli.add_command(create_report)
cli.add_command(compress_output_cmd)
cli.add_command(prepare_inputs)
cli.add_command(split_data)
cli.add_command(compile_model)

if __name__ == "__main__":
    cli()
