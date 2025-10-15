import os
import pandas as pd
import logging


rule searchExact:
    input:
        derep = os.path.join(config["work_dir"], "Results",
            "dereplication",  f'{{sample}}_merged_trimmed_filtered_derep.fasta'), 
        ESV_fasta = os.path.join(config["work_dir"],  "Results",
            "ESVs_fasta", f'{{sample}}_ESV.fasta')
    output:
        ESV_table_per_sample = temp(os.path.join(config["work_dir"],"Results",
            "ESV_tables", f'{{sample}}_ESV_table.tsv'))
    log: 
        log = os.path.join(config["work_dir"], "logs","search_exact", f'{{sample}}_search_exact.log')
    conda: config['conda']
    script:
        "../scripts/search_exact.py"


rule esv_table:
    input:
        sample_esv_tables = expand(os.path.join(config["work_dir"], "Results",
            "ESV_tables",f'{{sample}}_ESV_table.tsv'), sample=SAMPLE_NAMES),
        
        remove_chimera_reports = expand(os.path.join(config["work_dir"], "Results",
            "report", f'{{sample}}_remove_chimera_report.tsv'), sample=SAMPLE_NAMES),
        
    output:
        ESV_table = os.path.join(config["work_dir"], "Results",
            "report", f"{os.path.basename(config['work_dir'])}_ESV_table.tsv"),

        summary_report = os.path.join(config["work_dir"], "Results",
            "report", f"{os.path.basename(config['work_dir'])}_summary_report.tsv"),
        
        custom_multiqc_data = temp(os.path.join(config["work_dir"], "Results",
            "report", f"{os.path.basename(config['work_dir'])}_custom_multiqc_data_mqc.txt")),
        
        esv_sequence_fasta_file = os.path.join(config["work_dir"], "Results",
            "ESVs_fasta", f'{os.path.basename(config["work_dir"])}_esv_sequences.fasta'),
        
    log: 
        log = os.path.join(config["work_dir"], "logs", "ESV_table", "ESV_table.log")
    conda: config['conda']
    retries: 1
    script:
        "../scripts/esv_table.py"


rule create_multiqc_filelist:
    input:
        fastp_json = expand(os.path.join(config["work_dir"], "Results",
            "report","fastpQC", f'{{sample}}_fastpQC.json'),sample=SAMPLE_NAMES),

        cutadapt_json = expand(os.path.join(config["work_dir"], 
            "Results","trimming", "json_reports", 
            f'{{sample}}_merged_trimmed.json'),sample=SAMPLE_NAMES),
        
        custom_multiqc_data = os.path.join(config["work_dir"], "Results",
            "report", f"{os.path.basename(config['work_dir'])}_custom_multiqc_data_mqc.txt")
    output:
        multiqc_filelist_txt =  os.path.join(config['work_dir'],
            "edentity_pipeline_settings","multiqc_config", "multiqc_filelist.txt")
    log: os.path.join(config["work_dir"], "logs", "multiqc", f"{os.path.basename(config['work_dir'])}_creating_multiqc_filelist.log")
    script:
        "../scripts/create_multiqc_filelist.py"


rule multiqc:
    input:
        file_list = os.path.join(config['work_dir'],
            "edentity_pipeline_settings","multiqc_config", "multiqc_filelist.txt"),
        
        fastp_json = expand(os.path.join(config["work_dir"], "Results",
        "report","fastpQC", f'{{sample}}_fastpQC.json'),sample=SAMPLE_NAMES),

        cutadapt_json = expand(os.path.join(config["work_dir"], 
            "Results","trimming", "json_reports", 
            f'{{sample}}_merged_trimmed.json'),sample=SAMPLE_NAMES),
        
        custom_multiqc_data = os.path.join(config["work_dir"], "Results",
            "report", f"{os.path.basename(config['work_dir'])}_custom_multiqc_data_mqc.txt")
    output:
        html = os.path.join(config["work_dir"], "Results", "report",
            f"{os.path.basename(config['work_dir'])}_multiqc_reports",
            f"{os.path.basename(config['work_dir'])}_multiqc_report.html")
    params:
        qc_dir = os.path.join(config["work_dir"], "Results", 
            "report", f"{os.path.basename(config['work_dir'])}_multiqc_reports"),        
        
        config = os.path.join(config['work_dir'],
            "edentity_pipeline_settings","multiqc_config", "config.yaml"),
        report_name = os.path.basename(f"{config['work_dir']}_multiqc_report.html")
    # conda: "../envs/multiqc.yaml"

    log: os.path.join(config["work_dir"], "logs", "multiqc", f"{os.path.basename(config['work_dir'])}_multiqc.log")

    shell:
        """
        multiqc --config {params.config} \
        -o {params.qc_dir} --filename {params.report_name} \
        --no-data-dir \
        --file-list {input.file_list} -f > {log} 2>&1
        """