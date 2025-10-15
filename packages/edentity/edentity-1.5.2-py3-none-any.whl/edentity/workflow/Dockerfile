FROM condaforge/mambaforge:latest

# Step 2: Retrieve conda environments

# Conda environment:
#   source: workflow/envs/vsearch.yaml
#   prefix: /conda-envs/163dd44b50c96433c482eacfda446195
#   priority: strict
#   name: vsearch
#   channels:
#     - conda-forge
#     - bioconda
#     - nodefaults
#   dependencies:
#     - vsearch=2.28.1
#     - pip
#     - biopython=1.84
#     - multiqc
#     - fastp
#     - cutadapt=4.9
#     - pip:
#       - nbitk==0.3.2
#       
RUN mkdir -p /conda-envs/163dd44b50c96433c482eacfda446195
COPY workflow/envs/vsearch.yaml /conda-envs/163dd44b50c96433c482eacfda446195/environment.yaml

# Step 3: Generate conda environments

RUN conda env create --prefix /conda-envs/163dd44b50c96433c482eacfda446195 --file /conda-envs/163dd44b50c96433c482eacfda446195/environment.yaml && \
    conda clean --all -y
