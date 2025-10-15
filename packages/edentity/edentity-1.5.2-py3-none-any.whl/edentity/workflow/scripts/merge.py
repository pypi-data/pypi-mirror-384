from nbitk.Tools.vsearch import Vsearch
from snakemake.script import snakemake
import logging
import re
import os
import polars as pl
from datetime import datetime

config = snakemake.config  # will point to snakemake config file

# Instantiate Vsearch runner
vsearch_merge = Vsearch(config)

# set logging to file
handler = logging.FileHandler(snakemake.log.log, mode="w")
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "vsearch-merge - %(asctime)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
vsearch_merge.logger.addHandler(handler)
try:
    # capture run starts
    # collect stats about the run
    root, project_name = os.path.split(snakemake.config["work_dir"])
    sample_file_name = os.path.split(snakemake.input.r1)[1]

    if (
        "reformated" in sample_file_name
    ):  # if the sample file is reformated (from AVITI)
        sample_name = sample_file_name.split("_reformated")[0]
    else:
        sample_name = re.split(r"_R[12]\.", sample_file_name)[
            0
        ]  # get sample name excluding the extension

    # Parse run logs to collect metrics
    current_start_datetime = datetime.now().strftime("%d-%m-%Y %H:%M")

    # start the merge process
    # define parameters
    merge_params = {
        "fastq_mergepairs": f"{snakemake.input.r1}",
        "reverse": f"{snakemake.input.r2}",
        "fastqout": f"{snakemake.output.merged}",
        "fastq_maxdiffpct": config["maxdiffpct"],
        "fastq_maxdiffs": config["maxdiffs"],
        "fastq_minovlen": config["minovlen"],
        "fastq_qmax": config["fastq_qmax"],  # max expected quality score
        "fastq_allowmergestagger": "",
    }
    vsearch_merge.set_params(merge_params)

    # Remove the nbitkit loghandler to prevent writing to stdo
    for fh in vsearch_merge.logger.handlers[:]:
        vsearch_merge.logger.removeHandler(fh)
    vsearch_merge.logger.addHandler(handler)

    # run vsearch
    exit_code = vsearch_merge.run()
    # extract general QC stats from fastp logs
    with open(snakemake.input.fastp_log, "r") as fastp_log:
        log_content = fastp_log.read()
        total_reads = int(re.search(r"total reads:\s*(\d+)", log_content).group(1))

    # Extract merge stats from vseearch merge log
    with open(snakemake.log.log, "r") as file:
        log_content = file.read()

        pairs_match = re.search(r"(\d+)\s+Pairs", log_content)
        merged_match = re.search(r"(\d+)\s+Merged", log_content)

        if pairs_match and merged_match:
            pairs = int(pairs_match.group(1))
            merged = int(merged_match.group(1))
            # print(pairs, merged)
        else:
            raise ValueError("Could not find the required information in the log file")

        #  Write the metrics to a TSV file
        tsv_output_dir = os.path.join(config["work_dir"], "Results", "report")
        if not os.path.exists(tsv_output_dir):
            os.makedirs(tsv_output_dir)

        tsv_output_path = snakemake.output.summary_report
        # get percent merged
        try:
            merged_percent = merged / pairs * 100
        except ZeroDivisionError:
            merged_percent = 0.0

        if not os.path.isfile(
            tsv_output_path
        ):  # if the file is run for the first time, write the column names
            with open(tsv_output_path, "a") as tsv_file:
                tsv_file.write(
                    "Sample\ttotal_reads\tfastp_filtered\tmerged\tmerged_percent\n"
                )
                try:
                    merged_percent = merged / pairs * 100
                except ZeroDivisionError:
                    merged_percent = 0.0
                tsv_file.write(
                    f"{sample_name}\t{total_reads}\t{pairs}\t{merged}\t{merged_percent}\n"
                )
        else:  # if the file already exists, append the new metrics
            report_df = pl.read_csv(tsv_output_path, separator="\t")
            temp_df = pl.DataFrame(
                {
                    "Sample": [sample_name],
                    "total_reads": [total_reads],
                    "fastp_filtered": [pairs],
                    "merged": [merged],
                    "merged_percent": [merged_percent],
                }
            )
            merged_df = pl.concat([report_df, temp_df])
            merged_df.write_csv(tsv_output_path, separator="\t")

except Exception as e:
    vsearch_merge.logger.error(e, exc_info=True)
    print(e)
    exit(1)
