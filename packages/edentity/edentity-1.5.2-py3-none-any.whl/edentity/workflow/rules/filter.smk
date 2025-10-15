import os

rule filter:
    input:
        trimmed = os.path.join(config["work_dir"], "Results",
            "trimming", "trimmed_seqs", f'{{sample}}_merged_trimmed.fastq'), 
        
        trimming_report = os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_trimming_report.tsv')       
    output:
        filtered = temp(os.path.join(config["work_dir"],  "Results",
            "filter", f'{{sample}}_merged_trimmed_filtered.fasta')),
        
        summary_report = temp(os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_filter_report.tsv'))
    log: 
        log = os.path.join(config["work_dir"], "logs", "filter",  f'{{sample}}_filter.log')
    conda: config['conda']
    script:
        "../scripts/filter.py"