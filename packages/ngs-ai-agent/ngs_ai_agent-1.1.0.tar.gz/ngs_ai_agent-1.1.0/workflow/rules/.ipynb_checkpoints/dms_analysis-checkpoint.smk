"""
Deep Mutational Scanning Analysis Rules
"""

rule calculate_fitness:
    input:
        input_csvs=lambda wildcards: [f"{RESULTS_DIR}/variants/{sample}_variants_counts.csv" for sample in SAMPLES.keys() if "input" in sample],
        output_csvs=lambda wildcards: [f"{RESULTS_DIR}/variants/{sample}_variants_counts.csv" for sample in SAMPLES.keys() if "output" in sample]
    output:
        fitness=f"{RESULTS_DIR}/dms/fitness_scores.csv",
        summary=f"{RESULTS_DIR}/dms/analysis_summary.txt"
    params:
        min_input_coverage=config["variant_calling"]["min_coverage"],
        debug_info=lambda wildcards: f"SAMPLES: {list(SAMPLES.keys())}, Input: {[s for s in SAMPLES.keys() if 'input' in s]}, Output: {[s for s in SAMPLES.keys() if 'output' in s]}"
    log:
        "logs/dms/fitness_calculation.log"
    script:
        "../scripts/fitness_calculator.py"

rule annotate_variants:
    input:
        fitness=f"{RESULTS_DIR}/dms/fitness_scores.csv",
        reference=lambda wildcards: config.get("reference_genome", "resources/reference.fasta")
    output:
        annotated=f"{RESULTS_DIR}/dms/annotated_fitness.csv"
    script:
        "../scripts/variant_annotation.py"
