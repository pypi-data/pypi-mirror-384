from nbitk.Tools.cutadapt import Cutadapt
from snakemake.script import snakemake
import logging
import json
import os
import subprocess
import polars as pl
from Bio.Seq import Seq


config = snakemake.config


def reverse_primer(seq):
    return f"{Seq(seq).reverse_complement()}"


def get_min_overlap(adapter1, adapter2, ratio=0.9):
    return int(min(len(adapter1), len(adapter2)) * ratio)


def get_overlap(adapter, ratio=0.9):
    return int(len(adapter) * ratio)


def is_valid_dna_sequence(sequence):
    """
    Check if a DNA sequence contains only valid IUPAC codes, including ambiguous codes.
    Parameters:
    sequence (str): The DNA sequence to validate.
    Returns:
    bool: True if the sequence is valid, False otherwise.
    """
    valid_characters = set("ACGTBDHKMNRSVWYI")
    return all(base in valid_characters for base in sequence)


def generate_cutadapt_linked_primers(
    forward_primers: list[str], reverse_primers: list[str], anchored: bool = False
):
    combinations = []
    for fwd in forward_primers:
        for rev in reverse_primers:

            if anchored is True:  # min_overlap is not needed if anchoring is true
                combinations.extend(["-g", f"^{fwd}...{reverse_primer(rev)}$"])
            else:
                combinations.extend(
                    [
                        "-g",
                        f"{fwd};min_overlap={get_overlap(fwd)}...{reverse_primer(rev)};min_overlap={get_overlap(rev)}",
                    ]
                )

    return combinations


cutadapt_runner = Cutadapt(config)

#  set logging to file
handler = logging.FileHandler(snakemake.log.log, mode="w")
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "cutadapt-trimming - %(asctime)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
cutadapt_runner.logger.addHandler(handler)

# read in the primers
forward_primers = config["forward_primer"].split(",")
reverse_primers = config["reverse_primer"].split(",")

# validate that the primers have valid dna sequences
for primer in forward_primers + reverse_primers:
    if not is_valid_dna_sequence(primer):
        raise ValueError(f"Primer {primer} is not a valid DNA sequence (IUPAC codes).")

try:

    if len(forward_primers) > 1 or len(reverse_primers) > 1:
        # construct cutadapt command
        # submit directly instead of nbitk.run() since nbitkit requires key value,
        # and we are using the cutadapt with many primers all with the same key name e.g -g
        # this needs to be added on nbitk of course
        cutadapt_cmd = [
            "cutadapt",
            "--cores",
            "0",
            "--discard-untrimmed",
            "--output",
            snakemake.output.trimmed,
            "--json",
            snakemake.output.json,
            snakemake.input.merged,
        ] + [
            adapter
            for adapter in generate_cutadapt_linked_primers(
                forward_primers, reverse_primers, config["anchoring"]
            )
        ]

        with open(snakemake.log.log, mode="w") as log_file:
            subprocess.run(
                cutadapt_cmd, check=True, stdout=log_file, stderr=subprocess.STDOUT
            )
    else:  # use nbitkit cutadapt
        #  params

        cutadapt_runner.set_input_sequences([snakemake.input.merged])
        cutadapt_runner.set_output(snakemake.output.trimmed)
        cutadapt_runner.set_json_report(snakemake.output.json)
        cutadapt_runner.set_discard_untrimmed(
            discard_untrimmed=config["discard_untrimmed"]
        )

        # set adapter 1: "(^)ADAPTER1;min_overlap=int...ADAPTER2;min_overlap=int"
        if config["anchoring"] is True:
            cutadapt_runner.set_front_adapter(
                f"^{forward_primers[0]}...{reverse_primer(reverse_primers[0])}$"
            )
        else:
            cutadapt_runner.set_front_adapter(
                f"{forward_primers[0]};min_overlap={get_overlap(forward_primers[0])}..."
                f"{reverse_primer(reverse_primers[0])};min_overlap={get_overlap(reverse_primers[0])}"
            )

        #  Remove the nbitkit loghandler to prevent writing to stdo
        for fh in cutadapt_runner.logger.handlers[:]:
            cutadapt_runner.logger.removeHandler(fh)
        cutadapt_runner.logger.addHandler(handler)

        # run cutadapt
        return_code = cutadapt_runner.run()

    # Parse json output to collect metrics
    sample_name = os.path.split(snakemake.input.merged)[1].split("_merged")[
        0
    ]  # get sample name exluding the extension
    with open(snakemake.output.json, "r") as file:
        json_content = json.load(file)
        inputReads = int(json_content["read_counts"]["input"])
        passedReads = int(json_content["read_counts"]["output"])

    #  Write the metrics to a TSV file
    report_df = pl.read_csv(snakemake.input.merge_report, separator="\t")
    report_df = report_df.with_columns(pl.lit(passedReads).alias("trimmed"))
    report_df.write_csv(snakemake.output.summary_report, separator="\t")

except Exception as e:
    cutadapt_runner.logger.error(e, exc_info=True)
    print(e)
    exit(1)
