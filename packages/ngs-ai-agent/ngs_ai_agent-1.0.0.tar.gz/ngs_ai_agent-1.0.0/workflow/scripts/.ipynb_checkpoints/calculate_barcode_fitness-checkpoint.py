#!/usr/bin/env python3
"""
Calculate fitness scores from barcode count data
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import os
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_barcode_counts(count_files):
    """
    Load barcode count data from multiple files
    
    Args:
        count_files: List of CSV files with barcode counts
        
    Returns:
        Dictionary mapping sample name to count data
    """
    
    count_data = {}
    
    for count_file in count_files:
        sample_name = Path(count_file).stem.replace('_barcode_counts', '')
        logger.info(f"Loading counts from {count_file} (sample: {sample_name})")
        
        # Load the variant counts (aggregated by mutation)
        df = pd.read_csv(count_file)
        count_data[sample_name] = df
        
        logger.info(f"  - {len(df)} variants, {df['count'].sum():,} total reads")
    
    return count_data

def calculate_fitness_from_barcode_data(input_data, output_data, barcode_map_file, 
                                       min_input_coverage=10, pseudocount=1):
    """
    Calculate fitness scores using barcode count data
    
    Args:
        input_data: Dictionary of input sample count data
        output_data: Dictionary of output sample count data  
        barcode_map_file: Barcode mapping file
        min_input_coverage: Minimum coverage in input samples
        pseudocount: Pseudocount for fitness calculation
        
    Returns:
        DataFrame with fitness scores
    """
    
    # Load barcode mapping for reference
    barcode_mapping = pd.read_csv(barcode_map_file)
    all_mutations = set(barcode_mapping['mutation'].unique())
    
    # Combine all input and output data
    logger.info("Combining count data...")
    all_input_counts = {}
    all_output_counts = {}
    
    # Aggregate input counts across replicates
    for sample_name, df in input_data.items():
        for _, row in df.iterrows():
            mutation = row['mutation']
            count = row['count']
            if mutation in all_input_counts:
                all_input_counts[mutation] += count
            else:
                all_input_counts[mutation] = count
    
    # Aggregate output counts across replicates
    for sample_name, df in output_data.items():
        for _, row in df.iterrows():
            mutation = row['mutation']
            count = row['count']
            if mutation in all_output_counts:
                all_output_counts[mutation] += count
            else:
                all_output_counts[mutation] = count
    
    # Calculate fitness scores
    logger.info("Calculating fitness scores...")
    fitness_results = []
    
    # Get WT frequencies for normalization
    wt_input_count = all_input_counts.get('WT', 0)
    wt_output_count = all_output_counts.get('WT', 0)
    
    total_input = sum(all_input_counts.values())
    total_output = sum(all_output_counts.values())
    
    if wt_input_count == 0 or wt_output_count == 0:
        logger.warning("No WT found, using pseudocount for normalization")
        wt_input_freq = pseudocount / total_input
        wt_output_freq = pseudocount / total_output
    else:
        wt_input_freq = wt_input_count / total_input
        wt_output_freq = wt_output_count / total_output
    
    wt_fitness = np.log(wt_output_freq / wt_input_freq)
    
    # Calculate fitness for each mutation (aggregated across replicates)
    for mutation in all_mutations:
        input_count = all_input_counts.get(mutation, 0)
        output_count = all_output_counts.get(mutation, 0)
        
        # Apply minimum coverage filter
        if input_count < min_input_coverage:
            continue
        
        # Calculate frequencies
        input_freq = input_count / total_input
        output_freq = max(output_count, pseudocount) / total_output  # Use pseudocount if 0
        
        # Calculate fitness: w_i = log(f_i^out / f_i^in) - log(f_WT^out / f_WT^in)
        raw_fitness = np.log(output_freq / input_freq)
        normalized_fitness = raw_fitness - wt_fitness
        
        # Classify mutation type
        mutation_type = classify_mutation_type(mutation)
        
        fitness_results.append({
            'mutation': mutation,
            'input_count': input_count,
            'output_count': output_count,
            'input_frequency': input_freq,
            'output_frequency': output_freq,
            'raw_fitness': raw_fitness,
            'fitness': normalized_fitness,
            'mutation_type': mutation_type
        })
    
    fitness_df = pd.DataFrame(fitness_results)
    fitness_df = fitness_df.sort_values('fitness', ascending=False)
    
    logger.info(f"Calculated fitness for {len(fitness_df)} mutations")
    
    # Augment for heatmap compatibility
    # - Parse mutation strings like "T32Y" (or multi: "T32Y_L45P")
    # - Create columns: alt_amino_acid, amino_acid_position, fitness_score
    # - Explode multi-mutation rows into multiple rows (one per AA change)
    pattern = re.compile(r"^([A-Z\*])(\d+)([A-Z\*])$")
    expanded_rows = []
    for _, row in fitness_df.iterrows():
        mutation = row['mutation']
        if mutation in ('WT', 'UNMAPPED'):
            # Skip WT/unmapped for heatmap matrix
            continue
        parts = str(mutation).split('_')
        for part in parts:
            m = pattern.match(part.strip())
            if not m:
                # Skip if not a simple AA substitution (e.g., DEL/INS)
                continue
            ref_aa, pos_str, alt_aa = m.groups()
            try:
                pos = int(pos_str)
            except ValueError:
                continue
            expanded = dict(row)
            expanded['ref_amino_acid'] = ref_aa
            expanded['alt_amino_acid'] = alt_aa
            expanded['amino_acid_position'] = pos
            expanded['fitness_score'] = row['fitness']
            # Ensure generic 'type' column for AI analysis
            expanded['type'] = row.get('mutation_type', classify_mutation_type(row['mutation']))
            expanded_rows.append(expanded)
    
    if expanded_rows:
        fitness_df_expanded = pd.DataFrame(expanded_rows)
        logger.info(f"Expanded fitness data for heatmap: {len(fitness_df_expanded)} rows")
        # Attach per-replicate fitness (computed below) later in main flow
        fitness_df_expanded.attrs['aggregated_fitness'] = fitness_df  # keep original in attrs
        return fitness_df_expanded
    else:
        # Fallback: add empty columns so downstream script fails gracefully if no data
        fitness_df['alt_amino_acid'] = np.nan
        fitness_df['amino_acid_position'] = np.nan
        fitness_df['fitness_score'] = fitness_df['fitness']
        fitness_df['type'] = fitness_df.get('mutation_type', np.nan)
        return fitness_df

def compute_per_output_replicate_fitness(input_data, output_data, barcode_map_file,
                                         min_input_coverage=10, pseudocount=1):
    """Compute fitness per output replicate using pooled input as reference.
    Returns: dict of sample_name -> DataFrame(columns: mutation, fitness)
    """
    # Pooled input counts
    pooled_input = {}
    for sample_name, df in input_data.items():
        for _, row in df.iterrows():
            pooled_input[row['mutation']] = pooled_input.get(row['mutation'], 0) + row['count']
    total_input = sum(pooled_input.values()) or 1
    wt_input = pooled_input.get('WT', 0)
    wt_input_freq = (pseudocount / total_input) if wt_input == 0 else (wt_input / total_input)

    per_rep_fitness = {}
    for out_sample, df_out in output_data.items():
        out_counts = {}
        for _, row in df_out.iterrows():
            out_counts[row['mutation']] = out_counts.get(row['mutation'], 0) + row['count']
        total_out = sum(out_counts.values()) or 1
        wt_out = out_counts.get('WT', 0)
        wt_out_freq = (pseudocount / total_out) if wt_out == 0 else (wt_out / total_out)
        wt_fitness = np.log(wt_out_freq / wt_input_freq)

        rows = []
        # Use union of mutations observed in mapping to ensure consistency
        for mutation in set(list(pooled_input.keys()) + list(out_counts.keys())):
            in_count = pooled_input.get(mutation, 0)
            if in_count < min_input_coverage:
                continue
            out_count = out_counts.get(mutation, 0)
            in_freq = in_count / total_input
            out_freq = max(out_count, pseudocount) / total_out
            raw_fitness = np.log(out_freq / in_freq)
            norm_fitness = raw_fitness - wt_fitness
            rows.append({'mutation': mutation, 'fitness': norm_fitness})
        per_rep_fitness[out_sample] = pd.DataFrame(rows)
    return per_rep_fitness

def classify_mutation_type(mutation):
    """Classify mutation type based on mutation string"""
    
    if mutation == 'WT':
        return 'wildtype'
    elif mutation == 'UNMAPPED':
        return 'unmapped'
    elif '_' in mutation:
        return 'multiple'
    elif mutation.endswith('*'):
        return 'nonsense'
    elif len(mutation) >= 3 and mutation[0] == mutation[-1]:
        return 'synonymous'
    elif 'DEL' in mutation:
        return 'deletion'
    elif 'INS' in mutation:
        return 'insertion'
    else:
        return 'missense'

def parse_mutation_string(mutation_string):
    """
    Parse mutation string to extract reference AA, alternative AA, and position
    Matches the logic from amplicon fitness_calculator.py
    """
    import re
    
    # Pattern for deletions: DEL + number (e.g., DEL75)
    deletion_match = re.match(r'DEL(\d+)', mutation_string)
    if deletion_match:
        position = int(deletion_match.group(1))
        ref_aa = 'X'  # Unknown reference for deletion
        alt_aa = 'DEL'  # Deletion indicator
        return ref_aa, alt_aa, position
    
    # Pattern for insertions: INS + number (e.g., INS75)
    insertion_match = re.match(r'INS(\d+)', mutation_string)
    if insertion_match:
        position = int(insertion_match.group(1))
        ref_aa = 'X'  # Unknown reference for insertion
        alt_aa = 'INS'  # Insertion indicator
        return ref_aa, alt_aa, position
    
    # Pattern for synonymous mutations: single letter + number + = (e.g., R61=)
    synonymous_match = re.match(r'([A-Z])(\d+)=', mutation_string)
    if synonymous_match:
        ref_aa = synonymous_match.group(1)
        position = int(synonymous_match.group(2))
        alt_aa = ref_aa  # Same as reference for synonymous
        return ref_aa, alt_aa, position
    
    # Pattern for missense mutations: single letter + number + single letter (e.g., T32Y)
    missense_match = re.match(r'([A-Z])(\d+)([A-Z])', mutation_string)
    if missense_match:
        ref_aa = missense_match.group(1)
        position = int(missense_match.group(2))
        alt_aa = missense_match.group(3)
        return ref_aa, alt_aa, position
    
    # Pattern for stop codons: single letter + number + * (e.g., Q45*)
    stop_match = re.match(r'([A-Z])(\d+)\*', mutation_string)
    if stop_match:
        ref_aa = stop_match.group(1)
        position = int(stop_match.group(2))
        alt_aa = '*'
        return ref_aa, alt_aa, position
    
    # If pattern doesn't match, return defaults
    logger.warning(f"Could not parse mutation string: {mutation_string}")
    return 'X', 'X', 0

def generate_analysis_summary(fitness_df, input_data, output_data):
    """Generate analysis summary statistics"""
    
    summary_lines = []
    summary_lines.append("=== Barcode-coupled DMS Analysis Summary ===")
    summary_lines.append("")
    
    # Input/Output sample info
    summary_lines.append("Input samples:")
    for sample_name, df in input_data.items():
        total_reads = df['count'].sum()
        unique_variants = len(df)
        summary_lines.append(f"  - {sample_name}: {total_reads:,} reads, {unique_variants} variants")
    
    summary_lines.append("")
    summary_lines.append("Output samples:")
    for sample_name, df in output_data.items():
        total_reads = df['count'].sum()
        unique_variants = len(df)
        summary_lines.append(f"  - {sample_name}: {total_reads:,} reads, {unique_variants} variants")
    
    summary_lines.append("")
    
    # Fitness statistics
    summary_lines.append("Fitness Analysis:")
    summary_lines.append(f"  - Total variants analyzed: {len(fitness_df)}")
    # Use fitness_score column (amplicon format) or fitness column (original format)
    fitness_col = 'fitness_score' if 'fitness_score' in fitness_df.columns else 'fitness'
    summary_lines.append(f"  - Mean fitness: {fitness_df[fitness_col].mean():.3f}")
    summary_lines.append(f"  - Std fitness: {fitness_df[fitness_col].std():.3f}")
    summary_lines.append(f"  - Min fitness: {fitness_df[fitness_col].min():.3f}")
    summary_lines.append(f"  - Max fitness: {fitness_df[fitness_col].max():.3f}")
    
    # Mutation type breakdown
    summary_lines.append("")
    summary_lines.append("Mutation types:")
    # Use 'type' column (amplicon format) or 'mutation_type' column (original format)
    type_col = 'type' if 'type' in fitness_df.columns else 'mutation_type'
    type_counts = fitness_df[type_col].value_counts()
    for mut_type, count in type_counts.items():
        summary_lines.append(f"  - {mut_type}: {count}")

    # Per-replicate correlation (if available)
    try:
        summary_lines.append("")
        summary_lines.append("Per-output replicate fitness correlations (Pearson/Spearman):")
        # Reconstruct aggregated fitness (if passed via attrs) for filtering
        if hasattr(fitness_df, 'attrs') and 'aggregated_fitness' in fitness_df.attrs:
            aggregated = fitness_df.attrs['aggregated_fitness']
        else:
            aggregated = fitness_df
        # Compute per-replicate fitness
        per_rep = compute_per_output_replicate_fitness(input_data, output_data, None,
                                                       min_input_coverage=1, pseudocount=1)
        sample_names = list(per_rep.keys())
        # Build aligned matrix by mutation intersection
        for i in range(len(sample_names)):
            for j in range(i+1, len(sample_names)):
                s1, s2 = sample_names[i], sample_names[j]
                df1, df2 = per_rep[s1], per_rep[s2]
                merged = pd.merge(df1, df2, on='mutation', suffixes=(f'_{s1}', f'_{s2}'))
                if len(merged) >= 3:
                    pear = merged[f'fitness_{s1}'].corr(merged[f'fitness_{s2}'], method='pearson')
                    spear = merged[f'fitness_{s1}'].corr(merged[f'fitness_{s2}'], method='spearman')
                    summary_lines.append(f"  - {s1} vs {s2}: Pearson={pear:.3f}, Spearman={spear:.3f} (n={len(merged)})")
                else:
                    summary_lines.append(f"  - {s1} vs {s2}: insufficient overlap (n={len(merged)})")
    except Exception as e:
        summary_lines.append(f"Correlation calculation failed: {e}")
    
    return "\n".join(summary_lines)

if __name__ == "__main__":
    # Get parameters from Snakemake
    input_files = snakemake.input.input_counts
    output_files = snakemake.input.output_counts
    barcode_map_file = snakemake.input.barcode_map
    
    fitness_output = snakemake.output.fitness_scores
    summary_output = snakemake.output.analysis_summary
    
    min_input_coverage = snakemake.params.min_input_coverage
    pseudocount = snakemake.params.pseudocount
    
    # Create output directories
    Path(fitness_output).parent.mkdir(parents=True, exist_ok=True)
    Path(summary_output).parent.mkdir(parents=True, exist_ok=True)
    
    # Load count data
    logger.info("Loading input count data...")
    input_data = load_barcode_counts(input_files)
    
    logger.info("Loading output count data...")
    output_data = load_barcode_counts(output_files)
    
    # Calculate fitness
    logger.info("Calculating fitness scores...")
    fitness_df = calculate_fitness_from_barcode_data(
        input_data, output_data, barcode_map_file,
        min_input_coverage, pseudocount
    )
    
    # Create amplicon-compatible format with per-repeat fitness
    logger.info("Creating amplicon-compatible fitness output...")
    
    # Get per-repeat fitness data
    per_rep_fitness = compute_per_output_replicate_fitness(
        input_data, output_data, barcode_map_file, min_input_coverage, pseudocount
    )
    
    # Create mutation mapping for per-repeat data
    mutation_to_repeats = {}
    for sample_name, df in per_rep_fitness.items():
        for _, row in df.iterrows():
            mutation = row['mutation']
            if mutation not in mutation_to_repeats:
                mutation_to_repeats[mutation] = {}
            mutation_to_repeats[mutation][sample_name] = row['fitness']
    
    # Create amplicon-compatible fitness DataFrame
    amplicon_fitness_results = []
    
    for _, row in fitness_df.iterrows():
        mutation = row['mutation']
        
        # Parse mutation string for amino acid information
        ref_aa, alt_aa, position = parse_mutation_string(mutation)
        
        # Determine mutation type
        mutation_type = classify_mutation_type(mutation)
        
        # Create base row
        fitness_row = {
            'mutation': mutation,
            'fitness_score': row['fitness'],
            'type': mutation_type,
            'ref_amino_acid': ref_aa,
            'alt_amino_acid': alt_aa,
            'amino_acid_position': position,
            'input_count': row['input_count'],
            'output_count': row['output_count'],
            'input_frequency': row['input_frequency'],
            'output_frequency': row['output_frequency'],
            'raw_fitness': row['raw_fitness']
        }
        
        # Add per-repeat fitness columns
        for sample_name in per_rep_fitness.keys():
            col_name = f"{sample_name}_fitness"
            if mutation in mutation_to_repeats and sample_name in mutation_to_repeats[mutation]:
                fitness_row[col_name] = mutation_to_repeats[mutation][sample_name]
            else:
                fitness_row[col_name] = np.nan
        
        amplicon_fitness_results.append(fitness_row)
    
    # Create DataFrame and sort by fitness
    amplicon_fitness_df = pd.DataFrame(amplicon_fitness_results)
    amplicon_fitness_df = amplicon_fitness_df.sort_values('fitness_score', ascending=False)
    
    # Save main fitness scores (amplicon-compatible format)
    amplicon_fitness_df.to_csv(fitness_output, index=False)
    logger.info(f"Amplicon-compatible fitness scores saved to {fitness_output}")
    
    # Create annotated_fitness.csv (same as fitness_scores.csv for barcode DMS)
    annotated_output = fitness_output.replace('fitness_scores.csv', 'annotated_fitness.csv')
    amplicon_fitness_df.to_csv(annotated_output, index=False)
    logger.info(f"Annotated fitness scores saved to {annotated_output}")
    
    # Generate and save summary
    summary = generate_analysis_summary(amplicon_fitness_df, input_data, output_data)
    with open(summary_output, 'w') as f:
        f.write(summary)
    logger.info(f"Analysis summary saved to {summary_output}")
    
    logger.info("Barcode fitness calculation complete!")
