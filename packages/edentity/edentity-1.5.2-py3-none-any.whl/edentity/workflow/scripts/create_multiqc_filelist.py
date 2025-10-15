from snakemake.script import snakemake
import logging
from pathlib import Path

# set logging
handler = logging.FileHandler(
    snakemake.log[0], mode="w"
)  # or snakemake.log.log if that's correct
handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def write_out_file_paths(files_path: list, output_txt_file_path: str):
    with open(output_txt_file_path, "w") as txt:
        for line in files_path:
            file_path = Path(line).resolve()
            assert file_path.exists(), f"file path does not exist: {file_path}"
            txt.write(f"{file_path}\n")
    return None


# writeout the files
try:

    write_out_file_paths(
        files_path=(
            list(snakemake.input.fastp_json)
            + list(snakemake.input.cutadapt_json)
            + [snakemake.input.custom_multiqc_data]
        ),
        output_txt_file_path=snakemake.output.multiqc_filelist_txt,
    )
    logger.info(
        f"successfully written out paths to: {Path(snakemake.output.multiqc_filelist_txt).resolve()}"
    )
except Exception as e:
    logger.error(f"{e}")
    raise
