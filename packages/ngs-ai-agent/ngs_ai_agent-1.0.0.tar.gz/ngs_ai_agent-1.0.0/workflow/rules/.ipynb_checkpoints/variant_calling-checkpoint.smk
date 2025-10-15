"""
Variant Calling Rules
"""

rule variant_calling:
    input:
        bam=f"{RESULTS_DIR}/mapped/{{sample}}.bam",
        reference=lambda wildcards: config.get("reference_genome", "resources/reference.fasta")
    output:
        vcf=f"{RESULTS_DIR}/variants/{{sample}}_variants.vcf",
        csv=f"{RESULTS_DIR}/variants/{{sample}}_variants_counts.csv"
    params:
        min_coverage=config["variant_calling"]["min_coverage"],
        min_frequency=config["variant_calling"]["min_frequency"],
        quality_threshold=config["variant_calling"]["quality_threshold"],
        max_workers=config["variant_calling"].get("max_workers", 8),
        overlap_min_qual=config["variant_calling"].get("overlap_min_qual", 30)
    script:
        "../scripts/variant_caller.py"

rule merge_variants:
    input:
        vcfs=expand(f"{RESULTS_DIR}/variants/{{sample}}_variants.vcf", sample=SAMPLES.keys())
    output:
        merged=f"{RESULTS_DIR}/variants/merged_variants.vcf"
    shell:
        """
        bcftools merge {input.vcfs} > {output.merged}
        """
