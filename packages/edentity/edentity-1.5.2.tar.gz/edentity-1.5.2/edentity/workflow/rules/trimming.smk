import os

rule trimming:
    input:        
        merged = os.path.join(config["work_dir"], "Results",
            "merge", f'{{sample}}_merged.fastq'), 
        
        merge_report = os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_merge_report.tsv')       
    output:
        trimmed = temp(os.path.join(config["work_dir"], "Results",
            "trimming", "trimmed_seqs", f'{{sample}}_merged_trimmed.fastq')),
        
        json = os.path.join(config["work_dir"], "Results","trimming",
            "json_reports", f'{{sample}}_merged_trimmed.json'),
        
        summary_report = temp(os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_trimming_report.tsv'))
    log: 
        log = os.path.join(config["work_dir"],"logs","trimming", f'{{sample}}_trimming.log')
    # conda: "../envs/cutadapt.yaml"
    script:
        "../scripts/trimming.py"
