"""Tests for the data processing module.

This test suite covers the data processing functionality of the BIFROST package,
focusing on input validation, data filtering, and batch processing. The tests use
fixtures and mocking to isolate components and test edge cases.
"""

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from bifrost_httr.core.data_processing import (
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


@pytest.fixture
def sample_counts_table() -> pd.DataFrame:
    """Create sample counts table for testing."""
    data = {
        "probe_id": ["probe1", "probe2", "probe3"],
        "sample1": [10000, 20000, 30000],  # Control drug1 batch1
        "sample2": [15000, 25000, 35000],  # Treatment 1 drug1 batch1
        "sample3": [15000, 25000, 35000],  # Treatment 2 drug1 batch1
        "sample4": [12000, 22000, 32000],  # Control drug1 batch2
        "sample5": [17000, 27000, 37000],  # Treatment 1 drug1 batch2
        "sample6": [17000, 27000, 37000],  # Treatment 2 drug1 batch2
        "sample7": [11000, 21000, 31000],  # Control drug2 batch1
        "sample8": [16000, 26000, 36000],  # Treatment 1 drug2 batch1
        "sample9": [16000, 26000, 36000],  # Treatment 2 drug2 batch1
        "sample10": [13000, 23000, 33000],  # Control drug2 batch2
        "sample11": [18000, 28000, 38000],  # Treatment 1 drug2 batch2
        "sample12": [18000, 28000, 38000],  # Treatment 2 drug2 batch2
    }
    df = pd.DataFrame(data)
    for col in df.columns[1:]:  # Convert all count columns to int64
        df[col] = df[col].astype(np.int64)
    return df


@pytest.fixture
def sample_meta_data() -> pd.DataFrame:
    """Create sample metadata for testing."""
    data = {
        "Test substance": [
            "drug1",
            "drug1",
            "drug1",
            "drug1",
            "drug1",
            "drug1",
            "drug2",
            "drug2",
            "drug2",
            "drug2",
            "drug2",
            "drug2",
        ],
        "Cell type": ["HepG2"] * 12,
        "Concentration": [0.0, 1.0, 2.0, 0.0, 1.0, 2.0, 0.0, 1.0, 2.0, 0.0, 1.0, 2.0],
        "Sample ID": [
            "sample1",
            "sample2",
            "sample3",
            "sample4",
            "sample5",
            "sample6",
            "sample7",
            "sample8",
            "sample9",
            "sample10",
            "sample11",
            "sample12",
        ],
        "Num. mapped reads": [10000, 20000, 15000, 25000, 12000, 22000, 17000, 27000, 15000, 25000, 12000, 22000],
        "Percent mapped reads": [60.0, 70.0, 65.0, 75.0, 62.0, 72.0, 67.0, 77.0, 75.0, 62.0, 72.0, 67.0],
        "Batch": [
            "batch1",
            "batch1",
            "batch1",
            "batch2",
            "batch2",
            "batch2",
            "batch1",
            "batch1",
            "batch1",
            "batch2",
            "batch2",
            "batch2",
        ],
    }
    df = pd.DataFrame(data)
    df["Num. mapped reads"] = df["Num. mapped reads"].astype(np.int64)
    df["Percent mapped reads"] = df["Percent mapped reads"].astype(np.float64)
    df["Concentration"] = df["Concentration"].astype(np.float64)
    return df


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Create sample configuration for testing."""
    return {
        "Batch key": "Batch",
        "Minimum average treatment count": 10,
        "Minimum number mapped reads": 500,
        "Minimum percent mapped reads": 50,
        "Minimum fold change": 1.5,
        "Maximum adjusted p-value": 0.05,
    }


def test_validate_counts_table(sample_counts_table: pd.DataFrame) -> None:
    """Test counts table validation."""
    # Test valid counts table
    validate_counts_table(sample_counts_table)

    # Test too few columns
    invalid_table = pd.DataFrame({"probe_id": ["gene1"]})
    with pytest.raises(ValueError, match="must have at least .* columns"):
        validate_counts_table(invalid_table)

    # Test negative values
    invalid_table = sample_counts_table.copy()
    invalid_table = invalid_table.astype(
        {"sample1": np.int64},
    )  # Convert column to int64
    invalid_table.loc[0, "sample1"] = -100  # Set first row, first count column to -100
    with pytest.raises(ValueError, match="Count values must be non-negative"):
        validate_counts_table(invalid_table)


def test_validate_meta_data(sample_meta_data: pd.DataFrame) -> None:
    """Test metadata validation."""
    # Test valid metadata
    validate_meta_data(sample_meta_data)

    # Test missing required columns
    for col in [
        "Test substance",
        "Concentration",
        "Sample ID",
        "Num. mapped reads",
        "Percent mapped reads",
    ]:
        invalid_meta = sample_meta_data.drop(columns=[col])
        with pytest.raises(ValueError, match=f"Missing required columns.*{col}"):
            validate_meta_data(invalid_meta)

    # Test negative concentration
    invalid_meta = sample_meta_data.copy()
    invalid_meta.loc[:, "Concentration"] = pd.Series(
        [-1.0, 0.0, 1.0, 1.0],
        dtype=np.float64,
    )
    with pytest.raises(ValueError, match="Concentration values must be non-negative"):
        validate_meta_data(invalid_meta)

    # Test invalid read counts
    invalid_meta = sample_meta_data.copy()
    invalid_meta.loc[:, "Num. mapped reads"] = pd.Series(
        [-1000, 2000, 3000, 3000],
        dtype=np.int64,
    )
    with pytest.raises(ValueError, match="Num. mapped reads must be non-negative"):
        validate_meta_data(invalid_meta)

    # Test invalid percent mapped reads
    invalid_meta = sample_meta_data.copy()
    invalid_meta.loc[:, "Percent mapped reads"] = pd.Series(
        [-10.0, 60.0, 110.0, 110.0],
        dtype=np.float64,
    )
    with pytest.raises(ValueError, match="Percent mapped reads must be between"):
        validate_meta_data(invalid_meta)


def test_validate_filter_dict(sample_meta_data: pd.DataFrame) -> None:
    """Test filter dictionary validation."""
    # Create valid filter dict
    filter_dict = {
        "Test substance": "drug1",
        "Cell type": "HepG2",
    }

    # Test valid filter dict
    validate_filter_dict(filter_dict, sample_meta_data)

    # Test with invalid substance
    invalid_filter = filter_dict.copy()
    invalid_filter["Test substance"] = "nonexistent"
    with pytest.raises(
        ValueError,
        match="Filter value 'nonexistent' not found in meta data column 'Test substance'",
    ):
        validate_filter_dict(invalid_filter, sample_meta_data)

    # Test missing required key
    invalid_filter = {"Cell type": "HepG2"}
    with pytest.raises(
        ValueError,
        match="Filter dictionary must contain 'Test substance' key",
    ):
        validate_filter_dict(invalid_filter, sample_meta_data)


def test_validate_output_directory(tmp_path: Path) -> None:
    """Test output directory validation."""
    # Test with non-existent directory (should create)
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)  # Create with proper permissions
    validate_output_directory(output_dir)
    assert output_dir.exists()
    assert output_dir.is_dir()

    # Test with existing directory
    validate_output_directory(output_dir)  # Should not raise error

    # Test with file instead of directory
    file_path = tmp_path / "file.txt"
    file_path.touch()
    with pytest.raises(ValueError, match="exists but is not a directory"):
        validate_output_directory(file_path)


def test_validate_config(sample_config: dict[str, Any]) -> None:
    """Test configuration validation."""
    # Test valid config
    validate_config(sample_config)

    # Test missing required keys
    for key in [
        "Minimum percent mapped reads",
        "Minimum number mapped reads",
        "Minimum average treatment count",
        "Batch key",
    ]:
        invalid_config = sample_config.copy()
        del invalid_config[key]
        with pytest.raises(
            ValueError,
            match=f"Missing required configuration keys.*{key}",
        ):
            validate_config(invalid_config)


def test_filter_total_mapped_reads(sample_meta_data: pd.DataFrame) -> None:
    """Test filtering by total mapped reads."""
    threshold = 15000
    filtered_table = filter_total_mapped_reads(sample_meta_data, threshold)

    # Check that samples below threshold are removed
    assert "sample1" not in filtered_table.index
    assert all(filtered_table["Num. mapped reads"] >= threshold)

    # Test with threshold higher than all values
    high_threshold = 50000
    filtered_table = filter_total_mapped_reads(sample_meta_data, high_threshold)
    assert filtered_table.empty

    # Test with threshold lower than all values
    low_threshold = 1000
    filtered_table = filter_total_mapped_reads(sample_meta_data, low_threshold)
    assert filtered_table.shape == sample_meta_data.shape


def test_filter_percent_mapped_reads(sample_meta_data: pd.DataFrame) -> None:
    """Test filtering by percent mapped reads."""
    threshold = 50
    filtered_table = filter_percent_mapped_reads(sample_meta_data, threshold)

    # Check that samples below threshold are removed
    assert all(filtered_table["Percent mapped reads"] >= threshold)

    # Test with threshold higher than all values
    high_threshold = 90
    filtered_table = filter_percent_mapped_reads(sample_meta_data, high_threshold)
    assert filtered_table.empty

    # Test with threshold lower than all values
    low_threshold = 30
    filtered_table = filter_percent_mapped_reads(sample_meta_data, low_threshold)
    assert filtered_table.shape == sample_meta_data.shape


def test_process_data(tmp_path: Path) -> None:
    """Test data processing pipeline."""
    # Create test input data
    input_data = {
        "counts": [[100, 200], [300, 400], [500, 600]],  # Regular list instead of numpy array
        "total_count": [1000, 2000, 3000],  # Regular list instead of numpy array
        "batch_index": [1, 1, 1],  # Regular list instead of numpy array
        "n_treatment_batch": 1,
        "concentration": [0.0, 1.0, 2.0],  # Regular list instead of numpy array
        "probes": ["probe1", "probe2"],
    }

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Write input data to file
    input_file = tmp_path / "input.json"
    with input_file.open("w") as f:
        json.dump(input_data, f)

    # Process data
    process_data(input_file, output_dir)

    # Verify output directories were created
    assert (output_dir / "Data").exists()
    assert (output_dir / "Fits").exists()

    # Verify probe files were created
    assert (output_dir / "Data" / "probe1.pkl").exists()
    assert (output_dir / "Data" / "probe2.pkl").exists()

    # Test with missing file
    with pytest.raises(FileNotFoundError):
        process_data(tmp_path / "nonexistent.json", output_dir)


def test_process_batches(tmp_path: Path) -> None:
    """Test batch processing functionality."""
    # Create test data files
    data_dir = tmp_path / "Data"
    data_dir.mkdir()

    for i in range(5):
        test_data = {
            "counts": np.array([100, 200]),
            "total_count": np.array([1000, 2000]),
        }
        with (data_dir / f"probe{i}.pkl").open("wb") as f:
            pickle.dump(test_data, f)

    # Test batch processing
    manifest_path = process_batches(
        data_dir=data_dir,
        output_dir=tmp_path,
        prefix="test",
        batch_size=2,
        batch_mode="batch",
    )

    # Verify manifest was created
    assert manifest_path.exists()

    # Verify batch archives were created
    assert (tmp_path / "test_batch1.tar.gz").exists()
    assert (tmp_path / "test_batch2.tar.gz").exists()
    assert (tmp_path / "test_batch3.tar.gz").exists()

    # Test with no files
    empty_dir = tmp_path / "Empty"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        process_batches(
            data_dir=empty_dir,
            output_dir=tmp_path,
            prefix="empty",
            batch_size=2,
            batch_mode="batch",
        )

    # Test with invalid archive mode
    with pytest.raises(ValueError, match="archive_mode must be either"):
        process_batches(
            data_dir=data_dir,
            output_dir=tmp_path,
            prefix="invalid",
            batch_size=2,
            batch_mode="batch",
            archive_mode="invalid",
        )


def test_process_batches_edge_cases(tmp_path: Path) -> None:
    """Test edge cases for batch processing."""
    # Create test data directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Test with empty directory
    with pytest.raises(FileNotFoundError, match="No pickle files found"):
        process_batches(data_dir, tmp_path, "test", 1, "batch")

    # Test with invalid archive mode
    with pytest.raises(ValueError, match="archive_mode must be either"):
        process_batches(data_dir, tmp_path, "test", 1, "batch", archive_mode="invalid")

    # Create a single test file
    test_data = {
        "counts": np.array([100, 200]),
        "total_count": np.array([1000, 2000]),
    }
    with (data_dir / "test.pkl").open("wb") as f:
        pickle.dump(test_data, f)

    # Test with batch size larger than number of files
    manifest_path = process_batches(
        data_dir=data_dir,
        output_dir=tmp_path,
        prefix="test",
        batch_size=10,
        batch_mode="batch",
    )
    assert manifest_path.exists()
    assert (tmp_path / "test_batch1.tar.gz").exists()


def test_write_bifrost_input(
    sample_meta_data: pd.DataFrame,
    sample_counts_table: pd.DataFrame,
    sample_config: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Test BIFROST input file generation."""
    # Create filter dict
    filter_dict = {
        "Test substance": "drug1",
        "Cell type": "HepG2",
        "N/A": None,
    }

    # Write input file
    write_bifrost_input(
        meta=sample_meta_data,
        filter_dict=filter_dict,
        counts_table=sample_counts_table,
        config_dict=sample_config,
        output_directory=tmp_path,
    )

    # Verify output file was created
    expected_file = tmp_path / "BIFROST_input_drug1_HepG2.json"
    assert expected_file.exists()

    # Verify file contents
    with expected_file.open() as f:
        data = json.load(f)
        assert "test_substance" in data
        assert "cell_type" in data
        assert "probes" in data
        assert "counts" in data
        assert "batch_index" in data
        assert "concentration" in data
        assert "n_treatment_batch" in data


def test_write_bifrost_input_edge_cases(
    sample_meta_data: pd.DataFrame,
    sample_counts_table: pd.DataFrame,
    sample_config: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Test edge cases for BIFROST input file generation."""
    # Test with non-existent substance
    filter_dict = {
        "Test substance": "nonexistent",
        "Cell type": "HepG2",
        "N/A": None,
    }
    with pytest.raises(
        ValueError,
        match="Filter value 'nonexistent' not found in meta data column 'Test substance'",
    ):
        write_bifrost_input(
            meta=sample_meta_data,
            filter_dict=filter_dict,
            counts_table=sample_counts_table,
            config_dict=sample_config,
            output_directory=tmp_path,
        )

    # Test with non-existent cell type
    filter_dict = {
        "Test substance": "drug1",
        "Cell type": "nonexistent",
        "N/A": None,
    }
    with pytest.raises(
        ValueError,
        match="Filter value 'nonexistent' not found in meta data column 'Cell type'",
    ):
        write_bifrost_input(
            meta=sample_meta_data,
            filter_dict=filter_dict,
            counts_table=sample_counts_table,
            config_dict=sample_config,
            output_directory=tmp_path,
        )

    # Test with data that doesn't pass global filters
    strict_config = sample_config.copy()
    strict_config["Minimum percent mapped reads"] = 99.9  # Set an impossible threshold
    filter_dict = {
        "Test substance": "drug1",
        "Cell type": "HepG2",
        "N/A": None,
    }
    with pytest.raises(ValueError, match="No data passes the global filters"):
        write_bifrost_input(
            meta=sample_meta_data,
            filter_dict=filter_dict,
            counts_table=sample_counts_table,
            config_dict=strict_config,
            output_directory=tmp_path,
        )

    # Test with data that doesn't pass probe filters
    strict_config = sample_config.copy()
    strict_config["Minimum average treatment count"] = 1000000
    with pytest.raises(ValueError, match="No probes pass the filtering criteria"):
        write_bifrost_input(
            meta=sample_meta_data,
            filter_dict=filter_dict,
            counts_table=sample_counts_table,
            config_dict=strict_config,
            output_directory=tmp_path,
        )


def test_validate_config_file() -> None:
    """Test validation of configuration file."""
    # Test valid case
    valid_data = {
        "Test substances": ["drug1", "drug2"],
        "Cell types": ["HepG2"],
        "Additional divider": "batch",  # String value instead of None
        "Specific filters": None,
        "Minimum percent mapped reads": 80.0,
        "Minimum number mapped reads": 1000000,
        "Minimum average treatment count": 10,
        "Batch key": "Batch",
        "Random seed": 5,
    }
    validate_config_file(valid_data)

    # Test missing Test substances
    invalid_data = valid_data.copy()
    del invalid_data["Test substances"]
    with pytest.raises(
        ValueError,
        match="Missing required keys in configuration file",
    ):
        validate_config_file(invalid_data)

    # Test missing Cell types
    invalid_data = valid_data.copy()
    del invalid_data["Cell types"]
    with pytest.raises(
        ValueError,
        match="Missing required keys in configuration file",
    ):
        validate_config_file(invalid_data)

    # Test non-string Test substances
    invalid_data = valid_data.copy()
    invalid_data["Test substances"] = [123]
    with pytest.raises(ValueError, match="Test substances must be a list of strings"):
        validate_config_file(invalid_data)

    # Test non-string Cell types
    invalid_data = valid_data.copy()
    invalid_data["Cell types"] = [123]
    with pytest.raises(ValueError, match="Cell types must be a list of strings"):
        validate_config_file(invalid_data)

    # Test non-string Additional divider
    invalid_data = valid_data.copy()
    invalid_data["Additional divider"] = 123
    with pytest.raises(
        ValueError,
        match="Additional divider must be a string if present",
    ):
        validate_config_file(invalid_data)

    # Test non-dict Specific filters
    invalid_data = valid_data.copy()
    invalid_data["Specific filters"] = "not a dict"
    with pytest.raises(
        ValueError,
        match="Specific filters must be a dictionary if present and not None",
    ):
        validate_config_file(invalid_data)

    # Test invalid min_percent_mapped_reads
    invalid_data = valid_data.copy()
    invalid_data["Minimum percent mapped reads"] = 150.0
    with pytest.raises(
        ValueError,
        match="Minimum percent mapped reads must be a number between 0 and 100",
    ):
        validate_config_file(invalid_data)

    # Test invalid min_num_mapped_reads
    invalid_data = valid_data.copy()
    invalid_data["Minimum number mapped reads"] = -1
    with pytest.raises(
        ValueError,
        match="Minimum number mapped reads must be a non-negative integer",
    ):
        validate_config_file(invalid_data)

    # Test invalid min_avg_treatment_count
    invalid_data = valid_data.copy()
    invalid_data["Minimum average treatment count"] = -1
    with pytest.raises(
        ValueError,
        match="Minimum average treatment count must be a non-negative integer",
    ):
        validate_config_file(invalid_data)

    # Test invalid batch_key
    invalid_data = valid_data.copy()
    invalid_data["Batch key"] = 123
    with pytest.raises(
        ValueError,
        match="Batch key must be a string",
    ):
        validate_config_file(invalid_data)

    # Test invalid random_seed
    invalid_data = valid_data.copy()
    invalid_data["Random seed"] = "not an int"
    with pytest.raises(
        ValueError,
        match="Random seed must be an integer",
    ):
        validate_config_file(invalid_data)


def test_process_data_edge_cases(tmp_path: Path) -> None:
    """Test edge cases for data processing."""
    # Create test input data
    input_data = {
        "counts": [[100, 200], [300, 400]],  # Regular list instead of numpy array
        "total_count": [1000, 2000],  # Regular list instead of numpy array
        "batch_index": [1, 1],  # Regular list instead of numpy array
        "n_treatment_batch": 1,
        "concentration": [0.0, 1.0],  # Regular list instead of numpy array
        "probes": ["probe1", "probe2"],
    }

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Write input data to file
    input_file = tmp_path / "input.json"
    with input_file.open("w") as f:
        json.dump(input_data, f)

    # Test with invalid file
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("invalid json")
    with pytest.raises(ValueError, match="Expected object or value"):
        process_data(invalid_file, output_dir)


def test_generate_bifrost_inputs(
    sample_meta_data: pd.DataFrame,
    sample_counts_table: pd.DataFrame,
    sample_config: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Test generation of multiple BIFROST input files."""
    # Create test substances and cell types
    config_dict = sample_config.copy()
    config_dict.update(
        {
            "Test substances": ["drug1", "drug2"],
            "Cell types": ["HepG2"],
            "Additional divider": "Batch",
            "Specific filters": None,
            "Minimum average treatment count": 10,
        },
    )

    # Generate inputs
    generate_bifrost_inputs(
        meta=sample_meta_data,
        counts_table=sample_counts_table,
        config_dict=config_dict,
        output_directory=tmp_path,
    )

    # Verify output files were created
    expected_files = [
        "BIFROST_input_drug1_HepG2_batch1.json",
        "BIFROST_input_drug1_HepG2_batch2.json",
        "BIFROST_input_drug2_HepG2_batch1.json",
        "BIFROST_input_drug2_HepG2_batch2.json",
    ]
    for file in expected_files:
        assert (tmp_path / file).exists()

    # Verify file contents
    for file in expected_files:
        with (tmp_path / file).open() as f:
            data = json.load(f)
            assert "test_substance" in data
            assert "cell_type" in data
            assert "probes" in data
            assert "counts" in data
            assert "batch_index" in data
            assert "concentration" in data
            assert "n_treatment_batch" in data


def test_generate_bifrost_inputs_not_enough_concs(
    sample_meta_data: pd.DataFrame,
    sample_counts_table: pd.DataFrame,
    sample_config: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Test generation of multiple BIFROST input files."""
    # Create test substances and cell types
    config_dict = sample_config.copy()
    config_dict.update(
        {
            "Test substances": ["drug1", "drug2"],
            "Cell types": ["HepG2"],
            "Additional divider": "Batch",
            "Specific filters": None,
            "Minimum average treatment count": 10,
        },
    )


    meta_data = sample_meta_data.copy()
    meta_data.update(
        {
            "Test substance": [
                "drug1",
                "drug1",
                "drug1",
                "drug1",
                "drug2",
                "drug2",
                "drug2",
                "drug2",
            ],
            "Cell type": ["HepG2"] * 8,
            "Concentration": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
            "Sample ID": [
                "sample1",
                "sample2",
                "sample3",
                "sample4",
                "sample5",
                "sample6",
                "sample7",
                "sample8",
            ],
            "Num. mapped reads": [10000, 20000, 15000, 25000, 12000, 22000, 17000, 27000],
            "Percent mapped reads": [60.0, 70.0, 65.0, 75.0, 62.0, 72.0, 67.0, 77.0],
            "Batch": [
                "batch1",
                "batch1",
                "batch2",
                "batch2",
                "batch1",
                "batch1",
                "batch2",
                "batch2",
            ],
        },
    )

    # Generate inputs
    with pytest.raises(ValueError) as exc_info:
        generate_bifrost_inputs(
            meta=meta_data,
            counts_table=sample_counts_table,
            config_dict=config_dict,
            output_directory=tmp_path,
        )


def test_write_bifrost_input_with_specific_filters(
    sample_meta_data: pd.DataFrame,
    sample_counts_table: pd.DataFrame,
    sample_config: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Test BIFROST input file generation with specific filters."""
    # Create filter dict
    filter_dict = {
        "Test substance": "drug1",
        "Cell type": "HepG2",
        "N/A": None,
    }

    # Add specific filters to config
    config_with_filters = sample_config.copy()
    config_with_filters["Specific filters"] = {"Batch": ["batch2"]}

    # Write input file
    write_bifrost_input(
        meta=sample_meta_data,
        filter_dict=filter_dict,
        counts_table=sample_counts_table,
        config_dict=config_with_filters,
        output_directory=tmp_path,
    )

    # Verify output file was created
    expected_file = tmp_path / "BIFROST_input_drug1_HepG2.json"
    assert expected_file.exists()

    # Verify file contents
    with expected_file.open() as f:
        data = json.load(f)
        assert "test_substance" in data
        assert "cell_type" in data
        assert "probes" in data
        assert "counts" in data
        assert "batch_index" in data
        assert "concentration" in data
        assert "n_treatment_batch" in data

    # Test with impossible threshold
    config_with_filters["Minimum average treatment count"] = 1000000
    with pytest.raises(ValueError, match="No probes pass the filtering criteria"):
        write_bifrost_input(
            meta=sample_meta_data,
            filter_dict=filter_dict,
            counts_table=sample_counts_table,
            config_dict=config_with_filters,
            output_directory=tmp_path,
        )


def test_write_bifrost_input_with_na_batch_key(
    sample_meta_data: pd.DataFrame,
    sample_counts_table: pd.DataFrame,
    tmp_path: Path,
) -> None:
    """Test BIFROST input generation with N/A batch key."""
    config_dict = {
        "Batch key": "N/A",  # Use N/A batch key
        "Minimum average treatment count": 10,
        "Minimum number mapped reads": 500,
        "Minimum percent mapped reads": 50,
    }

    filter_dict = {
        "Test substance": "drug1",
        "Cell type": "HepG2",
    }

    # Write input file
    write_bifrost_input(
        meta=sample_meta_data,
        filter_dict=filter_dict,
        counts_table=sample_counts_table,
        config_dict=config_dict,
        output_directory=tmp_path,
    )

    # Verify output file was created
    expected_file = tmp_path / "BIFROST_input_drug1_HepG2.json"
    assert expected_file.exists()

    # Verify file contents
    with expected_file.open() as f:
        data = json.load(f)
        # All samples should be in batch 1
        assert all(idx == 1 for idx in data["batch_index"])
        assert data["n_treatment_batch"] == 1


def test_write_bifrost_input_with_batch_matched_controls(
    sample_meta_data: pd.DataFrame,
    sample_counts_table: pd.DataFrame,
    tmp_path: Path,
) -> None:
    """Test BIFROST input generation with batch-matched controls."""
    config_dict = {
        "Batch key": "Batch",
        "Batch-matched controls": True,  # Enable batch-matched controls
        "Minimum average treatment count": 10,
        "Minimum number mapped reads": 500,
        "Minimum percent mapped reads": 50,
    }

    filter_dict = {
        "Test substance": "drug1",
        "Cell type": "HepG2",
    }

    # Write input file
    write_bifrost_input(
        meta=sample_meta_data,
        filter_dict=filter_dict,
        counts_table=sample_counts_table,
        config_dict=config_dict,
        output_directory=tmp_path,
    )

    # Verify output file was created
    expected_file = tmp_path / "BIFROST_input_drug1_HepG2.json"
    assert expected_file.exists()

    # Verify file contents - should only include batches that have treatments
    with expected_file.open() as f:
        data = json.load(f)
        # Only batch 1 and 2 should remain (both have treatments for drug1)
        unique_batches = list(set(data["batch_index"]))
        assert len(unique_batches) == 2


def test_write_bifrost_input_batch_matched_controls_string_values(
    sample_meta_data: pd.DataFrame,
    sample_counts_table: pd.DataFrame,
    tmp_path: Path,
) -> None:
    """Test BIFROST input generation with string boolean values for batch-matched controls."""
    config_dict = {
        "Batch key": "Batch",
        "Batch-matched controls": "true",  # Use string value
        "Minimum average treatment count": 10,
        "Minimum number mapped reads": 500,
        "Minimum percent mapped reads": 50,
    }

    filter_dict = {
        "Test substance": "drug1",
        "Cell type": "HepG2",
    }

    # Write input file
    write_bifrost_input(
        meta=sample_meta_data,
        filter_dict=filter_dict,
        counts_table=sample_counts_table,
        config_dict=config_dict,
        output_directory=tmp_path,
    )

    # Verify output file was created
    expected_file = tmp_path / "BIFROST_input_drug1_HepG2.json"
    assert expected_file.exists()


def test_process_data_zero_inflation_categories(tmp_path: Path) -> None:
    """Test data processing with zero-inflation count categories."""
    # Create test input data with various count levels including zeros
    input_data = {
        "counts": [
            [0, 50, 150],  # probe1: zero, low, high counts
            [1, 100, 200],  # probe2: low boundary, low boundary, high counts
        ],
        "total_count": [1000, 1000, 1000],
        "batch_index": [1, 1, 1],
        "n_treatment_batch": 1,
        "concentration": [0.0, 1.0, 10.0],
        "probes": ["probe1", "probe2"],
    }

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Write input data to file
    input_file = tmp_path / "input.json"
    with input_file.open("w") as f:
        json.dump(input_data, f)

    # Process data
    process_data(input_file, output_dir)

    # Load and verify probe1 data (has zero count)
    with (output_dir / "Data" / "probe1.pkl").open("rb") as f:
        probe1_data = pickle.load(f)

    # Check that all zero-inflation fields are present
    assert "n_zero_count" in probe1_data
    assert "zero_count_index" in probe1_data
    assert "n_low_count" in probe1_data
    assert "low_count_index" in probe1_data
    assert "n_high_count" in probe1_data
    assert "high_count_index" in probe1_data

    # Verify count categorization for probe1: [0, 50, 150]
    assert probe1_data["n_zero_count"] == 1  # count[0] = 0
    assert probe1_data["n_low_count"] == 1  # count[1] = 50
    assert probe1_data["n_high_count"] == 1  # count[2] = 150

    # Verify indices (1-based as expected by Stan)
    assert list(probe1_data["zero_count_index"]) == [1]  # index 0 + 1
    assert list(probe1_data["low_count_index"]) == [2]  # index 1 + 1
    assert list(probe1_data["high_count_index"]) == [3]  # index 2 + 1

    # Load and verify probe2 data (no zero counts)
    with (output_dir / "Data" / "probe2.pkl").open("rb") as f:
        probe2_data = pickle.load(f)

    # Verify count categorization for probe2: [1, 100, 200]
    assert probe2_data["n_zero_count"] == 0  # no zeros
    assert probe2_data["n_low_count"] == 2  # count[0] = 1, count[1] = 100
    assert probe2_data["n_high_count"] == 1  # count[2] = 200

    # Verify indices
    assert len(probe2_data["zero_count_index"]) == 0
    assert list(probe2_data["low_count_index"]) == [1, 2]  # indices 0,1 + 1
    assert list(probe2_data["high_count_index"]) == [3]  # index 2 + 1
