"""
Read Trimming Rules
"""

rule cutadapt_single:
    input:
        # Use the file path from SAMPLES dictionary
        lambda wildcards: SAMPLES[wildcards.sample] if wildcards.sample in SAMPLES else f"data/raw/{wildcards.sample}.fastq.gz"
    output:
        trimmed=f"{RESULTS_DIR}/trimmed/{{sample}}_trimmed.fastq.gz",
        report=f"{RESULTS_DIR}/trimmed/{{sample}}_cutadapt.txt"
    params:
        quality_cutoff=config["trimming"]["cutadapt"]["quality_cutoff"],
        min_length=config["trimming"]["cutadapt"]["min_length"],
        adapter=config["trimming"]["cutadapt"]["adapter_3prime"]
    threads: 4
    shell:
        """
        cutadapt \
            -a {params.adapter} \
            -q {params.quality_cutoff} \
            -m {params.min_length} \
            -j {threads} \
            -o {output.trimmed} \
            "{input}" > {output.report}
        """

rule cutadapt_paired:
    input:
        # Use the proper paired files mapping
        r1=lambda wildcards: PAIRED_FILES[wildcards.sample]["r1"] if wildcards.sample in PAIRED_FILES else f"data/raw/{wildcards.sample}_R1.fastq.gz",
        r2=lambda wildcards: PAIRED_FILES[wildcards.sample]["r2"] if wildcards.sample in PAIRED_FILES else f"data/raw/{wildcards.sample}_R2.fastq.gz"
    output:
        r1_trimmed=f"{RESULTS_DIR}/trimmed/{{sample}}_R1_trimmed.fastq.gz",
        r2_trimmed=f"{RESULTS_DIR}/trimmed/{{sample}}_R2_trimmed.fastq.gz",
        report=f"{RESULTS_DIR}/trimmed/{{sample}}_cutadapt.txt"
    params:
        quality_cutoff=config["trimming"]["cutadapt"]["quality_cutoff"],
        min_length=config["trimming"]["cutadapt"]["min_length"],
        adapter=config["trimming"]["cutadapt"]["adapter_3prime"]
    threads: 4
    shell:
        """
        cutadapt \
            -a {params.adapter} \
            -A {params.adapter} \
            -q {params.quality_cutoff} \
            -m {params.min_length} \
            -j {threads} \
            -o {output.r1_trimmed} \
            -p {output.r2_trimmed} \
            "{input.r1}" "{input.r2}" > {output.report}
        """
