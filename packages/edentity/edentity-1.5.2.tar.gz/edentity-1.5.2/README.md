# eDentity-metabarcoding-pipeline

- [Overview](#overview)
- [Installation](#installation)
    <!-- - [Using pip](#using-pip)
    - [Using conda](#using-conda) -->
- [Usage](#usage)
    - [Using Command Line Arguments](#using-command-line-arguments)
    - [Using a Configuration File](#using-a-configuration-file)
    - [Configuring Snakemake Parameters via Profile](#configuring-snakemake-parameters-via-profile)
    - [Pipeline Output Directory Structure](#pipeline-output-directory-structure)


# Overview

**eDentity** is a [Snakemake](https://snakemake.readthedocs.io/) based metabarcoding workflow designed for Illumina/AVITI paired-end data. It automates [Vsearch](https://github.com/torognes/vsearch) commands to denoise paired-end Fastq sequences and generate Exact Sequence Variants (ESVs). The pipeline is inspired by [APSCALE](https://doi.org/10.1093/bioinformatics/btac588); please cite them if you use this pipeline.

## Installation
<!-- 
Copy the dependencies below into a file (e.g., `edentity-env.yaml`), then create and activate the environment with:

```yaml
priority: strict
name: edentity-env
channels:
    - conda-forge
    - bioconda
    - nodefaults
dependencies:
    - snakemake
    - pip
    - cutadapt=4.9
    - biopython=1.84
    - fastp=0.24.0
    - multiqc=1.27.1
    - vsearch=2.28.1
    - pip:
        - edentity
```
Or simply install with:   -->
Install edentity alongside its dependencies with the command below;

```bash
conda create -n edentity-env \
  python=3.12.8 \
  fastp=0.24.0 \
  cutadapt=4.9 \
  vsearch=2.28.1 \
  biopython=1.84 \
  multiqc=1.27.1 \
  nbitk=0.5.9 \
  "edentity>1.4.8" \
  polars=1.30.0 \
  -c conda-forge -c bioconda -y && \
  conda activate edentity-env

```

# Usage

After installation, the pipeline can be run from the command line. Parameters can be provided either directly via command line arguments or through a configuration file.

## Using Command Line Arguments

Replace the example parameters with those specific to your project:

```bash
edentity --raw_data_dir /path/to/your/raw_fastq_files/ \
--work_dir /path/to/your/work_directory \
--forward_primer pcr primer sequence \
--reverse_primer pcr primer sequence \
--min_length 200 \
--max_length 600
```

## Using a Configuration File

Create a `params_config.yaml` file and copy the YAML template below into it. Adjust the parameters to your project specifications:

```yaml
# project specific
raw_data_dir:  # "/path/to/your/raw_fastq_files/"
work_dir:  # "path/to/your/work_directory"
make_json_reports: False
dataType: "Illumina" # [Illumina, AVITI], one of the two
cpu_cores: 20 

# general quality control (Fastp)
average_qual: 25
length_required: 100
n_base_limit: 0

# PE_merging (these are set to vsearch default values)
maxdiffpct: 100
maxdiffs: 10
minovlen: 10

# primer_trimming (cutadapt)
forward_primer:   
reverse_primer: 
anchoring: False
discard_untrimmed: True

# quality_filtering (vsearch)
min_length: 100
max_length: 600
maxEE: 1

# dereplication (vsearch)
fasta_width: 0

# denoising (vsearch)
alpha: 2
minsize: 4
```

Then run the pipeline with:

```bash
edentity --config_file params_config.yaml
```

**Parameters:**
- `--forward_primer`: Forward primer sequence.
- `--reverse_primer`: Reverse primer sequence.
- `--raw_data_dir`: Directory containing your raw sequencing data.
- `--work_dir`: Directory for pipeline outputs and intermediate files.
- `--make_json_reports`: Set true to create extended json reports 



## Configuring Snakemake Parameters via Profile

You can control Snakemake-specific parameters (such as cluster execution, resource limits, and rerun-incomplete ...) using a profile YAML configuration. This is useful for running the pipeline on HPC clusters or customizing workflow execution.

Create a `snakemake-profile.yaml` file with content like:

```yaml
executor: local # clusters e.g slurm, lsf, aws-batch ... see snakemake documentation 
jobs: "30"
max-jobs-per-second: "10"
max-status-checks-per-second: "10"
local-cores: 44
latency-wait: "30"
printshellcmds: "True"
rerun-incomplete: "False"
keep-incomplete: "True"
conda-cleanup-envs: "False"
dryrun: true
resources:
    mem_mb: 16000
    threads: 8

```
- `executor`: Cluster scheduler (e.g., SLURM).
- `jobs`: Maximum number of parallel jobs.
- `resources`: Default resource limits for jobs.
- `dryrun`: Set to `true` to perform a dry-run (no jobs will be executed).

For more details on these and other Snakemake parameters, see the [Snakemake documentation](https://snakemake.readthedocs.io/en/stable/executing/cli.html).

To use this profile, run:

```bash
edentity --profile snakemake-profile.yaml --config_file params_config.yaml
```

Snakemake parameters can also be provided directly via the command line, 
but they must be specified in their long form (e.g., `--jobs` instead of `-j`). 
Command-line parameters take precedence over those defined in the profile configuration file or the default parameters.

For example, you can use both a profile configuration file and override specific parameters via the command line:

```bash
edentity --profile snakemake-profile.yaml --config_file params_config.yaml \
--jobs 50 --latency-wait 60 --until merge 
```
In this example:
- The `--config_file` option specifies the parameters specific to **eDentity**, such as input directories, primers, and quality control settings.
- The `--profile` option specifies the Snakemake profile configuration file, which controls the behavior of Snakemake, such as job execution, resource limits, and cluster settings.
- The `--jobs`, `--latency-wait`, and `--until` parameters override the corresponding values in the profile configuration file.
- Command-line parameters always take priority over the profile or default settings.




For a full list of options params:

```bash
edentity --help
```

## Pipeline Output Directory Structure

After successful execution, the pipeline generates a structured set of output directories and files within your specified `work_dir`. All file names are prefixed with your `work_dir`. The main components are:

```
work_dir/
│   ├── Results/
│   │   ├── ESVs_fasta/                  # Directory containing FASTA file of ESVs
│   │   └── reports/                     # Reports generated by the pipeline
│   │       ├── ESV_table.tsv            # Table of Exact Sequence Variants (ESVs)
│   │       ├── summary_report.tsv       # Summary statistics for the run
│   │       ├── metabarcoding_run.json     # JSON report with run metadata and parameters
│   │       └── multiqc_report/            # Directory containing MultiQC output
│   │           └── multiqc.html           # Interactive MultiQC report
├── logs/                          # log files for each step of the pipeline
├── edentity_pipeline_settings/    # Stores configuration files used for the pipeline run

```


