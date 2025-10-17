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
"""Configuration utilities for BIFROST package.

This module provides functions for loading and managing configuration files
and metadata conversion.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .logging import get_logger

logger = get_logger(__name__)


def load_yaml_file(file_path: str | Path) -> dict[str, Any]:
    """Load and parse a YAML file.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dictionary containing the parsed YAML contents

    Raises:
        yaml.YAMLError: If the YAML file is invalid
        FileNotFoundError: If the file does not exist

    """
    path = Path(file_path)
    with path.open() as stream:
        return yaml.safe_load(stream)


def convert_meta_data(
    meta: pd.DataFrame,
    meta_mapper_dict: dict[str, list[str]],
) -> pd.DataFrame:
    """Build a pandas DataFrame containing meta data for internal use.

    Args:
        meta: Input meta data DataFrame
        meta_mapper_dict: Dictionary mapping output columns to input columns

    Returns:
        Processed meta data DataFrame

    Raises:
        TypeError: If a non-string key is encountered in the mapper

    """
    # Populate columns from meta data and mapper dict
    df = pd.DataFrame()
    for key, values in meta_mapper_dict.items():
        for i in values:
            if isinstance(i, str):
                if i in meta.columns:
                    df[key] = meta[i]
                    break
            else:
                error_msg = f"No logic defined to handle key of type {type(i)}"
                raise TypeError(error_msg)

    # Remove any rows with nans in the Cell type column
    if "Cell type" in df.columns:
        df = df[~df["Cell type"].isna()]

    return df
