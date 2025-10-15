def prep_multqc_data(summary_report_df, custom_multiqc_data_file):
    # Write the MultiQC custom data file
    with open(custom_multiqc_data_file, "w") as f:
        # Write MultiQC headers
        f.write("# id: 'edentity_summary'\n")
        f.write("# section_name: 'eDentity Pipeline Summary'\n")
        f.write(
            "# description: 'Summary statistics from the eDentity metabarcoding pipeline'\n"
        )
        f.write("# plot_type: 'table'\n")
        f.write("# pconfig:\n")
        f.write("#     id: 'edentity_stats_table'\n")
        f.write("#     title: 'eDentity Pipeline: Sample Processing Statistics'\n")

        # Configure column headers with formatting

        f.write("# headers:\n")
        f.write("#     total_reads:\n")
        f.write("#         title: 'Total reads'\n")
        f.write("#         format: '{:,}'\n")
        f.write("#     fastp_filtered:\n")
        f.write("#         title: 'Fastp filtered'\n")
        f.write("#         format: '{:,}'\n")
        f.write("#     merged_percent:\n")
        f.write("#         title: 'Merged (%)'\n")
        f.write("#         format: '{:.1f}'\n")
        f.write("#         min: 0\n")
        f.write("#         max: 100\n")
        f.write("#     trimmed:\n")
        f.write("#         title: 'Trimmed'\n")
        f.write("#         format: '{:,}'\n")
        f.write("#     vsearch_filtered:\n")
        f.write("#         title: 'Vsearch filtered'\n")
        f.write("#         format: '{:,}'\n")
        f.write("#     dereplicated:\n")
        f.write("#         title: 'Dereplicated'\n")
        f.write("#         format: '{:,}'\n")
        f.write("#     denoised:\n")
        f.write("#         title: 'Denoised'\n")
        f.write("#         format: '{:,}'\n")
        f.write("#     n_esv:\n")
        f.write("#         title: 'ESVs'\n")
        # f.write("#     chimeric_reads:\n")
        # f.write("#         title: 'Chimeric Reads'\n")
        # f.write("#         format: '{:,}'\n")
        # f.write("#     borderline_reads:\n")
        # f.write("#         title: 'Borderline Reads'\n")
        # f.write("#         format: '{:,}'\n")

        # Write the data table
        # Write the data directly from the original summary report
        summary_report_df.write_csv(f, separator="\t")
