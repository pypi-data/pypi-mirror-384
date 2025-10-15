"""
Read Mapping Rules
"""

# Reference and index files will be determined at runtime

rule bowtie2_index:
    input:
        reference=lambda wildcards: config.get("reference_genome", "resources/reference.fasta")
    output:
        index=expand("resources/reference.{ext}", ext=["1.bt2", "2.bt2", "3.bt2", "4.bt2", "rev.1.bt2", "rev.2.bt2"])
    params:
        prefix="resources/reference"
    threads: config["pipeline"]["threads"]
    shell:
        """
        bowtie2-build "{input.reference}" {params.prefix}
        """

# Single-end alignment rule
rule bowtie2_align_single:
    input:
        reads=lambda wildcards: f"{RESULTS_DIR}/trimmed/{wildcards.sample}_trimmed.fastq.gz" if wildcards.sample in SAMPLE_FILES else [],
        index=expand("resources/reference.{ext}", ext=["1.bt2", "2.bt2", "3.bt2", "4.bt2", "rev.1.bt2", "rev.2.bt2"])
    output:
        bam=f"{RESULTS_DIR}/mapped/{{sample}}.bam",
        bai=f"{RESULTS_DIR}/mapped/{{sample}}.bam.bai"
    wildcard_constraints:
        sample="|".join(SAMPLE_FILES.keys()) if SAMPLE_FILES else "NONE_SINGLE_END"
    params:
        index_prefix="resources/reference",
        mode=config["mapping"]["bowtie2"]["mode"]
    threads: config["mapping"]["bowtie2"]["threads"]
    shell:
        """
        bowtie2 --{params.mode} -p {threads} -x {params.index_prefix} -U "{input.reads}" | \
        samtools view -bS - | \
        samtools sort - -o {output.bam}
        samtools index "{output.bam}"
        """

rule bowtie2_align_paired:
    input:
        r1=lambda wildcards: f"{RESULTS_DIR}/trimmed/{wildcards.sample}_R1_trimmed.fastq.gz" if wildcards.sample in PAIRED_FILES else [],
        r2=lambda wildcards: f"{RESULTS_DIR}/trimmed/{wildcards.sample}_R2_trimmed.fastq.gz" if wildcards.sample in PAIRED_FILES else [],
        index=expand("resources/reference.{ext}", ext=["1.bt2", "2.bt2", "3.bt2", "4.bt2", "rev.1.bt2", "rev.2.bt2"])
    output:
        bam=f"{RESULTS_DIR}/mapped/{{sample}}.bam",
        bai=f"{RESULTS_DIR}/mapped/{{sample}}.bam.bai"
    wildcard_constraints:
        sample="|".join(PAIRED_FILES.keys()) if PAIRED_FILES else "NONE_PAIRED_END"
    params:
        index_prefix="resources/reference",
        mode=config["mapping"]["bowtie2"]["mode"]
    threads: config["mapping"]["bowtie2"]["threads"]
    shell:
        """
        bowtie2 --{params.mode} -p {threads} -x {params.index_prefix} -1 "{input.r1}" -2 "{input.r2}" | \
        samtools view -bS - | \
        samtools sort - -o {output.bam}
        samtools index {output.bam}
        """

rule mapping_stats:
    input:
        bam=f"{RESULTS_DIR}/mapped/{{sample}}.bam"
    output:
        stats=f"{RESULTS_DIR}/mapped/{{sample}}_stats.txt"
    shell:
        """
        samtools flagstat "{input.bam}" > {output.stats}
        """
