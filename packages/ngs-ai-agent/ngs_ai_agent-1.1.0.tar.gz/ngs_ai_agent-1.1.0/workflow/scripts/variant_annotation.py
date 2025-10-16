#!/usr/bin/env python3
"""
Annotate variants with additional information
"""

import pandas as pd
import logging
from pathlib import Path
from Bio import SeqIO

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def annotate_variants_with_reference(fitness_df, reference_file):
    """
    Annotate variants with reference sequence information
    
    Args:
        fitness_df: DataFrame with fitness scores
        reference_file: Reference genome FASTA file
        
    Returns:
        DataFrame with additional annotations
    """
    
    # Load reference sequence
    ref_record = next(SeqIO.parse(reference_file, "fasta"))
    ref_seq = str(ref_record.seq)
    
    logger.info(f"Loaded reference sequence: {len(ref_seq)} bp")
    
    # Add annotations
    annotated_variants = []
    
    for _, row in fitness_df.iterrows():
        mutation = row['mutation']
        
        # Parse mutation information
        annotation = parse_mutation_annotation(mutation, ref_seq)
        
        # Combine with fitness data
        annotated_row = row.to_dict()
        annotated_row.update(annotation)
        
        annotated_variants.append(annotated_row)
    
    annotated_df = pd.DataFrame(annotated_variants)
    
    logger.info(f"Annotated {len(annotated_df)} variants")
    
    return annotated_df

def parse_mutation_annotation(mutation, ref_seq):
    """
    Parse mutation string and add detailed annotations
    
    Args:
        mutation: Mutation string (e.g., "T32Y", "WT", "DEL75")
        ref_seq: Reference sequence
        
    Returns:
        Dictionary with annotation information
    """
    
    annotation = {
        'mutation_class': 'unknown',
        'position': None,
        'reference_aa': None,
        'variant_aa': None,
        'codon_position': None,
        'is_synonymous': False,
        'is_nonsense': False,
        'is_indel': False
    }
    
    if mutation == 'WT':
        annotation['mutation_class'] = 'wildtype'
        return annotation
    
    if mutation == 'UNMAPPED':
        annotation['mutation_class'] = 'unmapped'
        return annotation
    
    # Handle multiple mutations
    if '_' in mutation:
        annotation['mutation_class'] = 'multiple'
        # For multiple mutations, just take the first one for position info
        first_mutation = mutation.split('_')[0]
        sub_annotation = parse_mutation_annotation(first_mutation, ref_seq)
        annotation.update({k: v for k, v in sub_annotation.items() if k != 'mutation_class'})
        return annotation
    
    # Handle deletions
    if 'DEL' in mutation:
        annotation['mutation_class'] = 'deletion'
        annotation['is_indel'] = True
        # Try to extract position
        try:
            pos_str = mutation.replace('DEL', '')
            if pos_str.isdigit():
                annotation['position'] = int(pos_str)
                annotation['codon_position'] = (int(pos_str) - 1) * 3
        except:
            pass
        return annotation
    
    # Handle insertions
    if 'INS' in mutation:
        annotation['mutation_class'] = 'insertion'
        annotation['is_indel'] = True
        # Try to extract position
        try:
            pos_str = mutation.replace('INS', '')
            if pos_str.isdigit():
                annotation['position'] = int(pos_str)
                annotation['codon_position'] = (int(pos_str) - 1) * 3
        except:
            pass
        return annotation
    
    # Handle point mutations (e.g., T32Y)
    if len(mutation) >= 3:
        try:
            ref_aa = mutation[0]
            var_aa = mutation[-1]
            pos_str = mutation[1:-1]
            
            if pos_str.isdigit():
                position = int(pos_str)
                annotation['position'] = position
                annotation['reference_aa'] = ref_aa
                annotation['variant_aa'] = var_aa
                annotation['codon_position'] = (position - 1) * 3
                
                # Classify mutation type
                if var_aa == '*':
                    annotation['mutation_class'] = 'nonsense'
                    annotation['is_nonsense'] = True
                elif ref_aa == var_aa:
                    annotation['mutation_class'] = 'synonymous'
                    annotation['is_synonymous'] = True
                else:
                    annotation['mutation_class'] = 'missense'
        except:
            # If parsing fails, mark as unknown
            annotation['mutation_class'] = 'unknown'
    
    return annotation

def add_structural_annotations(annotated_df, reference_file):
    """
    Add structural/functional annotations if available
    """
    
    # This could be expanded to include:
    # - Secondary structure predictions
    # - Domain annotations
    # - Conservation scores
    # - Known functional sites
    
    # For now, just add basic position-based annotations
    if 'position' in annotated_df.columns:
        # Add position-based categories
        annotated_df['position_category'] = annotated_df['position'].apply(
            lambda x: 'N-terminal' if pd.notna(x) and x <= 50 
                     else 'C-terminal' if pd.notna(x) and x >= 200
                     else 'central' if pd.notna(x)
                     else 'unknown'
        )
    
    return annotated_df

if __name__ == "__main__":
    # Get parameters from Snakemake
    fitness_file = snakemake.input.fitness
    reference_file = snakemake.input.reference
    output_file = snakemake.output.annotated
    
    # Create output directory
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Load fitness data
    logger.info(f"Loading fitness data from {fitness_file}")
    fitness_df = pd.read_csv(fitness_file)
    
    # Annotate variants
    logger.info("Annotating variants...")
    annotated_df = annotate_variants_with_reference(fitness_df, reference_file)
    
    # Add structural annotations
    logger.info("Adding structural annotations...")
    annotated_df = add_structural_annotations(annotated_df, reference_file)
    
    # Save annotated variants
    annotated_df.to_csv(output_file, index=False)
    logger.info(f"Annotated variants saved to {output_file}")
    
    # Log summary
    mutation_classes = annotated_df['mutation_class'].value_counts()
    logger.info("Mutation class distribution:")
    for mut_class, count in mutation_classes.items():
        logger.info(f"  - {mut_class}: {count}")
    
    logger.info("Variant annotation complete!")