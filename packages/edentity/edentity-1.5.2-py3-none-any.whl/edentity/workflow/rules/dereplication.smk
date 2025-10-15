import os

rule dereplication:
    input:        
        filtered = os.path.join(config["work_dir"],  "Results",
            "filter", f'{{sample}}_merged_trimmed_filtered.fasta'), 
        
        filter_report = os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_filter_report.tsv')       
    output:
        derep = temp(os.path.join(config["work_dir"], "Results",
            "dereplication",  f'{{sample}}_merged_trimmed_filtered_derep.fasta')),
        
        summary_report = temp(os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_derep_report.tsv'))
    log: 
        log = os.path.join(config["work_dir"], "logs", "dereplication",  f'{{sample}}_dereplication.log')
    conda: config['conda']
    script:
        "../scripts/dereplication.py"