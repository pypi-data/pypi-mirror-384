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

"""Compression utilities for BIFROST package.

This module provides functions for compressing and managing BIFROST output data.
"""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from bifrost_httr.core.statistics import calculate_global_pod

from .logging import get_logger

logger = get_logger(__name__)


def get_global_pod(df: pd.Series, seed: int | None = None) -> dict[str, Any]:
    """Calculate and return global PoD.

    Args:
        df: BIFROST summary Series
        seed: Optional random seed for reproducibility

    Returns:
        Dictionary of global PoD-related statistics

    Note:
        This function is a wrapper around the consolidated calculate_global_pod
        function in core.statistics for backward compatibility.

    """
    return calculate_global_pod(df, data_type="summary", seed=seed)


def compress_output(
    analysis_dir: str | Path,
    path_to_summary: str | Path,
    test_substance: str | None = None,
    cell_type: str | None = None,
    seed: int | None = None,
    *,
    no_compression: bool = False,
) -> None:
    """Compress intermediate output into a single pandas DataFrame.

    Args:
        analysis_dir: Directory containing probe .pkl files to process
        path_to_summary: Path to the output json file
        test_substance: Test substance string to be included within output file
        cell_type: Cell type string to be included within output file
        seed: Optional random seed for reproducibility
        no_compression: If True, save output as plain JSON without compression

    """
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)

    # Convert paths to Path objects
    analysis_dir = Path(analysis_dir)
    path_to_summary = Path(path_to_summary)

    # Get list of probe files
    data_files = [f for f in analysis_dir.glob("*.pkl") if f.is_file()]
    if not data_files:
        error_msg = f"No .pkl files found in {analysis_dir}"
        raise ValueError(error_msg)

    # Determine probe IDs
    probes = np.array([file.stem for file in data_files])

    # Create empty pandas series
    summary = pd.Series(dtype="object")

    # Extract details inputs universal to all chemicals/probes from first file
    with data_files[0].open("rb") as f:
        data = pd.read_pickle(f)

    for key in [
        "n_samp",
        "n_sample",
        "n_treatment_batch",
        "total_count",
        "n_batch",
        "batch_index",
        "n_conc",
        "conc",
        "conc_index",
        "max_conc",
    ]:
        summary[key] = data[key]

    summary["probes"] = probes

    # Extract probe-specific information
    for probe in probes:
        with (analysis_dir / f"{probe}.pkl").open("rb") as f:
            data = pd.read_pickle(f)

        summary[probe] = pd.Series(dtype="object")
        summary[probe]["diagnostics"] = data["diagnostics"]
        summary[probe]["parameters"] = data["parameters"]

        for par in data["fit"].index:
            summary[probe][par] = data["fit"][par]
        summary[probe]["count"] = data["count"]

    # Calculate global PoD and add to dictionary
    global_pod_dict = get_global_pod(summary, seed)
    summary["global_pod_dict"] = global_pod_dict

    # Create meta dictionary containing test substance and cell type, if provided
    meta = {}
    if test_substance is not None and isinstance(test_substance, str):
        meta['Test substance'] = test_substance
    else:
        meta['Test substance'] = "Unknown"

    if cell_type is not None and isinstance(cell_type, str):
        meta['Cell type'] = cell_type
    else:
        meta['Cell type'] = "Unknown"
    summary["meta"] = meta

    # Write summary
    if no_compression:
        # Save as plain JSON without compression
        summary.to_json(path_to_summary, orient="index")
    else:
        # Save with zip compression
        summary.to_json(path_to_summary, orient="index", compression="zip")

    logger.info("Output saved to %s", path_to_summary)
