from nbitk.Tools.vsearch import Vsearch
from snakemake.script import snakemake
import logging
import re
import os
import polars as pl


config = snakemake.config
vsearch_filtering = Vsearch(config)

# set logging to file
handler = logging.FileHandler(snakemake.log.log, mode="w")
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "vsearch-filter - %(asctime)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
vsearch_filtering.logger.addHandler(handler)

try:

    filtering_params = {
        "fastq_filter": f"{snakemake.input.trimmed}",
        "fastaout": f"{snakemake.output.filtered}",
        "fastq_maxee": config["maxEE"],
        "fastq_minlen": config["min_length"],
        "fastq_maxlen": config["max_length"],
        "fastq_qmax": config["fastq_qmax"],  # to allow for high quality data
    }

    vsearch_filtering.set_params(filtering_params)
    # Remove the nbitkit loghandler to prevent writing to stdo
    for fh in vsearch_filtering.logger.handlers[:]:
        vsearch_filtering.logger.removeHandler(fh)
    vsearch_filtering.logger.addHandler(handler)

    return_code = vsearch_filtering.run()

    # Parse run logs to collect metrics

    sample_name = os.path.split(snakemake.input.trimmed)[1].split("_merged")[
        0
    ]  # get sample name exluding the extension

    with open(snakemake.log.log, "r") as file:
        log_content = file.read()
        if not log_content.strip():
            passed_match = 0
            discarded_match = 0
        else:

            passed_match = re.search(r"(\d+)\s+sequences\s+kept", log_content)
            discarded_match = re.search(r"(\d+)\s+sequences\s+discarded", log_content)

            if passed_match and discarded_match:
                passed_match = int(passed_match.group(1))
                discarded_match = int(discarded_match.group(1))
                # print(passed_match, discarded_match)
            else:
                raise ValueError(
                    "Could not find the required information in the log file"
                )

        #  Write the metrics to a TSV file
    report_df = pl.read_csv(snakemake.input.trimming_report, separator="\t")
    report_df = report_df.with_columns(pl.lit(passed_match).alias("vsearch_filtered"))
    report_df.write_csv(snakemake.output.summary_report, separator="\t")

# log errors
except Exception as e:
    vsearch_filtering.logger.error(e, exc_info=True)
    print(e)
    exit(1)
