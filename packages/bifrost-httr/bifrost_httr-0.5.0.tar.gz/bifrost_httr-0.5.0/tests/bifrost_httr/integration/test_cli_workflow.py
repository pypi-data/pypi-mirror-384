"""Integration tests for the complete BIFROST-HTTr CLI workflow.

This test suite verifies that the complete CLI workflow works as documented in the README,
using the example data provided in the examples/minimal directory.
"""

import logging
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from bifrost_httr.cli import cli

logger = logging.getLogger(__name__)


@pytest.fixture
def example_data(tmp_path: Path) -> Path:
    """Copy example data to a temporary directory."""
    # Create example data directory
    example_dir = tmp_path / "examples" / "minimal"
    example_dir.mkdir(parents=True)

    # Copy example files from examples/minimal
    source_dir = Path("examples/minimal")
    for file in [
        "Example_Meta_Data.csv",
        "Example_Counts_5probes.csv",
        "substances_cell_types.yml",
        "meta_data_mapper.yml",
    ]:
        shutil.copy2(source_dir / file, example_dir / file)

    return example_dir


def test_complete_workflow(example_data: Path, tmp_path: Path) -> None:
    """Test the complete CLI workflow as documented in README."""
    runner = CliRunner()
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)

    # Step 1: Prepare Inputs
    logger.info("Testing Step 1: Prepare Inputs")
    result = runner.invoke(
        cli,
        [
            "prepare-inputs",
            "--meta-data",
            str(example_data / "Example_Meta_Data.csv"),
            "--counts",
            str(example_data / "Example_Counts_5probes.csv"),
            "--config",
            str(example_data / "substances_cell_types.yml"),
            "--meta-mapper",
            str(example_data / "meta_data_mapper.yml"),
            "--batch-key",
            "Exposure plate ID",
            "--output-dir",
            str(results_dir),
        ],
    )
    if result.exit_code != 0:
        pytest.fail(
            f"Step 1 (Prepare Inputs) failed with exit code {result.exit_code}:\n{result.output}",
        )

    # Check if BIFROST input file was created (should be exactly one)
    input_files = [
        f
        for f in results_dir.iterdir()
        if f.name.startswith("BIFROST_input_") and f.name.endswith(".json")
    ]
    if not input_files:
        pytest.fail("Step 1 (Prepare Inputs) did not create any BIFROST input files")
    if len(input_files) != 1:
        pytest.fail(
            f"Step 1 (Prepare Inputs) created {len(input_files)} input files, expected exactly 1",
        )

    input_file = input_files[0]
    # Verify it's the expected filename
    expected_filename = "BIFROST_input_Nitrofurantoin_HepG2.json"
    if input_file.name != expected_filename:
        pytest.fail(
            f"Step 1 created file '{input_file.name}', expected '{expected_filename}'",
        )
    logger.info("✓ Step 1 completed successfully")

    # Step 2: Split Data
    logger.info("Testing Step 2: Split Data")
    result = runner.invoke(
        cli,
        [
            "split-data",
            "--input-file",
            str(input_file),
            "--output-dir",
            str(results_dir),
            "--prefix",
            "test",
            "--batch-mode",
            "all",
            "--batch-size",
            "5",
        ],
    )
    if result.exit_code != 0:
        pytest.fail(
            f"Step 2 (Split Data) failed with exit code {result.exit_code}:\n{result.output}",
        )

    # Check all expected outputs were created
    if not (results_dir / "Data").exists():
        pytest.fail("Step 2 (Split Data) did not create Data directory")
    if not (results_dir / "Fits").exists():
        pytest.fail("Step 2 (Split Data) did not create Fits directory")
    if not (results_dir / "test.manifest.csv").exists():
        pytest.fail(
            "Step 2 (Split Data) did not create manifest file in output directory",
        )
    if not (results_dir / "test_batch0.tar.gz").exists():
        pytest.fail("Step 2 (Split Data) did not create batch archive")

    # Check that exactly 5 probe files were created
    probe_files = list((results_dir / "Data").glob("*.pkl"))
    expected_probes = [
        "ACBD3_59.pkl",
        "CEP89_11010.pkl",
        "MPDU1_11661.pkl",
        "OAS3_90233.pkl",
        "TMEM183A_34069.pkl",
    ]
    if len(probe_files) != 5:
        pytest.fail(
            f"Step 2 created {len(probe_files)} probe files, expected exactly 5",
        )

    actual_probe_names = sorted([f.name for f in probe_files])
    expected_probe_names = sorted(expected_probes)
    if actual_probe_names != expected_probe_names:
        pytest.fail(
            f"Step 2 created probes {actual_probe_names}, expected {expected_probe_names}",
        )
    logger.info("✓ Step 2 completed successfully")

    # Step 3: Run Analysis
    logger.info("Testing Step 3: Run Analysis")
    # Build command exactly as we did manually - one -f flag per probe file
    cmd = ["run-analysis", "--output-dir", str(results_dir), "--n-cores", "5"]
    for probe_file in sorted(probe_files):  # Sort for consistent order
        cmd.extend(["-f", str(probe_file)])

    result = runner.invoke(cli, cmd)
    if result.exit_code != 0:
        pytest.fail(
            f"Step 3 (Run Analysis) failed with exit code {result.exit_code}:\n{result.output}",
        )

    # Check that analysis results were created for all probes
    fit_files = list((results_dir / "Fits").glob("*.pkl"))
    json_files = list((results_dir / "Fits").glob("*.json"))

    if len(fit_files) != 5:
        pytest.fail(f"Step 3 created {len(fit_files)} fit files, expected exactly 5")
    if len(json_files) != 5:
        pytest.fail(f"Step 3 created {len(json_files)} JSON files, expected exactly 5")

    # Verify we have results for each probe
    expected_fit_names = [probe.replace(".pkl", "") for probe in expected_probes]
    actual_fit_names = sorted([f.stem for f in fit_files])
    if actual_fit_names != sorted(expected_fit_names):
        pytest.fail(
            f"Step 3 created fits for {actual_fit_names}, expected {sorted(expected_fit_names)}",
        )
    logger.info("✓ Step 3 completed successfully")

    # Step 4: Compress Output
    logger.info("Testing Step 4: Compress Output")
    result = runner.invoke(
        cli,
        [
            "compress-output",
            "--fits-dir",
            str(results_dir / "Fits"),
            "--output",
            str(results_dir / "summary.json.zip"),
        ],
    )
    if result.exit_code != 0:
        pytest.fail(
            f"Step 4 (Compress Output) failed with exit code {result.exit_code}:\n{result.output}",
        )

    summary_file = results_dir / "summary.json.zip"
    if not summary_file.exists():
        pytest.fail("Step 4 (Compress Output) did not create summary file")

    # Check that the file is actually compressed (should be smaller than uncompressed JSON)
    if summary_file.stat().st_size < 1000:  # Should be at least 1KB
        pytest.fail("Step 4 created summary file that seems too small")
    logger.info("✓ Step 4 completed successfully")

    # Step 5: Create Report
    logger.info("Testing Step 5: Create Report")
    result = runner.invoke(
        cli,
        [
            "create-report",
            "--summary-file",
            str(summary_file),
            "--test-substance",
            "MyChemical",
            "--cell-type",
            "HepaRG",
            "--output-name",
            str(results_dir / "report.html"),
        ],
    )
    if result.exit_code != 0:
        pytest.fail(
            f"Step 5 (Create Report) failed with exit code {result.exit_code}:\n{result.output}",
        )

    report_file = results_dir / "report.html"
    if not report_file.exists():
        pytest.fail("Step 5 (Create Report) did not create report file")

    # Check that report data directory was also created
    if not (results_dir / "report_data").exists():
        pytest.fail("Step 5 (Create Report) did not create report_data directory")

    # Check that the report file has reasonable size (should be several MB)
    if report_file.stat().st_size < 100000:  # Should be at least 100KB
        pytest.fail("Step 5 created report file that seems too small")

    logger.info("✓ Step 5 completed successfully")
    logger.info("✓ All steps completed successfully!")


def test_workflow_with_errors(example_data: Path, tmp_path: Path) -> None:
    """Test error handling in the CLI workflow."""
    runner = CliRunner()
    results_dir = tmp_path / "results"

    # Test missing input file
    result = runner.invoke(
        cli,
        [
            "prepare-inputs",
            "--meta-data",
            "nonexistent.csv",
            "--counts",
            str(example_data / "Example_Counts_5probes.csv"),
            "--config",
            str(example_data / "substances_cell_types.yml"),
            "--meta-mapper",
            str(example_data / "meta_data_mapper.yml"),
            "--batch-key",
            "Exposure plate ID",
            "--output-dir",
            str(results_dir),
        ],
    )
    assert result.exit_code != 0
    assert "Path 'nonexistent.csv' does not exist" in result.output

    # Test invalid batch key
    result = runner.invoke(
        cli,
        [
            "prepare-inputs",
            "--meta-data",
            str(example_data / "Example_Meta_Data.csv"),
            "--counts",
            str(example_data / "Example_Counts_5probes.csv"),
            "--config",
            str(example_data / "substances_cell_types.yml"),
            "--meta-mapper",
            str(example_data / "meta_data_mapper.yml"),
            "--batch-key",
            "NonexistentKey",
            "--output-dir",
            str(results_dir),
        ],
    )
    assert result.exit_code != 0
    # Check for the error message in the exception
    assert "Batch key 'NonexistentKey' not found in metadata columns" in str(
        result.exception,
    )
