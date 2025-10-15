import subprocess

# from Bio.Align import MultipleSeqAlignment
# from Bio.Align.Applications import ClustalOmegaCommandline
# from Bio.SeqRecord import SeqRecord
# import tempfile
# import os

# Define the function to resolve ambiguous bases using IUPAC codes


def resolve_ambiguity(bases):
    # Remove duplicates to deal with ambiguity
    bases_set = set(bases)

    # If there's only one unique base, return it directly
    if len(bases_set) == 1:
        return bases[0]

    # Handle specific cases:
    iupac_codes = {
        frozenset({"A", "C", "T"}): "H",
        frozenset({"A", "C", "G", "T"}): "N",
        frozenset({"A", "C"}): "M",
        frozenset({"A", "G"}): "R",
        frozenset({"C", "G"}): "S",
        frozenset({"A", "T"}): "W",
        frozenset({"C", "T"}): "Y",
        frozenset({"G", "T"}): "K",
    }

    return iupac_codes.get(frozenset(bases_set), "N")


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


def align_primers(primers):
    """
    Align primers using MUSCLE via subprocess.
    Returns a list of aligned primer sequences with the same length.
    """
    # Create a temporary file to store the input sequences
    with open("temp_input.fasta", "w") as f:
        for i, primer in enumerate(primers):
            f.write(f">Primer_{i}\n{primer}\n")

    # run muscle
    muscle_cmd = [
        "muscle",
        "-align",
        "temp_input.fasta",
        "-output",
        "temp_output.fasta",
    ]

    subprocess.run(muscle_cmd, check=True)
    # Read the aligned sequences from the output file
    aligned_primers = []
    with open("temp_output.fasta", "r") as f:
        for line in f:
            if line.startswith(">"):
                continue
            aligned_primers.append(line.strip())

    # Clean up temporary files
    # os.remove("temp_input.fasta")
    # os.remove("temp_output.fasta")

    return aligned_primers


def generate_consensus_primer(primers):
    """
    Generate a consensus primer from a list of input primers.
    Parameters:
    primers (list): A list of primer sequences as Biopython Seq objects.
    Returns:
    str: The consensus primer sequence.
    """

    # Perform simple multiple sequence alignment
    aligned_primers = align_primers(primers)

    # Ensure all primers are the same length after alignment
    length = len(aligned_primers[0])
    if not all(len(primer) == length for primer in aligned_primers):
        raise ValueError("All primers must be of the same length")

    consensus = []

    # Iterate over each position in the primers
    for i in range(length):
        # Get all bases at position i from each primer
        bases_at_pos = [primer[i] for primer in aligned_primers]

        # Resolve ambiguity and append to consensus sequence
        consensus_base = resolve_ambiguity(bases_at_pos)
        consensus.append(consensus_base)

    # Join the list of bases into a single consensus sequence
    return "".join(consensus)


# primers = [
#     Seq("AAAAACTAGACTCGTCATCGATGAAGAACGCAGCCC"),  # Primer 1
#     Seq("CTAGACTCGTCAACGATGAAGAACGCAGA"),  # Primer 2
#     Seq("CTAGACTCGTCACCGATGAAGAACGCAG"),  # Primer 3
#     Seq("CTAGACTCGTCATCGATGAAGAACGTAGT"),  # Primer 4
#     Seq("CTAGACTCGTCATCGATGAAGAACGTGG")   # Primer 5
# ]

# # Generate the consensus primer
# consensus_primer = generate_consensus_primer(primers)
# print("Aligned Primers:", consensus_primer)
# # for primer in consensus_primer:
# #     print(primer)
# # CTAGACTCGTCAHCGATGAAGAACGYRG
# # CTAGACTCGTCANCGATGAAGAACGYRG
# # CTAGACTCGTCAHCGATGAAGAACGYRG
# alignment = align_primers(primers)
# for primer in alignment:
#     print(primer)

# forward_primers = [
#     "CTAGACTCGTCATCGATGAAGAACGCAG",
#     "CTAGACTCGTCAACGATGAAGAACGCAG",
#     "CTAGACTCGTCACCGATGAAGAACGCAG",
#     "CTAGACTCGTCATCGATGAAGAACGTAG",
#     "CTAGACTCGTCATCGATGAAGAACGTGG",
#     "GTGYCAGCMGCCGCGGTAA"
# ]

# aligned_primers = align_primers(forward_primers)

# consesus_primers = generate_consensus_primer(forward_primers)
# print("\n forward Consesus primer:",consesus_primers)


# reverse_primesrs = [
#     "TCCTSCGCTTATTGATATGC",
#     "GGACTACNVGGGTWTCTAAT"
# ]

# reverse_consesus_primer = generate_consensus_primer(reverse_primesrs)
# print("\n reverse Consesus primer:",reverse_consesus_primer)
