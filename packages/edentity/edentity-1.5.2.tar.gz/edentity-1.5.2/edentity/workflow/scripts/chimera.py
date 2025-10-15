from nbitk.Tools.vsearch import Vsearch
from snakemake.script import snakemake
import logging
import re
import os
import polars as pl

config = snakemake.config
vsearch_removeChimera = Vsearch(config)

# set logging to file
handler = logging.FileHandler(snakemake.log.log, mode="w")
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "vsearch-removeChimera - %(asctime)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
vsearch_removeChimera.logger.addHandler(handler)

vsearch_removeChimera = Vsearch(config)
try:

    #  params
    chimera_params = {
        "uchime3_denovo": snakemake.input.denoised,
        "nonchimeras": snakemake.output.ESV_fasta,
        "relabel_sha1": "",
        "relabel_keep": "",
    }

    vsearch_removeChimera.set_params(chimera_params)

    # Remove the nbitkit loghandler to prevent writing to stdo
    for fh in vsearch_removeChimera.logger.handlers[:]:
        vsearch_removeChimera.logger.removeHandler(fh)

    vsearch_removeChimera.logger.addHandler(handler)

    return_code = vsearch_removeChimera.run()

    # Parse run logs to collect metrics

    sample_name = os.path.split(snakemake.input.denoised)[1].split("_merged")[
        0
    ]  # get sample name exluding the extension

    with open(snakemake.log.log, "r") as file:
        log_content = file.read()

        inReads_match = re.search(r"(\d+)\s+total\s+sequences.", log_content)
        unique_clusters_match = re.search(r"(\d+)\s+unique\s+sequences.", log_content)
        chimeric_match = re.search(r"Found\s+(\d+)", log_content)
        borderline_match = re.search(
            r"and\s+(\d+)(?:\s+\(\d+\.\d+%\))?\s+borderline\s+sequences", log_content
        )
        n_esv_match = re.search(
            r"Found\s+(\d+)(?:\s+\(\d+\.\d+%\))?\s+chimeras,\s+(\d+)(?:\s+\(\d+\.\d+%\))?\s+non-chimeras",
            log_content,
        )

        if (
            inReads_match
            and chimeric_match
            and unique_clusters_match
            and n_esv_match
            and borderline_match
        ):
            inReads_match = int(inReads_match.group(1))
            chimeric_match = int(chimeric_match.group(1))
            borderline_match = int(borderline_match.group(1))
            unique_clusters_match = int(
                unique_clusters_match.group(1)
            )  # not used anywhere at the moment;
            n_esv = int(n_esv_match.group(2))

        else:
            raise ValueError("Could not find the required information in the log file")

        #  Write the metrics to a TSV file
    report_df = pl.read_csv(snakemake.input.denoise_report, separator="\t")
    report_df = report_df.with_columns(
        [
            pl.lit(chimeric_match).alias("chimeric"),
            pl.lit(borderline_match).alias("borderline"),
        ]
    )
    report_df = report_df.with_columns(
        pl.when(pl.col("Sample") == sample_name)
        .then(n_esv)
        .otherwise(int(0))
        .alias("ESVs")
    )
    report_df.write_csv(snakemake.output.summary_report, separator="\t")


except Exception as e:
    vsearch_removeChimera.logger.error(e, exc_info=True)
    print(e)
    exit(1)
