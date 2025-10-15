#!/usr/bin/env python3
"""
Deep Mutational Scanning Fitness Calculation
Calculate fitness scores from variant frequency data
"""

import pandas as pd
import numpy as np
import vcf
from Bio import SeqIO
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DMSFitnessCalculator:
    """Calculate fitness scores for Deep Mutational Scanning"""
    
    def __init__(self, method="enrichment_ratio", pseudocount=1):
        self.method = method
        self.pseudocount = pseudocount
        self.genetic_code = {
            'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
            'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
            'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
            'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
            'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
            'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
            'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
            'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
            'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
            'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
            'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
            'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
            'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
            'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
            'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
            'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G'
        }
    
    def calculate_fitness(self, vcf_file, reference_file, output_csv, summary_file):
        """
        Calculate fitness scores from VCF file
        
        Args:
            vcf_file: Input VCF file with variants
            reference_file: Reference sequence file
            output_csv: Output CSV file with fitness scores
            summary_file: Summary statistics file
        """
        logger.info("Calculating fitness scores...")
        
        # Load reference sequence
        reference_seq = self._load_reference(reference_file)
        
        # Parse variants from VCF
        variants = self._parse_vcf(vcf_file)
        
        # Group variants by sample/timepoint if available
        variant_groups = self._group_variants(variants)
        
        # Calculate fitness scores
        fitness_data = self._calculate_fitness_scores(variant_groups, reference_seq)
        
        # Save results
        fitness_df = pd.DataFrame(fitness_data)
        fitness_df.to_csv(output_csv, index=False)
        
        # Generate summary
        self._generate_summary(fitness_df, summary_file)
        
        logger.info(f"Fitness calculation completed. Output: {output_csv}")
    
    def _load_reference(self, reference_file):
        """Load reference sequence"""
        try:
            record = next(SeqIO.parse(reference_file, "fasta"))
            return str(record.seq).upper()
        except Exception as e:
            logger.error(f"Error loading reference: {e}")
            raise
    
    def _parse_vcf(self, vcf_file):
        """Parse variants from VCF file"""
        variants = []
        
        try:
            vcf_reader = vcf.Reader(open(vcf_file, 'r'))
            
            for record in vcf_reader:
                variant = {
                    'chromosome': record.CHROM,
                    'position': record.POS,
                    'ref': record.REF,
                    'alt': str(record.ALT[0]),
                    'frequency': float(record.INFO.get('AF', [0])[0]) if 'AF' in record.INFO else 0,
                    'coverage': int(record.INFO.get('DP', 0)) if 'DP' in record.INFO else 0,
                    'alt_count': int(record.INFO.get('AC', [0])[0]) if 'AC' in record.INFO else 0
                }
                variants.append(variant)
                
        except Exception as e:
            logger.error(f"Error parsing VCF: {e}")
            # Fallback: try to parse as simple format
            variants = self._parse_simple_vcf(vcf_file)
        
        return variants
    
    def _parse_simple_vcf(self, vcf_file):
        """Fallback parser for simple VCF format"""
        variants = []
        
        with open(vcf_file, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                
                fields = line.strip().split('\t')
                if len(fields) >= 8:
                    # Parse INFO field
                    info_dict = {}
                    for info_item in fields[7].split(';'):
                        if '=' in info_item:
                            key, value = info_item.split('=', 1)
                            info_dict[key] = value
                    
                    variant = {
                        'chromosome': fields[0],
                        'position': int(fields[1]),
                        'ref': fields[3],
                        'alt': fields[4],
                        'frequency': float(info_dict.get('AF', 0)),
                        'coverage': int(info_dict.get('DP', 0)),
                        'alt_count': int(info_dict.get('AC', 0))
                    }
                    variants.append(variant)
        
        return variants
    
    def _group_variants(self, variants):
        """Group variants by sample/timepoint for fitness calculation"""
        # For now, treat all variants as one group
        # In future versions, this could group by sample metadata
        return {'all_samples': variants}
    
    def _calculate_fitness_scores(self, variant_groups, reference_seq):
        """Calculate fitness scores for each variant"""
        fitness_data = []
        
        for group_name, variants in variant_groups.items():
            for variant in variants:
                # Calculate amino acid change
                aa_change = self._get_amino_acid_change(
                    variant['position'], 
                    variant['ref'], 
                    variant['alt'], 
                    reference_seq
                )
                
                # Calculate fitness score
                if self.method == "enrichment_ratio":
                    fitness_score = self._calculate_enrichment_ratio(variant)
                elif self.method == "frequency_based":
                    fitness_score = self._calculate_frequency_fitness(variant)
                else:
                    fitness_score = 0.0
                
                fitness_data.append({
                    'chromosome': variant['chromosome'],
                    'position': variant['position'],
                    'ref_nucleotide': variant['ref'],
                    'alt_nucleotide': variant['alt'],
                    'ref_amino_acid': aa_change['ref_aa'],
                    'alt_amino_acid': aa_change['alt_aa'],
                    'amino_acid_position': aa_change['aa_pos'],
                    'mutation_type': aa_change['type'],
                    'frequency': variant['frequency'],
                    'coverage': variant['coverage'],
                    'alt_count': variant['alt_count'],
                    'fitness_score': fitness_score,
                    'group': group_name
                })
        
        return fitness_data
    
    def _get_amino_acid_change(self, position, ref_nt, alt_nt, reference_seq):
        """Determine amino acid change from nucleotide mutation"""
        # Convert to 0-based position
        pos_0based = position - 1
        
        # Determine codon position
        codon_start = (pos_0based // 3) * 3
        codon_pos = pos_0based % 3
        aa_position = (pos_0based // 3) + 1
        
        # Get reference codon
        if codon_start + 2 < len(reference_seq):
            ref_codon = reference_seq[codon_start:codon_start + 3]
            
            # Create mutated codon
            alt_codon = list(ref_codon)
            alt_codon[codon_pos] = alt_nt
            alt_codon = ''.join(alt_codon)
            
            # Translate codons
            ref_aa = self.genetic_code.get(ref_codon, 'X')
            alt_aa = self.genetic_code.get(alt_codon, 'X')
            
            # Determine mutation type
            if ref_aa == alt_aa:
                mut_type = 'synonymous'
            elif alt_aa == '*':
                mut_type = 'nonsense'
            else:
                mut_type = 'missense'
        else:
            ref_aa = alt_aa = 'X'
            mut_type = 'unknown'
        
        return {
            'ref_aa': ref_aa,
            'alt_aa': alt_aa,
            'aa_pos': aa_position,
            'type': mut_type
        }
    
    def _calculate_enrichment_ratio(self, variant):
        """Calculate enrichment ratio as fitness score"""
        # Simple frequency-based fitness (can be enhanced with time-series data)
        frequency = variant['frequency']
        
        # Log-transform with pseudocount
        fitness = np.log2((frequency * 100 + self.pseudocount) / (1 + self.pseudocount))
        
        return fitness
    
    def _calculate_frequency_fitness(self, variant):
        """Calculate frequency-based fitness score"""
        return variant['frequency']
    
    def _generate_summary(self, fitness_df, summary_file):
        """Generate summary statistics"""
        summary = {
            'total_variants': len(fitness_df),
            'synonymous_variants': len(fitness_df[fitness_df['mutation_type'] == 'synonymous']),
            'missense_variants': len(fitness_df[fitness_df['mutation_type'] == 'missense']),
            'nonsense_variants': len(fitness_df[fitness_df['mutation_type'] == 'nonsense']),
            'mean_fitness': fitness_df['fitness_score'].mean(),
            'std_fitness': fitness_df['fitness_score'].std(),
            'min_fitness': fitness_df['fitness_score'].min(),
            'max_fitness': fitness_df['fitness_score'].max()
        }
        
        with open(summary_file, 'w') as f:
            f.write("Deep Mutational Scanning Analysis Summary\n")
            f.write("=" * 40 + "\n\n")
            for key, value in summary.items():
                f.write(f"{key.replace('_', ' ').title()}: {value}\n")


def main():
    """Main function for Snakemake script execution"""
    # Snakemake variables
    vcf_file = snakemake.input.variants
    reference_file = snakemake.input.reference
    output_csv = snakemake.output.fitness
    summary_file = snakemake.output.summary
    
    # Parameters
    method = snakemake.params.method
    pseudocount = snakemake.params.pseudocount
    
    # Create fitness calculator
    calculator = DMSFitnessCalculator(method=method, pseudocount=pseudocount)
    
    # Calculate fitness
    calculator.calculate_fitness(vcf_file, reference_file, output_csv, summary_file)


if __name__ == "__main__":
    main()
