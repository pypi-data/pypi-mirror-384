import os
import re
from snakemake.logging import logger


# construct r1/r2
# only did this here since it is complicated  to have many if/else statements in the rule section.
if GZ is True:
    read_1 = os.path.join(fastq_files, f"{{sample}}_R1.fastq.gz"),        
    read_2 = os.path.join(fastq_files, f"{{sample}}_R2.fastq.gz")
else:
    read_1 = os.path.join(fastq_files, f"{{sample}}_R1.fastq"),        
    read_2 = os.path.join(fastq_files, f"{{sample}}_R2.fastq")

rule fastpQC: # will test merging using fastp : TODO; make params dynamic.
    input:
        r1 = read_1,
        r2 = read_2
    output:
        r1 = temp(os.path.join(config["work_dir"], "Results",
            "fastpQC", f'{{sample}}_R1.fastq.gz') if GZ else os.path.join(config["work_dir"],
            "Results", "fastpQC", f'{{sample}}_R1.fastq')),
        
        r2 = temp(os.path.join(config["work_dir"], "Results",
            "fastpQC", f'{{sample}}_R2.fastq.gz') if GZ else os.path.join(config["work_dir"],
            "Results", "fastpQC", f'{{sample}}_R2.fastq')),
        
        json = temp(os.path.join(config["work_dir"], "Results",
            "report", "fastpQC", f'{{sample}}_fastpQC.json')),   
        
        html = temp(os.path.join(config["work_dir"], "Results",
            "report", "fastpQC", f'{{sample}}_fastpQC.html')),
    params:
        average_qual = config['average_qual'],
        length_required = config['length_required'],
        n_base_limit = config['n_base_limit']

    log:
        log = os.path.join(config["work_dir"], "logs", "fastpQC", f'{{sample}}_fastpQC.log')
    # conda: "../envs/fastp.yaml"
    threads: config['cpu_cores'] # are this threads or CPUs?
    shell:
        """
        fastp -i {input.r1} -I {input.r2} \
        -o {output.r1} -O {output.r2} \
        --n_base_limit {params.n_base_limit} \
        --length_required {params.length_required} \
        --average_qual {params.average_qual} \
        --dont_eval_duplication \
        --disable_adapter_trimming \
        --json {output.json} --html {output.html} \
        --thread {threads} > {log.log} 2> {log.log}
        """

rule merge: # fastp does QC and can also merge; we will test merging using fastp
    input:        
        r1 = os.path.join(config["work_dir"], "Results", 
            "fastpQC", f'{{sample}}_R1.fastq.gz') if GZ else os.path.join(config["work_dir"],
            "Results", "fastpQC", f'{{sample}}_R1.fastq'),     
        
        r2 = os.path.join(config["work_dir"], "Results", 
            "fastpQC", f'{{sample}}_R2.fastq.gz') if GZ else os.path.join(config["work_dir"],
            "Results", "fastpQC", f'{{sample}}_R2.fastq'),
        
        fastp_log = os.path.join(config["work_dir"], "logs", "fastpQC", f'{{sample}}_fastpQC.log')
    output:
        merged = temp(os.path.join(config["work_dir"], "Results",
            "merge", f'{{sample}}_merged.fastq')),
        
        summary_report = temp(os.path.join(config["work_dir"], "Results",
            "report", f"{{sample}}_merge_report.tsv"))
    log: 
        log = os.path.join(config["work_dir"], "logs", "merge", f'{{sample}}_merge.log')
    conda: config['conda']
    script:
        "../scripts/merge.py"

