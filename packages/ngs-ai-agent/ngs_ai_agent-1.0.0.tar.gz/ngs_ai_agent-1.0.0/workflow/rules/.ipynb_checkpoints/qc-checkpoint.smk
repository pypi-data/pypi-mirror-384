"""
Quality Control Rules
"""

rule fastqc:
    input:
        # Use the file path from SAMPLES dictionary
        lambda wildcards: SAMPLES[wildcards.sample] if wildcards.sample in SAMPLES else f"data/raw/{wildcards.sample}.fastq.gz"
    output:
        html=f"{RESULTS_DIR}/qc/fastqc/{{sample}}_fastqc.html",
        zip=f"{RESULTS_DIR}/qc/fastqc/{{sample}}_fastqc.zip"
    params:
        outdir=f"{RESULTS_DIR}/qc/fastqc"
    threads: config["qc"]["fastqc"]["threads"]
    shell:
        """
        mkdir -p {params.outdir}
        fastqc "{input}" -o {params.outdir} -t {threads}
        # Rename output files to match expected names
        cd {params.outdir}
        mv $(basename "{input}" .fastq.gz)_fastqc.html {wildcards.sample}_fastqc.html
        mv $(basename "{input}" .fastq.gz)_fastqc.zip {wildcards.sample}_fastqc.zip
        """

rule multiqc:
    input:
        expand(f"{RESULTS_DIR}/qc/fastqc/{{sample}}_fastqc.zip", sample=SAMPLES.keys())
    output:
        f"{RESULTS_DIR}/qc/multiqc/multiqc_report.html"
    params:
        outdir=f"{RESULTS_DIR}/qc/multiqc"
    shell:
        """
        mkdir -p {params.outdir}
        multiqc {RESULTS_DIR}/qc/fastqc -o {params.outdir}
        """
