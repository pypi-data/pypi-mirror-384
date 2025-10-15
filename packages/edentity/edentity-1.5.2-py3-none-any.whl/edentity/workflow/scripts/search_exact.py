from nbitk.Tools.vsearch import Vsearch
from snakemake.script import snakemake
import logging
import polars as pl
from Bio import SeqIO
import os

config = snakemake.config
vsearch_exact = Vsearch(config)

# set logging to file
handler = logging.FileHandler(snakemake.log.log, mode="w")
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "vsearch-searchExact - %(asctime)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
vsearch_exact.logger.addHandler(handler)


try:

    #  params
    search_exact_params = {
        "search_exact": snakemake.input.derep,
        "db": snakemake.input.ESV_fasta,
        "output_no_hits": "",
        "maxhits": "1",
        "otutabout": snakemake.output.ESV_table_per_sample,
    }

    vsearch_exact.set_params(search_exact_params)

    # Remove the nbitkit loghandler to prevent writing to stdo
    for fh in vsearch_exact.logger.handlers[:]:
        vsearch_exact.logger.removeHandler(fh)
    vsearch_exact.logger.addHandler(handler)

    # call up the vsearch_exact
    return_code = vsearch_exact.run()

    sample_esv_df = pl.read_csv(snakemake.output.ESV_table_per_sample, separator="\t")

    # Add fasta sequence to sample ESV_table
    if sample_esv_df.shape[0] > 0:  # check if there are ESVs in the sample
        for record in SeqIO.parse(snakemake.input.ESV_fasta, "fasta"):
            sample_esv_df = sample_esv_df.with_columns(
                pl.when(pl.col("#OTU ID") == str(record.id))
                .then(pl.lit(str(record.seq)))
                .otherwise(
                    pl.col("sequence") if "sequence" in sample_esv_df.columns else None
                )
                .alias("sequence")
            )

    else:
        # the fasta file is empty, so we create an empty sequence column
        # first assert the file is empty
        assert (
            os.path.getsize(snakemake.input.ESV_fasta) == 0
        ), "Fasta file is not empty but no ESVs found."

    # write out the ESV table
    sample_esv_df.write_csv(snakemake.output.ESV_table_per_sample, separator="\t")

except Exception as e:
    vsearch_exact.logger.error(e, exc_info=True)
    print(e)
    exit(1)
