from snakemake.script import snakemake
import logging
import os
import concurrent.futures
from datetime import datetime
import subprocess
import json
from custom_multiqc_module import prep_multqc_data
import polars as pl

"""
This script aggregates ESV tables into a single table,
processes summary reports, and generates JSON files for metabarcoding run statistics.
The abundance_ratio represents the ratio of ESV abundance to the total abundance for each sample.
"""

config = snakemake.config

# Aggregate the ESV tables into a single table
# set logging configuration
logging.basicConfig(
    filename=snakemake.log.log,
    level=logging.INFO,
    format="creating ESV table - %(asctime)s - %(levelname)s - %(message)s",
)
handler = logging.getLogger()


def process_file(file):
    """
    Processes a given file to extract and rename columns for ESV (Exact Sequence Variant) data.

    Args:
        file (str): The file path to the input ESV table. The file is expected to be a tab-separated
                    values (TSV) file with at least two columns.

    Returns:
        polars.DataFrame: A DataFrame containing the processed ESV data. The first column is renamed
                          to "ESV_ID", and the second column is renamed to the sample name derived
                          from the file name. If the input file contains no rows, the original empty
                          DataFrame is returned.
    """
    sample_name = os.path.basename(file).split("_ESV_table")[0]
    handler.info(f"Reading {file}")
    temp_df = pl.read_csv(file, separator="\t")
    # print(sample_name)
    if temp_df.height > 0:
        # print(temp_df.shape)
        temp_df = temp_df.rename(
            {temp_df.columns[0]: "ESV_ID", temp_df.columns[1]: sample_name}
        )
    else:
        handler.info(f"No ESVs detected in sample:{file} ")
    return temp_df


# get the project name
# this will be used as the prefix for the output reports
project_name = os.path.basename(config["work_dir"])


try:
    esv_tables = [
        [f, os.path.basename(f).split("_ESV_table.tsv")[0]]
        for f in sorted(snakemake.input.sample_esv_tables)
        if os.path.isfile(os.path.join(f))
    ]

    # project_name = os.path.basename(config["work_dir"])

    hash_seq = {}
    hast_sample = {}
    samples = []
    for path_f, sample_name in esv_tables:
        if sample_name in samples:
            handler.warning(
                f"Sample {sample_name} already exists in the ESV table. Skipping duplicate."
            )
            continue
        keep_sample = False
        handler.info(f"Reading {sample_name}")
        t_sum = 0
        with open(path_f, "r") as f:
            for i, line in enumerate(f):
                if i == 0 or not line.strip():
                    continue
                keep_sample = True
                seq_id, count, seq = line.strip().split("\t")
                if seq_id not in hash_seq:
                    hash_seq[seq_id] = {"seq": seq, "total": 0}
                    hast_sample[seq_id] = {}
                hast_sample[seq_id][sample_name] = count
                hash_seq[seq_id]["total"] += int(count)
        if keep_sample:
            samples.append(sample_name)

    handler.info("Writting ESV tables...")
    with open(snakemake.output.esv_sequence_fasta_file, "w") as fasta:
        with open(snakemake.output.ESV_table, "w") as f:
            sample_str = "\t".join(samples)
            f.write(f"ESV_NO\tESV_ID\t{sample_str}\tsequence\n")
            for i, (seq_id, d) in enumerate(
                sorted(hash_seq.items(), key=lambda x: x[1]["total"], reverse=True),
                start=1,
            ):
                f.write(f"ESV_{i}\t{seq_id}\t")
                f.write(
                    "\t".join(
                        [
                            (
                                hast_sample[seq_id][sample]
                                if sample in hast_sample[seq_id]
                                else "0"
                            )
                            for sample in samples
                        ]
                    )
                )
                f.write(f"\t{d['seq']}\n")
                fasta.write(
                    f">{seq_id}\n{d['seq']}\n"
                )  # write out only unique sequences

    df = pl.read_csv(snakemake.output.ESV_table, separator="\t")
    # read tsv report
    report_path = os.path.join(config["work_dir"], "Results", "report")
    summary_report_df = pl.DataFrame()

    def read_report(file):
        if os.path.exists(file):
            return pl.read_csv(file, separator="\t")
        return pl.DataFrame()

    handler.info("Reading summary reports")

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=config["cpu_cores"]
    ) as executor:
        results = list(
            executor.map(read_report, snakemake.input.remove_chimera_reports)
        )

    handler.info("Merging summary reports")
    summary_report_df = pl.concat(results).unique()

    # Calculate percentages at each processing step
    # Merged reads as percentage of total read pairs
    # handler.info("Calculating merged reads percentage")

    # summary_report_df = summary_report_df.with_columns(
    #     (pl.col("merged_reads") / pl.col("fastp_filtered") * 100)
    #     .fill_null(0)
    #     .alias("merged_percent")
    # )

    # Primer-trimmed reads as percentage of merged reads
    # handler.info("Calculating primer trimmed reads percentage")
    # summary_report_df = summary_report_df.with_columns(
    #     (pl.col("trimmed") / pl.col("merged_reads") * 100)
    #     .fill_null(0)
    #     .alias("trimmed_percent")
    # )

    # Quality filtered reads as percentage of primer-trimmed reads
    # handler.info("Calculating quality filtered reads percentage")
    # summary_report_df = summary_report_df.with_columns(
    #     (pl.col("vsearch_filtered") / pl.col("trimmed") * 100)
    #     .fill_null(0)
    #     .alias("passed_filtering_percent")
    # )

    # Dereplicated reads as percentage of quality filtered reads
    # handler.info("Calculating dereplicated reads percentage")
    # summary_report_df = summary_report_df.with_columns(
    #     (pl.col("dereplicated") / pl.col("vsearch_filtered") * 100)
    #     .fill_null(0)
    #     .alias("dereplicated_percent")
    # )

    # # Denoised reads as percentage of dereplicated reads
    # handler.info("Calculating denoised reads percentage")
    # summary_report_df = summary_report_df.with_columns(
    #     (pl.col("denoised") / pl.col("dereplicated") * 100)
    #     .fill_null(0)
    #     .alias("denoised_percent")
    # )
    # summary_report_df = summary_report_df.to_pandas()
    # write out the summary report
    # reorder columns for ease of readability
    col_order = [
        "Sample",
        "total_reads",
        "fastp_filtered",
        "merged",
        "merged_percent",
        "trimmed",
        # "trimmed_percent",
        "vsearch_filtered",
        # "passed_filtering_percent",
        "dereplicated",
        # "dereplicated_percent",
        "denoised",
        # "denoised_percent",
        "chimeric",
        "borderline",
        "ESVs",
    ]

    summary_report_df = summary_report_df.select(col_order)

    # rename ESVs to n_esv and convert to integer
    summary_report_df = summary_report_df.rename({"ESVs": "n_esv"})
    summary_report_df = summary_report_df.with_columns(pl.col("n_esv").cast(pl.Int64))
    summary_report_df.write_csv(snakemake.output[1], separator="\t", float_precision=2)

    # write out the custom multiqc data file
    # custom_multiqc_data_file = os.path.join(report_path, f"{project_name}_custom_multiqc_data.txt")
    prep_multqc_data(summary_report_df, snakemake.output[2])

    # write out the snakmake config as metabarcoding_run.json

    if config["make_json_reports"] is True:
        # construct table 6: metabarcoding_sample
        handler.info("Creating metabarcoding_sample json report")
        summary_report_df = summary_report_df.rename({"Sample": "sample_id"})
        # Convert to list of dicts and write as JSON with indent=2
        summary_report_dict = summary_report_df.to_dicts()
        with open(
            os.path.join(
                report_path, f"{project_name}_table_6_metabarcoding_sample.json"
            ),
            "w",
        ) as f:
            json.dump(summary_report_dict, f, indent=2)

        # construct table 8: ESV sequence
        # convert df to pandas dataframe

        handler.info("Creating ESV sequence json report")
        unique_esv = df.select(["ESV_ID", "sequence"]).unique()
        unique_esv = unique_esv.with_columns(
            pl.col("sequence").str.len_chars().alias("sequence_length")
        )
        unique_esv_dict = unique_esv.to_dicts()
        with open(
            os.path.join(report_path, f"{project_name}_table_8_ESV_sequence.json"), "w"
        ) as f:
            json.dump(unique_esv_dict, f, indent=2)

        # construct table 7: ESV
        handler.info("Creating ESV json report")
        # Drop the "ESV_NO" and "sequence" columns (strs)
        df = df.drop(["ESV_NO", "sequence"])

        # Melt the DataFrame from wide to long format
        esv_table_long = df.melt(
            id_vars=["ESV_ID"], variable_name="sample_id", value_name="abundance"
        )

        # convert abundance to integer and rename ESV_ID to sequence_id
        # Convert 'abundance' to integer
        esv_table_long = esv_table_long.with_columns(pl.col("abundance").cast(pl.Int64))
        # add esv abundance ratio

        # Rename column
        esv_table_long = esv_table_long.rename({"ESV_ID": "sequence_id"})

        # Compute total abundance per sample_id and add it as a new column
        esv_table_long = esv_table_long.with_columns(
            esv_table_long.group_by("sample_id")
            .agg(pl.col("abundance").sum().alias("total_abundance"))
            .join(esv_table_long, on="sample_id", how="left")
            .select("total_abundance")
        )

        esv_table_long_dict = esv_table_long.to_dicts()
        with open(
            os.path.join(report_path, f"{project_name}_table_7_ESV.json"), "w"
        ) as f:
            json.dump(esv_table_long_dict, f, indent=2)

    # construct table 5: metabarcoding_run
    handler.info("Creating metabarcoding_run json report")

    # get workflow version
    # uses git latest git tag of the repo
    cmd = "git describe --tags --always"
    git_tag = subprocess.run(cmd.split(), capture_output=True, text=True)
    if not git_tag.stderr:
        config["workflow_version"] = git_tag.stdout.split("\n")[0]
    else:  # just incase some errors arise from git; especially when the pipeline is used outside edentity
        config["workflow_version"] = None  # terrible, the value must be provided!!

    #  construct the metabarcoding_run.json
    metabarcoding_run_dict = {}
    metabarcoding_run_dict["runID"] = config["runID"]
    metabarcoding_run_dict["start_time"] = config["start_time"]

    metabarcoding_run_dict["workflow_version"] = config["workflow_version"]

    metabarcoding_run_dict["settings"] = {
        "raw_data_dir": config["raw_data_dir"],
        "make_json_reports": config["make_json_reports"],
        "forward_primer": config["forward_primer"],
        "reverse_primer": config["reverse_primer"],
        "work_dir": config["work_dir"],
        "dataType": config["dataType"],
        "anchoring": config["anchoring"],
        "maxdiffpct": config["maxdiffpct"],
        "maxdiffs": config["maxdiffs"],
        "minovlen": config["minovlen"],
        "min_length": config["min_length"],
        "max_length": config["max_length"],
        "maxEE": config["maxEE"],
        "alpha": config["alpha"],
        "minsize": config["minsize"],
        "conda": config["conda"],
        "license_file": config["license_file"],
        "changelog_file": config["changelog_file"],
        "cpu_cores": config["cpu_cores"],
        "log_level": config["log_level"],
        "snakemake_version": config["snakemake_version"],
    }
    metabarcoding_run_dict["commandline_settings"] = config["command_line_args"]
    config["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metabarcoding_run_dict["end_time"] = config["end_time"]
    with open(
        os.path.join(report_path, f"{project_name}_table_5_metabarcoding_run.json"), "w"
    ) as metabarcoding_run:
        json.dump(metabarcoding_run_dict, metabarcoding_run, indent=2)

except Exception as e:
    handler.error(e, exc_info=True)
    print(e)
    exit(1)
