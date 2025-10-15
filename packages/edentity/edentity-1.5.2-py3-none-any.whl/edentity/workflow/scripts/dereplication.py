from nbitk.Tools.vsearch import Vsearch
from snakemake.script import snakemake
import logging
import re
import os
import polars as pl

config = snakemake.config
vsearch_derep = Vsearch(config)

# set logging to file
handler = logging.FileHandler(snakemake.log.log, mode="w")
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "vsearch-dereplication - %(asctime)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
vsearch_derep.logger.addHandler(handler)

try:

    #  params
    derep_params = {
        "fastx_uniques": snakemake.input.filtered,
        "fastaout": snakemake.output.derep,
        "sizeout": "",
        "fasta_width": config["fasta_width"],
        "fastq_qmax": config["fastq_qmax"],
    }  # to allow for high quality data
    vsearch_derep.set_params(derep_params)

    # Remove the nbitkit loghandler to prevent writing to stdo
    for fh in vsearch_derep.logger.handlers[:]:
        vsearch_derep.logger.removeHandler(fh)
    vsearch_derep.logger.addHandler(handler)

    return_code = vsearch_derep.run()

    # Parse run logs to collect metrics

    sample_name = os.path.split(snakemake.input.filtered)[1].split("_merged")[
        0
    ]  # get sample name exluding the extension

    with open(snakemake.log.log, "r") as file:
        log_content = file.read()
        if not log_content.strip():
            dereplicated_match = 0
        else:
            inReads_match = re.search(r"(\d+)\s+seqs", log_content)
            dereplicated_match = re.search(r"(\d+)\s+unique\s+sequences", log_content)

            if inReads_match and dereplicated_match:
                inReads_match = int(inReads_match.group(1))
                dereplicated_match = int(dereplicated_match.group(1))
                # print(inReads_match, dereplicated_match)
            else:
                raise ValueError(
                    "Could not find the required information in the log file"
                )
        #  Write the metrics to a TSV file
    report_df = pl.read_csv(snakemake.input.filter_report, separator="\t")
    report_df = report_df.with_columns(pl.lit(dereplicated_match).alias("dereplicated"))
    report_df.write_csv(snakemake.output.summary_report, separator="\t")


except Exception as e:
    vsearch_derep.logger.error(e, exc_info=True)
    print(e)
    exit(1)
