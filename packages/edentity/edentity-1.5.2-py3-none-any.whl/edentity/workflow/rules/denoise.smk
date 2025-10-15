import os

rule denoise:
    input:        
        derep = os.path.join(config["work_dir"], "Results", "dereplication",
            f'{{sample}}_merged_trimmed_filtered_derep.fasta'),
        
        derep_report = os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_derep_report.tsv')        
    output:
        denoised = temp(os.path.join(config["work_dir"], "Results",
            "denoise", f'{{sample}}_merged_trimmed_filtered_derep_denoised.fasta')),
        
        summary_report = temp(os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_denoise_report.tsv'))

    log: 
        log = os.path.join(config["work_dir"], "logs", "denoise",  f'{{sample}}_denoising.log')
    conda: config['conda']
    script:
        "../scripts/denoise.py"