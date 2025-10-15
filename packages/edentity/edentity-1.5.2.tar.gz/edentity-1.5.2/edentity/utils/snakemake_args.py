import subprocess
from typing import List
import re


def get_snakemake_args() -> List[str]:
    """
    Fetch the help output of snakemake and parse all valid args.

    This function runs snakemake --help argument, captures the output,
    and extracts valid command-line args.

    Returns:
        List[str]: A list of valid command-line args as strings.
    """
    try:
        # Run the tool with the help flag and capture its output
        result = subprocess.run(
            ["snakemake", "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        help_output = result.stdout

        # Split the output into lines
        help_lines = help_output.split("\n")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting snakemake args: {e}")
        return []

    # set to hold matched parameters
    args = set({})

    # Loop through each line to capture parameters
    for line in help_lines:
        for word in line.split(" "):
            if word.startswith("--"):
                clean_arg = re.sub(r"[^a-zA-Z0-9\-]", "", word)
                args.add(clean_arg)
    return list(args)
