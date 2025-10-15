import os

rule removeChimera:
    input:        
        denoised = os.path.join(config["work_dir"], "Results",
            "denoise", f'{{sample}}_merged_trimmed_filtered_derep_denoised.fasta'),
        
        denoise_report = os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_denoise_report.tsv')
    output:
        ESV_fasta = temp(os.path.join(config["work_dir"],  "Results",
            "ESVs_fasta", f'{{sample}}_ESV.fasta')),
        
        summary_report = temp(os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_remove_chimera_report.tsv'))
    log: 
        log = os.path.join(config["work_dir"], "logs", "chimera", f'{{sample}}_chimera.log')
    conda: config['conda']
    script:
        "../scripts/chimera.py"