"""
Barcode-coupled Deep Mutational Scanning Rules
Handles barcode→variant mapping and barcode-based fitness calculation
"""

# Note: extract_barcodes rule removed - now using alignment-based approach

# Rule for preparing reference for Minimap2 barcode mapping
rule prepare_minimap2_reference:
    input:
        reference=lambda wildcards: config.get("barcode_dms", {}).get("barcode_reference", config["reference_genome"])
    output:
        cleaned_ref="resources/barcode_reference_cleaned.fasta"
    threads: config["pipeline"]["threads"]
    shell:
        """
        # Clean the reference file to ensure it's in proper FASTA format
        python -c "
import sys
from Bio import SeqIO
from pathlib import Path

ref_file = '{input.reference}'
output_file = '{output.cleaned_ref}'

print(f'Cleaning reference file: {{ref_file}}')
print(f'Output file: {{output_file}}')

# Try to read and clean the reference
try:
    # First try standard formats
    records = list(SeqIO.parse(ref_file, 'fasta'))
    if not records:
        # Try GenBank format
        records = list(SeqIO.parse(ref_file, 'genbank'))
    if not records:
        # Try fasta-pearson format (with comments)
        records = list(SeqIO.parse(ref_file, 'fasta-pearson'))
    
    if records:
        # Write clean FASTA
        SeqIO.write(records, output_file, 'fasta')
        print(f'Successfully cleaned reference: {{len(records)}} sequences')
    else:
        print('Error: No sequences found in reference file')
        sys.exit(1)
        
except Exception as e:
    print(f'Error processing reference: {{e}}')
    sys.exit(1)
"
        """

# Rule for aligning long-read data to reference using Minimap2
rule align_mapping_reads:
    input:
        reads=f"{RESULTS_DIR}/trimmed/{{sample}}_trimmed.fastq.gz",
        reference="resources/barcode_reference_cleaned.fasta"
    output:
        bam=f"{RESULTS_DIR}/barcode_mapping/{{sample}}_aligned.bam",
        bai=f"{RESULTS_DIR}/barcode_mapping/{{sample}}_aligned.bam.bai"
    params:
        # Minimap2 parameters from config
        preset=config.get("barcode_dms", {}).get("minimap2_preset", "map-pb"),
        secondary=config.get("barcode_dms", {}).get("minimap2_secondary", False),
        sam_hit_only=config.get("barcode_dms", {}).get("minimap2_sam_hit_only", True)
    threads: config["pipeline"]["threads"]
    shell:
        """
        # Align reads using Minimap2
        # Build minimap2 command with conditional secondary parameter
        if [ "{params.secondary}" = "True" ]; then
            minimap2 -ax {params.preset} \
                --secondary=yes \
                --sam-hit-only \
                -t {threads} \
                "{input.reference}" \
                "{input.reads}" \
            | samtools view -bS - | \
            samtools sort - -o "{output.bam}"
        else
            minimap2 -ax {params.preset} \
                --secondary=no \
                --sam-hit-only \
                -t {threads} \
                "{input.reference}" \
                "{input.reads}" \
            | samtools view -bS - | \
            samtools sort - -o "{output.bam}"
        fi
        samtools index "{output.bam}"
        """

# Rule for building barcode→variant map from aligned reads
rule build_barcode_variant_map:
    input:
        aligned_bams=expand(f"{RESULTS_DIR}/barcode_mapping/{{sample}}_aligned.bam", sample=MAPPING_SAMPLES),
        reference=lambda wildcards: config.get("barcode_dms", {}).get("barcode_reference", config["reference_genome"]),
        cleaned_reference="resources/barcode_reference_cleaned.fasta"  # Ensure reference is prepared first
    output:
        barcode_map=f"{RESULTS_DIR}/barcode_mapping/barcode_variant_map.csv",
        mapping_stats=f"{RESULTS_DIR}/barcode_mapping/mapping_statistics.txt"
    params:
        min_coverage=config.get("barcode_dms", {}).get("min_barcode_coverage", 5),
        barcode_region=config.get("barcode_dms", {}).get("barcode_region", "barcode"),
        gene_region=config.get("barcode_dms", {}).get("gene_region", "gene"),
        max_workers=config.get("barcode_dms", {}).get("max_workers", None)
    threads: config["pipeline"]["threads"]
    script:
        "../scripts/build_barcode_map_from_alignment.py"

# Rule for counting barcodes in short-read data (only for short-read samples, not mapping samples)
rule count_barcodes:
    input:
        reads=f"{RESULTS_DIR}/trimmed/{{sample}}_trimmed.fastq.gz",
        barcode_map=f"{RESULTS_DIR}/barcode_mapping/barcode_variant_map.csv"
    output:
        barcode_counts=f"{RESULTS_DIR}/barcode_counts/{{sample}}_barcode_counts.csv"
    params:
        min_quality=config.get("barcode_dms", {}).get("min_barcode_quality", 20),
        max_workers=config.get("barcode_dms", {}).get("max_workers", None)
    threads: config["pipeline"]["threads"]
    script:
        "../scripts/count_barcodes.py"

# Rule for calculating fitness from barcode counts (V1 - original)
rule calculate_barcode_fitness:
    input:
        input_counts=lambda wildcards: [f"{RESULTS_DIR}/barcode_counts/{sample}_barcode_counts.csv" 
                                       for sample in INPUT_SAMPLES],
        output_counts=lambda wildcards: [f"{RESULTS_DIR}/barcode_counts/{sample}_barcode_counts.csv" 
                                        for sample in OUTPUT_SAMPLES],
        barcode_map=f"{RESULTS_DIR}/barcode_mapping/barcode_variant_map.csv"
    output:
        fitness_scores=f"{RESULTS_DIR}/dms/fitness_scores.csv",
        annotated_fitness=f"{RESULTS_DIR}/dms/annotated_fitness.csv",
        analysis_summary=f"{RESULTS_DIR}/dms/analysis_summary.txt"
    params:
        min_input_coverage=config.get("barcode_dms", {}).get("min_input_coverage", 10),
        pseudocount=config["dms"]["fitness_calculation"]["pseudocount"]
    threads: config["pipeline"]["threads"]
    script:
        "../scripts/calculate_barcode_fitness_v2.py"


# Rule for barcode quality control
rule barcode_qc:
    input:
        barcode_counts=expand(f"{RESULTS_DIR}/barcode_counts/{{sample}}_barcode_counts.csv", 
                             sample=SHORT_READ_SAMPLES.keys()),
        barcode_map=f"{RESULTS_DIR}/barcode_mapping/barcode_variant_map.csv"
    output:
        qc_report=f"{RESULTS_DIR}/qc/barcode_qc_report.html"
    script:
        "../scripts/barcode_qc_report.py"
