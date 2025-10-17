"""Tests for configuration utilities."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from bifrost_httr.utils.config import convert_meta_data, load_yaml_file


@pytest.fixture
def sample_yaml_file(tmp_path: Path) -> Path:
    """Create a sample YAML file for testing.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        Path to the sample YAML file
    """
    yaml_content = {
        "test_substance": "Compound A",
        "cell_type": "HepG2",
        "thresholds": {
            "min_reads": 1000,
            "min_mapped": 0.8,
        },
    }

    yaml_path = tmp_path / "config.yaml"
    with yaml_path.open("w") as f:
        yaml.safe_dump(yaml_content, f)

    return yaml_path


@pytest.fixture
def sample_meta_data() -> pd.DataFrame:
    """Create sample metadata DataFrame for testing.

    Returns:
        Sample metadata DataFrame
    """
    return pd.DataFrame(
        {
            "Sample ID": ["S1", "S2", "S3"],
            "Cell Line": ["HepG2", "HepG2", "HepG2"],
            "Treatment": ["Compound A", "Compound A", "Compound A"],
            "Concentration": [0.0, 1.0, 10.0],
            "Batch": [1, 1, 2],
            "Mapped Reads": [1000, 2000, 3000],
        },
    )


def test_load_yaml_file(sample_yaml_file: Path) -> None:
    """Test loading YAML files."""
    # Test loading valid YAML
    config = load_yaml_file(sample_yaml_file)
    assert isinstance(config, dict)
    assert config["test_substance"] == "Compound A"
    assert config["thresholds"]["min_reads"] == 1000

    # Test loading non-existent file
    with pytest.raises(FileNotFoundError):
        load_yaml_file(sample_yaml_file.parent / "nonexistent.yaml")

    # Test loading invalid YAML
    invalid_yaml = sample_yaml_file.parent / "invalid.yaml"
    invalid_yaml.write_text("invalid: :")
    with pytest.raises(yaml.YAMLError):
        load_yaml_file(invalid_yaml)


def test_convert_meta_data(sample_meta_data: pd.DataFrame) -> None:
    """Test metadata conversion."""
    # Test basic conversion
    meta_mapper = {
        "Cell type": ["Cell Line"],
        "Test substance": ["Treatment"],
        "Concentration": ["Concentration"],
        "Batch": ["Batch"],
        "Num. mapped reads": ["Mapped Reads"],
    }

    result = convert_meta_data(sample_meta_data, meta_mapper)
    assert isinstance(result, pd.DataFrame)
    assert "Cell type" in result.columns
    assert "Test substance" in result.columns
    assert len(result) == len(sample_meta_data)

    # Test with missing column in mapper
    meta_mapper["Missing"] = ["NonexistentColumn"]
    result = convert_meta_data(sample_meta_data, meta_mapper)
    assert "Missing" not in result.columns

    # Test with non-string key in mapper
    invalid_mapper = meta_mapper.copy()
    invalid_mapper["Invalid"] = [123]  # type: ignore[list-item]
    with pytest.raises(TypeError, match="No logic defined to handle key of type"):
        convert_meta_data(sample_meta_data, invalid_mapper)
