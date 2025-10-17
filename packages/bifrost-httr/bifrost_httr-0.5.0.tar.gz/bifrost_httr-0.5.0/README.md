# BIFROST-HTTr Package

**Bayesian Inference for Region of Signal Threshold (BIFROST) for High-Throughput Transcriptomics (HTTr)**

A Python package for high-throughput transcriptomics (HTTr) analysis using Bayesian modeling to infer point-of-departure (PoD) from concentration-response datasets.

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quickstart](#quickstart)
   1. [Example Files](#1-example-files)
   2. [Processing Steps](#2-processing-steps)
4. [Configuration](#configuration)
5. [Input Data Requirements](#input-data-requirements)
6. [Command Line Interface](#command-line-interface)
7. [Usage](#usage)
8. [Report Template Customization](#report-template-customization)
9. [Features](#features)
10. [Requirements](#requirements)
11. [License](#license)

## Introduction

BIFROST-HTTr is a Python package designed for high-throughput transcriptomics (HTTr) analysis. It uses Bayesian modeling to infer point-of-departure (PoD) from concentration-response datasets, providing robust statistical analysis and visualization tools.

## Installation

### From PyPI (Recommended)

```bash
pip install bifrost-httr
```

### From Source (Development)

```bash
git clone https://github.com/seqera-services/bifrost-httr.git
cd bifrost-httr
pip install -e .
```

> **⚠️ Important Note for Windows Users**
> 
> While BIFROST-HTTr works smoothly on Linux and macOS, Windows users may encounter installation challenges with CmdStanPy, which is a core dependency. To ensure successful installation:
> 
> 1. Install the RTools 4.0 toolchain which includes the required C++ compiler (g++ 8) and GNU Make utility
> 2. Ensure your system has the Universal C Runtime (UCRT) - this comes with Windows 10 and newer
> 3. Add the toolchain directories to your PATH:
>    ```
>    C:\rtools44\usr\bin
>    C:\rtools44\x86_64-w64-mingw32.static.posix\bin
>    ```
> 
> For detailed installation instructions, see:
> - [CmdStanPy Installation Guide](https://mc-stan.org/cmdstanpy/installation.html)
> - [CmdStan User Guide - Windows Setup](https://mc-stan.org/docs/cmdstan-guide/installation.html#windows)

## Quickstart

This quickstart guide will help you get up and running with BIFROST-HTTr using example data. The example files can be found in the [`examples/minimal`](examples/minimal) directory.

### 1. Example Files

The minimal example includes:

1. **Metadata File** ([`Example_Meta_Data.csv`](examples/minimal/Example_Meta_Data.csv)): Contains sample information including test substances, concentrations, and quality metrics
2. **Counts File** ([`Example_Counts_5probes.csv`](examples/minimal/Example_Counts_5probes.csv)): Contains gene expression counts for 5 example probes
3. **Configuration File** ([`substances_cell_types.yml`](examples/minimal/substances_cell_types.yml)): Defines test substances and cell types
4. **Metadata Mapper** ([`meta_data_mapper.yml`](examples/minimal/meta_data_mapper.yml)): Maps your column names to BIFROST's internal format (optional if your columns already match)

### 2. Processing Steps

BIFROST-HTTr supports two processing paths:

#### Path 1: From Raw Data

##### Step 1: Prepare Inputs
First, convert your raw data (metadata and counts) into BIFROST's internal JSON format. This step performs data validation and quality checks.

```bash
bifrost-httr prepare-inputs \
  --meta-data examples/minimal/Example_Meta_Data.csv \
  --counts examples/minimal/Example_Counts_5probes.csv \
  --config examples/minimal/substances_cell_types.yml \
  --meta-mapper examples/minimal/meta_data_mapper.yml \
  --batch-key "Exposure plate ID" \
  --output-dir results
```

This command will:
- Validate your metadata and counts files
- Apply quality control filters
- Map column names using the metadata mapper (in this case, mapping the `TREATMENT_VESSEL_ID` column from the metadata file to BIFROST's internal `Exposure plate ID` field)
- Group samples by exposure plate ID for batch processing
- Generate a `bifrost_input.json` file in the output directory

##### Step 2: Split Data
Next, process the prepared JSON data into a format suitable for the Stan model:

```bash
bifrost-httr split-data \
  --input-file results/BIFROST_input_*.json \
  --output-dir results \
  --prefix test \
  --batch-mode all \
  --batch-size 5
```

This step:
- Uses the same directory (`results`) for consistency
- Processes the JSON input into the Stan model format
- Organizes the data into batches (use `--batch-size` to control how many probes per batch)
- Creates a manifest file for tracking the analysis

The command will create:
- A `Data` directory in `results` containing processed .pkl files for each probe
- An empty `Fits` directory in `results` where analysis results will be stored
- A manifest file (`test.manifest.csv`) tracking which probes are in which batch

##### Step 3: Run Analysis
Finally, perform the concentration-response analysis on the processed data:

```bash
bifrost-httr run-analysis \
  -f results/Data/ACBD3_59.pkl \
  -f results/Data/CEP89_11010.pkl \
  -f results/Data/MPDU1_11661.pkl \
  -f results/Data/OAS3_90233.pkl \
  -f results/Data/TMEM183A_34069.pkl \
  --output-dir results \
  --n-cores 5
```

This step:
- Uses the same directory (`results`) for consistency
- Fits Bayesian models to your data using the specified probe files (use -f flag for each probe file)
- Calculates point-of-departure (PoD) values
- Generates the data needed for concentration-response plots
- Creates summary statistics that will be used in report generation

The results will be stored in the `Fits` directory alongside the `Data` directory (in this example, `results/Fits`) and will be used by the report generation step to create the actual plots and visualizations.

##### Step 4: Compress Output
Before creating the report, compress the analysis results into a single summary file:

```bash
bifrost-httr compress-output \
  --fits-dir results/Fits \
  --output results/summary.json.zip
  --test-substance "MyChemical" \
  --cell-type "HepaRG"
```

This step:
- Uses the same directory (`results`) for consistency
- Combines all probe analysis results into a single summary file
- Automatically compresses the output by default (recommended)
- Use `--no-compression` flag only if you need an uncompressed JSON file

Note: By default, output is compressed. If you specify a `.json` filename, it will be automatically corrected to `.json.zip` for compressed output. Use `--no-compression` with a `.json` extension for uncompressed output.

##### Step 5: Create Report
Generate a comprehensive HTML report with plots and statistics:

```bash
bifrost-httr create-report \
  --summary-file results/summary.json.zip \
  --test-substance "MyChemical" \
  --cell-type "HepaRG" \
  --output-name results/report.html
```

This step:
- Creates interactive concentration-response plots
- Generates summary statistics and tables
- Produces a comprehensive HTML report in the results directory

#### Path 2: From Pre-prepared JSON

If you already have data in BIFROST's JSON format, you can skip the preparation step and run the analysis directly:

```bash
bifrost-httr run-analysis \
  --input your_input.json \
  --output-dir results
```

This is useful when:
- Re-analyzing previously prepared data
- Using data prepared by other tools
- Running batch analyses with pre-formatted inputs

## Configuration

BIFROST-HTTr supports flexible parameter configuration through both configuration files and command-line arguments.

### Configuration File

Create a YAML configuration file with your parameters. Required and optional parameters should use Title Case:

```yaml
# Required parameters
Test substances:
  - "Paracetamol"
  - "Nitrofurantoin"

Cell types:
  - "HepG2"
  - "HepaRG"

# Optional parameters (with defaults shown)
Batch key: "Batch"
Minimum percent mapped reads: 80.0
Minimum number mapped reads: 1000000
Minimum average treatment count: 10
Random seed: 5

# Optional divider for additional sample grouping
Additional divider: "N/A"

# Optional filters to exclude specific samples
Specific filters:
  # Example: exclude samples from specific batches
  # Batch: ["batch3"]
```

### Command-Line Arguments

Most parameters can also be provided via command-line arguments, which take precedence over config file values:

```bash
bifrost-httr prepare-inputs \
  --meta-data metadata.csv \
  --counts counts.csv \
  --config config.yaml \
  --batch-key "Exposure plate ID" \
  --min-percent-mapped-reads 50.0 \
  --min-num-mapped-reads 100000 \
  --min-avg-treatment-count 5
```

### Parameter Precedence

When the same parameter is specified in multiple places, the following precedence order applies:
1. Command-line arguments (highest priority)
2. Configuration file values
3. Default values (lowest priority)

For example:
- If `--batch-key` is provided via CLI, it overrides the `Batch key` from the config file
- If neither is provided, the default value "Exposure plate ID" is used

## Input Data Requirements

BIFROST-HTTr supports two distinct input modes:

1. Raw data input - for processing new experimental data
2. Pre-prepared JSON input - for using previously formatted data

### Raw Data Input

For raw data input, you need three files:

#### 1. Metadata CSV File

The metadata file must contain sample information with the following required fields. The column names must either match BIFROST's internal format exactly (shown below) or be mapped using a metadata mapper file.

| Internal Column Name   | Type    | Description                                | Validation Rules           |
| --------------------- | ------- | ------------------------------------------ | -------------------------- |
| `Test substance`      | string  | Test substance name                        | Must not contain spaces    |
| `Cell type`           | string  | Cell type used in experiment              | Must not contain spaces    |
| `Concentration`       | numeric | Test substance concentration              | Must be non-negative (≥ 0) |
| `Sample ID`           | string  | Unique sample identifier                   | Must not contain spaces    |
| `Num. mapped reads`   | integer | Number of mapped reads                    | Must be non-negative (≥ 0) |
| `Percent mapped reads`| numeric | Percentage of mapped reads                | Must be between 0 and 100  |

Example metadata structure with matching column names:
```csv
Test substance,Cell type,Concentration,Sample ID,Num. mapped reads,Percent mapped reads,Batch
Nitrofurantoin,HepG2,0.0192,S1_HG2_NFUR_1,2857440,86.0,Batch1
Nitrofurantoin,HepG2,0.096,S2_HG2_NFUR_2,5710831,95.35,Batch1
```

#### 2. Counts CSV File

The counts file contains gene expression data in matrix format:
- First column contains unique probe identifiers
- Column headers must match `SAMPLE_ID` values from metadata
- Values must be non-negative integers
- No missing values allowed

Example counts structure:
```csv
Probe_ID,S1_HG2_NFUR_1,S2_HG2_NFUR_2
ACBD3_59,79,141
CEP89_11010,75,240
MPDU1_11661,263,310
```

#### 3. Metadata Mapper YAML File (Optional)

The metadata mapper is an optional file that defines how columns in your metadata file map to BIFROST's internal format. This allows you to use your existing data files without renaming columns. The mapper is not needed if your metadata file's column names already match BIFROST's internal format (see section 1).

Example mapper structure for custom column names:
```yaml
Test substance:
  - "TEST_SUBSTANCE"  # Will look for this column first
  - "Compound"        # Will use this as fallback
  - "Chemical"        # Another fallback option

Cell type:
  - "CELL_TYPE"
  - "Cell Line"

Concentration:
  - "CONCENTRATION"
  - "Dose"
  - "Treatment Concentration"

Sample ID:
  - "SAMPLE_ID"
  - "Sample"

Num. mapped reads:
  - "NUM_MAPPED_READS"
  - "Total Reads"

Percent mapped reads:
  - "PERCENT_MAPPED_READS"
  - "Mapping Rate"
```

When using a mapper, you must specify mappings for all required fields. For each field, you can provide multiple possible column names - BIFROST will use the first matching column it finds in your metadata file.

Example metadata structure with custom column names (requires mapper):
```csv
TEST_SUBSTANCE,CELL_TYPE,CONCENTRATION,SAMPLE_ID,NUM_MAPPED_READS,PERCENT_MAPPED_READS,BATCH
Nitrofurantoin,HepG2,0.0192,S1_HG2_NFUR_1,2857440,86.0,Batch1
Nitrofurantoin,HepG2,0.096,S2_HG2_NFUR_2,5710831,95.35,Batch1
```

### Pre-prepared JSON Input

Alternatively, you can provide pre-formatted JSON files that contain all necessary information in BIFROST's internal format:

```json
{
    "test_substance": "Nitrofurantoin",
    "cell_type": "HepG2",
    "probes": ["ACBD3_59", "CEP89_11010"],
    "counts": [
        [79, 141, 153],  // Counts for probe 1
        [75, 240, 140]   // Counts for probe 2
    ],
    "batch_index": [1, 1, 1],
    "concentration": [0.0192, 0.096, 0.48],
    "n_treatment_batch": 1
}
```

When using pre-prepared JSON input:
- The metadata mapper and configuration files are not required
- Multiple JSON files can be processed in parallel
- Each JSON file represents one complete dataset (substance + cell type combination)

## Command Line Interface

The package provides a unified command-line interface with the following commands in order of typical execution:

```bash
# 1. [Optional] Pre-compile Stan model
# Only needed when running multiple analysis jobs on a shared filesystem
# to prevent redundant compilations and race conditions
bifrost-httr compile-model [STAN_FILE]  # Uses built-in model if no file specified

# 2. Prepare BIFROST input files from raw data
bifrost-httr prepare-inputs \
  --meta-data META_DATA.csv \           # Required: Path to meta data CSV file
  --meta-mapper META_MAPPER.yml \       # Required: Path to meta data mapper YAML file
  --counts COUNTS.csv \                 # Required: Path to counts CSV file
  --config CONFIG.yml \                 # Required: Path to configuration YAML file
  --output-dir OUTPUT_DIR \             # Required: Directory to store outputs
  [--batch-key BATCH_KEY] \            # Field to use as batch key (default: 'Exposure plate ID')
  [--min-percent-mapped-reads VALUE] \  # Minimum percentage mapped reads (default: 50.0)
  [--min-num-mapped-reads VALUE] \      # Minimum number mapped reads (default: 100000)
  [--min-avg-treatment-count VALUE]     # Minimum average treatment count (default: 5)

# 3. Split data into processing batches
bifrost-httr split-data \
  --input-file INPUT.json \            # Required: Path to input data json
  --output-dir OUTPUT_DIR \            # Required: Directory to store outputs
  --prefix PREFIX \                    # Required: Prefix for output files
  [--batch-size N] \                   # Number of files per batch (default: 0)
  [--batch-mode batch|all] \           # Batch mode: individual or single archive (default: all)
  [--archive-mode tar|directory] \     # Archive mode: tar.gz or folders (default: tar)
  [--test-probes N] \                  # Number of probes to sample for testing
  [--random-seed SEED]                 # Random seed for reproducibility (default: 5)

# 4. Run concentration-response analysis
# Note: Will automatically compile the model if needed
bifrost-httr run-analysis \
  --data-files DATA1.pkl [DATA2.pkl ...] \  # Required: List of probe .pkl files (at least one)
  [--model-executable MODEL.exe] \          # Path to compiled Stan model (optional)
  [--n-cores N] \                          # Number of cores to use
  [--seed SEED]                            # Random seed for reproducibility

# 5. Compress intermediate output files
bifrost-httr compress-output \
  --fits-dir FITS_DIR \               # Required: Directory with probe .pkl files
  --output OUTPUT.json \              # Required: Path to output (will auto-correct .json to .json.zip if compressed)
  [--test-substance NAME] \          # Name of the test substance (will be stored within the output json)
  [--cell-type TYPE] \               # Type of cell used in the test (will be stored within the output json)
  [--seed SEED] \                     # Random seed for reproducibility
  [--no-compression]                  # Save as plain JSON without compression

# 6. Create MultiQC reports from analysis results
bifrost-httr create-report \
  --summary-file SUMMARY.json \        # Required: Path to summary JSON file
  --test-substance NAME \              # Required: Name of the test substance
  --cell-type TYPE \                   # Required: Type of cell used in the test
  [--output-name NAME] \               # Output filename (default: multiqc_report.html)
  [--timepoint TIME] \                 # Exposure duration (default: 24 hours)
  [--conc-units uM|ugml-1|mgml-1] \   # Concentration units (default: uM)
  [--interactive-plots] \              # Force interactive plots
  [--n-fold-change-probes N] \         # Number of most regulated probes (default: 5)
  [--cds-threshold VALUE] \            # CDS threshold for filtering (default: 0.5)
  [--n-lowest-means N] \               # Number of lowest mean PoD probes (default: 10)
  [--n-pod-stats N] \                  # Probes in PoD statistics table (default: 100)
  [--plot-height PIXELS] \             # Height of conc-response plots (default: 400)
  [--pod-vs-fc-height PIXELS] \        # Height of PoD vs FC plot (default: 600)
  [--no-cds-threshold] \               # Don't filter probes by CDS threshold
  [--custom-templates FILE]            # Custom template YAML file
```

For detailed help on any command:

```bash
bifrost-httr --help
bifrost-httr <command> --help
```

## Usage

### As a Library

```python
import bifrost_httr

# Load and process data
data = bifrost_httr.BifrostData("summary.json")
report = bifrost_httr.BifrostMultiQCReport(data, test_substance="MyChemical")
report.create_report()
```

## Report Template Customization

BIFROST reports can be customized by providing your own template file to override the default text and formatting:

```bash
# Create a custom template file
cp templates/example_custom_templates.yml templates/my_custom_templates.yml

# Edit the template to customize specific sections
# Only include the sections you want to change - others will use defaults

# Use custom templates in your report
bifrost-httr create-report \
  --summary-file summary.json \
  --custom-templates templates/my_custom_templates.yml \
  --test-substance "MyChemical" \
  --cell-type "HepaRG"
```

### Available Template Sections

You can customize any of the following sections:
- **Introduction text** - Main report introduction and methodology
- **Summary descriptions** - Explanations for statistics and plots
- **Plot guides** - Instructions for reading concentration-response plots
- **Section overviews** - Text for different analysis sections
- **No-data messages** - Custom messages when data is insufficient

### Template Variables

Templates support variables like `{test_substance}`, `{cell_type}`, `{timepoint}`, `{cds_threshold}`, and `{conc_units}` that are automatically filled in from your analysis parameters.

For complete documentation and examples, see the [`templates/`](templates/) directory.

## Features

- Bayesian modeling of concentration-response relationships
- Point-of-departure (PoD) estimation with uncertainty quantification
- Global PoD calculation across multiple probes
- Interactive visualization and reporting
- Parallel processing support
- Stan-based statistical modeling

## Requirements

- Python ≥3.10
- NumPy, Pandas, SciPy
- CmdStanPy for Bayesian modeling
- MultiQC and Plotly for reporting
- PyYAML for configuration files
- Click for command-line interface

## License

# Copyright (C) 2025 as Unilever Global IP Limited
# Bifrost-HTTr is free software: you can redistribute it and/or modify it under the terms
# of the GNU Lesser General Public License as published by the Free Software Foundation,
# either version 3 of the License. Bifrost-HTTr is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with Bifrost-HTTr.
# If not, see https://www.gnu.org/licenses/ . It is the responsibility of Bifrost-HTTr users to
# familiarise themselves with all dependencies and their associated licenses.
