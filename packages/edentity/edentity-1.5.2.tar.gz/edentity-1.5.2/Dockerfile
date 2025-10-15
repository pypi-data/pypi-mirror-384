FROM condaforge/mambaforge:24.9.2-0
LABEL io.github.snakemake.containerized="true"
LABEL io.github.snakemake.conda_env_hash="428af8958ac834f4d5e69a3faf690bf39fa900031c1f165ab52b89a72457ebf4"

# Step 2: Retrieve conda environments

# Conda environment:
#   source: workflow/envs/cutadapt.yaml
#   prefix: /conda-envs/edf345db7c901e7d3dc3ca55e5af56e2
#   priority: strict
#   name: cutadapt
#   channels:
#     - conda-forge
#     - bioconda
#     - nodefaults
#   dependencies:
#     - pip
#     - cutadapt=4.9
#     - biopython=1.84
#     - pip:
#       - nbitk==0.3.2
RUN mkdir -p /conda-envs/edf345db7c901e7d3dc3ca55e5af56e2
COPY workflow/envs/cutadapt.yaml /conda-envs/edf345db7c901e7d3dc3ca55e5af56e2/environment.yaml

# Conda environment:
#   source: workflow/envs/fastp.yaml
#   prefix: /conda-envs/b588f57bfee906402cd48ab9480dae74
#   priority: strict
#   name: fastp
#   channels:
#     - conda-forge
#     - bioconda
#     - nodefaults
#   dependencies:  
#     - fastp=0.24.0
RUN mkdir -p /conda-envs/b588f57bfee906402cd48ab9480dae74
COPY workflow/envs/fastp.yaml /conda-envs/b588f57bfee906402cd48ab9480dae74/environment.yaml

# Conda environment:
#   source: workflow/envs/multiqc.yaml
#   prefix: /conda-envs/54be30cf1928dd479025b6fec1bd55c4
#   priority: strict
#   name: multiqc
#   channels:
#     - conda-forge
#     - bioconda
#     - nodefaults
#   dependencies:  
#     - multiqc=1.27.1
RUN mkdir -p /conda-envs/54be30cf1928dd479025b6fec1bd55c4
COPY workflow/envs/multiqc.yaml /conda-envs/54be30cf1928dd479025b6fec1bd55c4/environment.yaml

# Conda environment:
#   source: workflow/envs/vsearch.yaml
#   prefix: /conda-envs/1575a372c32dbdce868ad7f639c291bf
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
#     - pip:
#       - nbitk==0.3.2
RUN mkdir -p /conda-envs/1575a372c32dbdce868ad7f639c291bf
COPY workflow/envs/vsearch.yaml /conda-envs/1575a372c32dbdce868ad7f639c291bf/environment.yaml

# Step 3: Generate conda environments

RUN conda env create --prefix /conda-envs/edf345db7c901e7d3dc3ca55e5af56e2 --file /conda-envs/edf345db7c901e7d3dc3ca55e5af56e2/environment.yaml && \
    conda env create --prefix /conda-envs/b588f57bfee906402cd48ab9480dae74 --file /conda-envs/b588f57bfee906402cd48ab9480dae74/environment.yaml && \
    conda env create --prefix /conda-envs/54be30cf1928dd479025b6fec1bd55c4 --file /conda-envs/54be30cf1928dd479025b6fec1bd55c4/environment.yaml && \
    conda env create --prefix /conda-envs/1575a372c32dbdce868ad7f639c291bf --file /conda-envs/1575a372c32dbdce868ad7f639c291bf/environment.yaml && \
    conda clean --all -y
