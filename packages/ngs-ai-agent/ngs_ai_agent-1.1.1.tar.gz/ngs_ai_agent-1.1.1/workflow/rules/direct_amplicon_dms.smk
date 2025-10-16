"""
Direct Amplicon Deep Mutational Scanning Rules
Handles direct variant calling from amplicon sequencing data
"""

# Include the variant calling rules
include: "variant_calling.smk"

# Direct amplicon fitness calculation (moved from dms_analysis.smk)
rule calculate_fitness:
    input:
        input_csvs=lambda wildcards: [f"{RESULTS_DIR}/variants/{sample}_variants_counts.csv" 
                                     for sample in INPUT_SAMPLES],
        output_csvs=lambda wildcards: [f"{RESULTS_DIR}/variants/{sample}_variants_counts.csv" 
                                      for sample in OUTPUT_SAMPLES]
    output:
        fitness=f"{RESULTS_DIR}/dms/fitness_scores.csv",
        summary=f"{RESULTS_DIR}/dms/analysis_summary.txt"
    params:
        min_input_coverage=config.get("dms", {}).get("min_input_coverage", 10),
        debug_info=lambda wildcards: f"INPUT_SAMPLES: {INPUT_SAMPLES}, OUTPUT_SAMPLES: {OUTPUT_SAMPLES}"
    log:
        "logs/dms/fitness_calculation.log"
    script:
        "../scripts/fitness_calculator.py"

# Direct amplicon variant annotation
rule annotate_variants:
    input:
        fitness=f"{RESULTS_DIR}/dms/fitness_scores.csv",
        reference=lambda wildcards: config.get("reference_genome", "resources/reference.fasta")
    output:
        annotated=f"{RESULTS_DIR}/dms/annotated_variants.csv"
    script:
        "../scripts/variant_annotation.py"
