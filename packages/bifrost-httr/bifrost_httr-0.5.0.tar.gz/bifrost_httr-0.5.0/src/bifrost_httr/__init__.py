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

"""BIFROST HTTr Analysis Package.

This package provides tools for analyzing high-throughput transcriptomics (HTTr) data
using the BIFROST (Bayesian Inference of Fold Response and Omics Statistical Testing)
methodology.
"""

from .core.analysis import gen_plotting_data, run_concentration_response_analysis
from .core.data_processing import (
    filter_percent_mapped_reads,
    filter_total_mapped_reads,
    generate_bifrost_inputs,
    process_batches,
    process_data,
    validate_config,
    validate_config_file,
    validate_counts_table,
    validate_filter_dict,
    validate_meta_data,
    validate_output_directory,
    write_bifrost_input,
)
from .core.model import fit_model
from .visualization.data import BifrostData, ProbeData
from .visualization.report import BifrostMultiQCReport

__all__ = [
    "BifrostData",
    "BifrostMultiQCReport",
    "ProbeData",
    "filter_percent_mapped_reads",
    "filter_total_mapped_reads",
    "fit_model",
    "gen_plotting_data",
    "generate_bifrost_inputs",
    "process_batches",
    "process_data",
    "run_concentration_response_analysis",
    "validate_config",
    "validate_config_file",
    "validate_counts_table",
    "validate_filter_dict",
    "validate_meta_data",
    "validate_output_directory",
    "write_bifrost_input",
]
