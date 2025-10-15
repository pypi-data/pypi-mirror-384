#!/usr/bin/env python3
"""
Fitness Calculator for Deep Mutational Scanning
Implements the fitness equation: w_i = log(f_i^out / f_i^in) - log(f_WT^out / f_WT^in)

Updated to use CSV input files from variant caller V4, which provides mutation counts
and proper mutation type classification (missense, synonymous, deletion, etc.).

Focuses on single mutations only, since true multi-mutation detection requires 
fragment-level analysis that is now properly handled by the variant caller.

Enhanced to calculate fitness for each repeat individually for accurate correlation analysis.
"""

import pandas as pd
import numpy as np
import argparse
import logging
from collections import defaultdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DMSFitnessCalculator:
    """
    Calculate fitness scores for DMS variants - single mutations only
    
    This class implements the fitness calculation using the equation:
    w_i = log(f_i^out / f_i^in) - log(f_WT^out / f_WT^in)
    
    where f_i is the frequency of mutation i in input (in) and output (out) samples.
    
    Note: When mutations are missing from output samples, the calculator uses a count=1 approach
    to estimate frequencies instead of using arbitrary small values. This provides more
    biologically meaningful fitness calculations.
    """
    
    def __init__(self, min_input_coverage=10):
        self.input_samples = []
        self.output_samples = []
        self.wild_type_freqs = {}
        self.min_input_coverage = min_input_coverage
        
    def load_variant_data(self, input_csvs, output_csvs):
        """
        Load variant data from input and output CSV files
        
        Args:
            input_csvs: List of input CSV files (before selection)
            output_csvs: List of output CSV files (after selection)
        """
        logger.info("Loading variant data from CSV files...")
        
        # Load input samples
        for csv_file in input_csvs:
            sample_data = self._parse_csv(csv_file, "input")
            self.input_samples.append(sample_data)
            
        # Load output samples
        for csv_file in output_csvs:
            sample_data = self._parse_csv(csv_file, "output")
            self.output_samples.append(sample_data)
            
        logger.info(f"Loaded {len(self.input_samples)} input samples and {len(self.output_samples)} output samples")
    
    def _parse_csv(self, csv_file, sample_type):
        """Parse CSV file and extract variant information"""
        variants = defaultdict(dict)
        
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded CSV with {len(df)} rows from {csv_file}")
            
            # Check for required columns
            required_columns = ['variant', 'count']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in {csv_file}: {missing_columns}")
                logger.error(f"Available columns: {list(df.columns)}")
                return variants
            
            # Calculate total count for frequency normalization
            total_count = df['count'].sum()
            logger.info(f"Total count in {csv_file}: {total_count:,}")
            
            # Process each variant
            for _, row in df.iterrows():
                mutation = row['variant']
                count = row['count']
                frequency = count / total_count if total_count > 0 else 0
                
                # Only process single mutations (no underscores) and WT
                if '_' not in mutation or mutation == 'WT':
                    variants[mutation] = {
                        'frequency': frequency,
                        'coverage': count,  # Use count as coverage for CSV
                        'count': count,
                        'type': row.get('type', 'unknown')
                    }
                    
                    logger.debug(f"Added variant {mutation}: count={count}, frequency={frequency:.6f}")
                else:
                    logger.debug(f"Skipping multi-mutation {mutation}")
                    
        except Exception as e:
            logger.error(f"Error parsing CSV file {csv_file}: {e}")
            return variants
        
        logger.info(f"Parsed {len(variants)} variants from {csv_file}")
        return variants
    
    def _parse_vcf(self, vcf_file, sample_type):
        """Parse VCF file and extract variant information"""
        variants = defaultdict(dict)
        
        try:
            with open(vcf_file, 'r') as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    
                    parts = line.strip().split('\t')
                    if len(parts) < 8:
                        continue
                    
                    # Parse VCF fields
                    chrom = parts[0]
                    pos = int(parts[1])
                    ref = parts[3]
                    alt = parts[4]
                    info = parts[7]
                    
                    # Parse INFO field
                    info_dict = self._parse_info(info)
                    
                    # Extract mutation annotation
                    mutation = info_dict.get('MUT', 'UNKNOWN')
                    frequency = float(info_dict.get('AF', 0))  # AF is already normalized!
                    coverage = int(info_dict.get('DP', 0))
                    
                    if mutation != 'UNKNOWN' and mutation != 'ERROR':
                        # Only process single mutations (no underscores)
                        if '_' not in mutation:
                            variants[mutation] = {
                                'frequency': frequency,  # Use AF directly - already normalized
                                'coverage': coverage,
                                'position': pos,
                                'ref': ref,
                                'alt': alt
                            }
                        else:
                            logger.warning(f"Skipping multi-mutation {mutation} - not supported in current system")
                        
        except Exception as e:
            logger.error(f"Error parsing VCF file {vcf_file}: {e}")
            
        return variants
    
    def _parse_info(self, info_string):
        """Parse VCF INFO field"""
        info_dict = {}
        for item in info_string.split(';'):
            if '=' in item:
                key, value = item.split('=', 1)
                info_dict[key] = value
        return info_dict
    
    def _normalize_frequencies(self, sample):
        """
        AF field is already normalized by position-specific coverage, so no additional normalization needed
        
        Args:
            sample: Sample data dictionary
            
        Returns:
            dict: Sample data (no normalization applied)
        """
        # AF field is already properly normalized by position-specific coverage
        # No additional normalization needed
        return sample
    
    def calculate_fitness_scores_individual(self):
        """
        Calculate fitness scores for each individual repeat
        
        Returns:
            dict: Dictionary with repeat-specific fitness scores
        """
        logger.info("Calculating individual repeat fitness scores...")
        
        # AF field is already normalized by position-specific coverage
        input_samples = self.input_samples
        output_samples = self.output_samples
        
        # Calculate fitness for each repeat
        repeat_fitness = {}
        
        for rep_idx in range(len(input_samples)):
            input_sample = input_samples[rep_idx]
            output_sample = output_samples[rep_idx]
            
            # Get wild-type frequencies for this repeat
            wt_input_freq = input_sample.get('WT', {}).get('frequency', 0.001)
            
            # Handle missing WT in output - use count=1 approach
            if 'WT' in output_sample:
                wt_output_freq = output_sample['WT'].get('frequency', 0.001)
            else:
                # Calculate WT frequency using count=1 and total sample count
                total_output_count = sum(output_sample.get(mut, {}).get('count', 0) for mut in output_sample.keys())
                wt_output_freq = 1.0 / (total_output_count + 1) if total_output_count > 0 else 0.001
                logger.debug(f"WT missing from output repeat {rep_idx + 1}, using count=1 frequency: {wt_output_freq:.6f}")
            
            # Calculate fitness for each mutation in this repeat
            repeat_fitness[f"repeat_{rep_idx + 1}"] = {}
            
            for mutation in set(input_sample.keys()) | set(output_sample.keys()):
                if mutation == 'WT':
                    repeat_fitness[f"repeat_{rep_idx + 1}"][mutation] = 0.0
                    continue
                
                # Check minimum input coverage requirement
                input_count = input_sample.get(mutation, {}).get('count', 0)
                if input_count < self.min_input_coverage:
                    logger.debug(f"Skipping {mutation} in repeat {rep_idx + 1}: input count {input_count} < min_input_coverage {self.min_input_coverage}")
                    # Don't add to repeat_fitness - this will result in empty value
                    continue
                
                # Get frequencies for this repeat (AF is already normalized)
                # If mutation is missing from output, use count=1 to calculate frequency
                if mutation in output_sample:
                    f_out = output_sample[mutation].get('frequency', 0.001)
                else:
                    # Calculate frequency using count=1 and total sample count
                    total_output_count = sum(output_sample.get(mut, {}).get('count', 0) for mut in output_sample.keys())
                    f_out = 1.0 / (total_output_count + 1) if total_output_count > 0 else 0.001
                    logger.debug(f"Mutation {mutation} missing from output repeat {rep_idx + 1}, using count=1 frequency: {f_out:.6f}")
                
                f_in = input_sample.get(mutation, {}).get('frequency', 0.001)
                
                # Calculate fitness
                try:
                    fitness = np.log(f_out / f_in) - np.log(wt_output_freq / wt_input_freq)
                    repeat_fitness[f"repeat_{rep_idx + 1}"][mutation] = fitness
                    logger.debug(f"Calculated fitness for {mutation} in repeat {rep_idx + 1}: {fitness:.4f} (input_count={input_count})")
                except (ValueError, ZeroDivisionError):
                    repeat_fitness[f"repeat_{rep_idx + 1}"][mutation] = np.nan
        
        return repeat_fitness
    
    def calculate_fitness_scores_averaged(self):
        """
        Calculate fitness scores using averaged frequencies across replicates
        
        Returns:
            dict: Dictionary with averaged fitness scores
        """
        logger.info("Calculating averaged fitness scores...")
        
        # AF field is already normalized by position-specific coverage
        input_samples = self.input_samples
        output_samples = self.output_samples
        
        # Calculate average frequencies across replicates
        input_freqs = self._average_frequencies(input_samples)
        output_freqs = self._average_frequencies(output_samples)
        
        # Debug: print frequency dictionaries
        logger.info(f"Input frequencies: {input_freqs}")
        logger.info(f"Output frequencies: {output_freqs}")
        
        # Get wild-type frequencies
        wt_input_freq = input_freqs.get('WT', 0.001)
        
        # Handle missing WT in output - use count=1 approach
        if 'WT' in output_freqs:
            wt_output_freq = output_freqs.get('WT', 0.001)
        else:
            # Calculate WT frequency using count=1 and total sample count across all output samples
            total_output_count = sum(
                sum(output_sample.get(mut, {}).get('count', 0) for mut in output_sample.keys())
                for output_sample in self.output_samples
            )
            wt_output_freq = 1.0 / (total_output_count + 1) if total_output_count > 0 else 0.001
            logger.info(f"WT missing from output samples, using count=1 frequency: {wt_output_freq:.6f}")
        
        logger.info(f"Wild-type frequencies - Input: {wt_input_freq:.6f}, Output: {wt_output_freq:.6f}")
        
        # Calculate fitness scores for each mutation
        fitness_scores = {}
        
        for mutation in set(input_freqs.keys()) | set(output_freqs.keys()):
            if mutation == 'WT':
                fitness_scores[mutation] = 0.0
                continue
            
            # Check minimum input coverage requirement across all input samples
            avg_input_count = self._get_average_input_count(mutation)
            if avg_input_count < self.min_input_coverage:
                logger.debug(f"Skipping {mutation} in averaged analysis: avg input count {avg_input_count:.1f} < min_input_coverage {self.min_input_coverage}")
                continue
                
            # Get frequencies (AF is already normalized)
            # If mutation is missing from output, use count=1 to calculate frequency
            if mutation in output_freqs:
                f_out = output_freqs.get(mutation, 0.001)
            else:
                # Calculate frequency using count=1 and total sample count across all output samples
                total_output_count = sum(
                    sum(output_sample.get(mut, {}).get('count', 0) for mut in output_sample.keys())
                    for output_sample in self.output_samples
                )
                f_out = 1.0 / (total_output_count + 1) if total_output_count > 0 else 0.001
                logger.debug(f"Mutation {mutation} missing from output samples, using count=1 frequency: {f_out:.6f}")
            
            f_in = input_freqs.get(mutation, 0.001)
            
            # Calculate fitness using the equation
            try:
                fitness = np.log(f_out / f_in) - np.log(wt_output_freq / wt_input_freq)
                fitness_scores[mutation] = fitness
                logger.info(f"Calculated fitness for {mutation}: {fitness:.4f} (f_in={f_in:.6f}, f_out={f_out:.6f}, avg_input_count={avg_input_count:.1f})")
            except (ValueError, ZeroDivisionError):
                fitness_scores[mutation] = np.nan
                logger.warning(f"Could not calculate fitness for {mutation}")
        
        logger.info(f"Final averaged fitness scores: {fitness_scores}")
        return fitness_scores
    
    def _average_frequencies(self, samples):
        """Average frequencies across replicates"""
        all_mutations = set()
        for sample in samples:
            all_mutations.update(sample.keys())
        
        avg_freqs = {}
        for mutation in all_mutations:
            freqs = []
            for sample in samples:
                if mutation in sample:
                    freq = sample[mutation].get('frequency', 0)
                    freqs.append(freq)
                else:
                    freqs.append(0)
            
            # Remove zeros and calculate mean
            valid_freqs = [f for f in freqs if f > 0]
            if valid_freqs:
                avg_freqs[mutation] = np.mean(valid_freqs)
            else:
                avg_freqs[mutation] = 0.0
                
        return avg_freqs
    
    def _get_average_input_count(self, mutation):
        """Get average input count for a mutation across all input samples"""
        counts = []
        for input_sample in self.input_samples:
            count = input_sample.get(mutation, {}).get('count', 0)
            if count > 0:  # Only include samples where mutation is present
                counts.append(count)
        
        if counts:
            return np.mean(counts)
        else:
            return 0
    
    def calculate_correlation_analysis(self, repeat_fitness):
        """
        Calculate correlation between repeats for quality control
        
        Args:
            repeat_fitness: Dictionary with repeat-specific fitness scores
            
        Returns:
            dict: Correlation analysis results
        """
        logger.info("Calculating correlation analysis between repeats...")
        
        # Get all mutations present in at least one repeat
        all_mutations = set()
        for repeat_data in repeat_fitness.values():
            all_mutations.update(repeat_data.keys())
        
        # Remove WT from correlation analysis
        all_mutations.discard('WT')
        
        # Create correlation matrix
        repeat_names = list(repeat_fitness.keys())
        correlation_data = {}
        
        for mutation in all_mutations:
            # Get fitness scores for this mutation across repeats
            fitness_scores = []
            for repeat_name in repeat_names:
                fitness = repeat_fitness[repeat_name].get(mutation, np.nan)
                if not np.isnan(fitness):
                    fitness_scores.append(fitness)
            
            # Calculate correlation if we have at least 2 valid scores
            if len(fitness_scores) >= 2:
                correlation_data[mutation] = {
                    'fitness_scores': fitness_scores,
                    'mean_fitness': np.mean(fitness_scores),
                    'std_fitness': np.std(fitness_scores),
                    'cv_fitness': np.std(fitness_scores) / np.mean(fitness_scores) if np.mean(fitness_scores) != 0 else np.nan
                }
        
        # Calculate overall correlation between repeats
        repeat_correlations = {}
        for i, repeat1 in enumerate(repeat_names):
            for j, repeat2 in enumerate(repeat_names):
                if i < j:  # Avoid duplicate pairs
                    pair_name = f"{repeat1}_vs_{repeat2}"
                    
                    # Get common mutations
                    common_mutations = set(repeat_fitness[repeat1].keys()) & set(repeat_fitness[repeat2].keys())
                    common_mutations.discard('WT')
                    
                    if len(common_mutations) > 1:
                        # Calculate Pearson correlation
                        fitness1 = [repeat_fitness[repeat1][mut] for mut in common_mutations if not np.isnan(repeat_fitness[repeat1][mut])]
                        fitness2 = [repeat_fitness[repeat2][mut] for mut in common_mutations if not np.isnan(repeat_fitness[repeat2][mut])]
                        
                        if len(fitness1) > 1 and len(fitness2) > 1:
                            try:
                                correlation = np.corrcoef(fitness1, fitness2)[0, 1]
                                repeat_correlations[pair_name] = correlation
                            except:
                                repeat_correlations[pair_name] = np.nan
        
        return {
            'mutation_correlations': correlation_data,
            'repeat_correlations': repeat_correlations
        }
    
    def save_results(self, fitness_scores, output_file, repeat_fitness=None, correlation_analysis=None):
        """Save fitness scores to CSV file with repeat information"""
        logger.info(f"Saving fitness scores to {output_file}")
        
        # Prepare data for output
        results = []
        for mutation, fitness in fitness_scores.items():
            if mutation == 'WT':
                results.append({
                    'mutation': mutation,
                    'fitness_score': fitness,
                    'type': 'wild_type',
                    'ref_amino_acid': 'WT',
                    'alt_amino_acid': 'WT',
                    'amino_acid_position': 0
                })
            else:
                # Parse mutation string to extract amino acid information
                ref_aa, alt_aa, position = self._parse_mutation_string(mutation)
                
                # Determine mutation type
                if alt_aa == 'DEL':
                    mutation_type = 'deletion'
                elif alt_aa == 'INS':
                    mutation_type = 'insertion'
                elif ref_aa == alt_aa:
                    mutation_type = 'synonymous'
                elif alt_aa == '*':
                    mutation_type = 'nonsense'
                else:
                    mutation_type = 'missense'
                
                # Add repeat-specific fitness scores if available
                row_data = {
                    'mutation': mutation,
                    'fitness_score': fitness,
                    'type': mutation_type,
                    'ref_amino_acid': ref_aa,
                    'alt_amino_acid': alt_aa,
                    'amino_acid_position': position
                }
                
                # Add repeat-specific data
                if repeat_fitness:
                    for repeat_name, repeat_data in repeat_fitness.items():
                        if mutation in repeat_data:
                            row_data[f"{repeat_name}_fitness"] = repeat_data[mutation]
                            logger.debug(f"Added {repeat_name}_fitness for {mutation}: {repeat_data[mutation]}")
                        else:
                            row_data[f"{repeat_name}_fitness"] = np.nan
                            logger.debug(f"Missing {repeat_name}_fitness for {mutation}, setting to NaN")
                else:
                    logger.warning("No repeat_fitness data provided to save_results")
                
                results.append(row_data)
        
        # Create DataFrame and save
        df = pd.DataFrame(results)
        
        # Ensure proper data types
        df['amino_acid_position'] = pd.to_numeric(df['amino_acid_position'], errors='coerce').fillna(0).astype(int)
        df['fitness_score'] = pd.to_numeric(df['fitness_score'], errors='coerce')
        
        # Sort by fitness score
        df = df.sort_values('fitness_score', ascending=False)
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        
        # Save correlation analysis if available
        if correlation_analysis:
            correlation_file = output_file.replace('.csv', '_correlation.csv')
            self._save_correlation_results(correlation_analysis, correlation_file)
        
        logger.info(f"Saved {len(results)} fitness scores")
        
        # Print summary
        print(f"\n=== Fitness Calculation Summary ===")
        print(f"Input samples: {len(self.input_samples)}")
        print(f"Output samples: {len(self.output_samples)}")
        print(f"Total mutations processed: {len(fitness_scores)}")
        print(f"Single mutations: {len([m for m in fitness_scores.keys() if m != 'WT'])}")
        print(f"Wild-type fitness: {fitness_scores.get('WT', 'N/A')}")
        print(f"Fitness range: {min([f for f in fitness_scores.values() if isinstance(f, (int, float)) and not np.isnan(f)]):.4f} to {max([f for f in fitness_scores.values() if isinstance(f, (int, float)) and not np.isnan(f)]):.4f}")
        print(f"Sequencing type: Auto-detected from BAM files")
        print(f"Frequency source: AF field (already normalized by position-specific coverage)")
        print(f"Multi-mutations: Skipped (not supported in current system)")
        print(f"Individual repeat analysis: Enabled for correlation analysis")
        print(f"Results saved to: {output_file}")
        if repeat_fitness:
            print(f"Repeat-specific results: {len(repeat_fitness)} repeats analyzed")
        if correlation_analysis:
            print(f"Correlation analysis: Enabled for quality control")
    
    def _save_correlation_results(self, correlation_analysis, output_file):
        """Save correlation analysis results to CSV"""
        # Save repeat correlations
        repeat_corr_df = pd.DataFrame([
            {'repeat_pair': pair, 'correlation': corr}
            for pair, corr in correlation_analysis['repeat_correlations'].items()
        ])
        repeat_corr_df.to_csv(output_file.replace('.csv', '_repeats.csv'), index=False)
        
        # Save mutation correlations
        mutation_corr_data = []
        for mutation, data in correlation_analysis['mutation_correlations'].items():
            mutation_corr_data.append({
                'mutation': mutation,
                'mean_fitness': data['mean_fitness'],
                'std_fitness': data['std_fitness'],
                'cv_fitness': data['cv_fitness'],
                'fitness_scores': ','.join([f"{f:.4f}" for f in data['fitness_scores']])
            })
        
        mutation_corr_df = pd.DataFrame(mutation_corr_data)
        mutation_corr_df.to_csv(output_file.replace('.csv', '_mutations.csv'), index=False)
        
        logger.info(f"Saved correlation analysis to {output_file}")
    
    def _parse_mutation_string(self, mutation_string):
        """
        Parse mutation string to extract reference AA, alternative AA, and position
        
        Args:
            mutation_string: String like "T32Y" (missense) or "R61=" (synonymous)
            
        Returns:
            tuple: (ref_aa, alt_aa, position)
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
    
    def get_mutation_statistics(self):
        """
        Get statistics about the mutations analyzed
        
        Returns:
            dict: Statistics about mutations
        """
        all_mutations = set()
        for sample in self.input_samples + self.output_samples:
            all_mutations.update(sample.keys())
        
        stats = {
            'total_mutations': len(all_mutations),
            'single_mutations': len([m for m in all_mutations if '_' not in m and m != 'WT']),
            'multi_mutations_skipped': len([m for m in all_mutations if '_' in m]),
            'wild_type_variants': len([m for m in all_mutations if m == 'WT']),
            'input_samples': len(self.input_samples),
            'output_samples': len(self.output_samples)
        }
        
        return stats


def main():
    """Main function for Snakemake script execution"""
    # Snakemake variables
    input_csvs = snakemake.input.input_csvs
    output_csvs = snakemake.input.output_csvs
    fitness_output = snakemake.output.fitness
    summary_output = snakemake.output.summary
    
    # Debug information
    logger.info(f"Input CSVs: {input_csvs}")
    logger.info(f"Output CSVs: {output_csvs}")
    logger.info(f"Fitness output: {fitness_output}")
    logger.info(f"Summary output: {summary_output}")
    
    # Validate inputs
    if not input_csvs:
        logger.error("No input CSV files provided!")
        raise ValueError("Input CSV files are required")
    
    if not output_csvs:
        logger.error("No output CSV files provided!")
        raise ValueError("Output CSV files are required")
    
    # Get parameters
    min_input_coverage = getattr(snakemake.params, 'min_input_coverage', 10)
    logger.info(f"Using minimum input coverage: {min_input_coverage}")
    
    # Create fitness calculator
    calculator = DMSFitnessCalculator(min_input_coverage=min_input_coverage)
    
    # Load data
    calculator.load_variant_data(input_csvs, output_csvs)
    
    # Get mutation statistics
    stats = calculator.get_mutation_statistics()
    logger.info(f"Mutation statistics: {stats}")
    
    # Calculate individual repeat fitness scores
    repeat_fitness = calculator.calculate_fitness_scores_individual()
    logger.info(f"Individual repeat fitness calculated: {len(repeat_fitness)} repeats")
    for repeat_name, repeat_data in repeat_fitness.items():
        logger.info(f"  {repeat_name}: {len(repeat_data)} mutations")
        if repeat_data:
            sample_mutations = list(repeat_data.keys())[:5]  # Show first 5
            logger.info(f"    Sample mutations: {sample_mutations}")
    
    # Calculate averaged fitness scores
    averaged_fitness = calculator.calculate_fitness_scores_averaged()
    logger.info(f"Averaged fitness calculated: {len(averaged_fitness)} mutations")
    
    # Calculate correlation analysis
    correlation_analysis = calculator.calculate_correlation_analysis(repeat_fitness)
    
    # Save results with repeat information
    logger.info("About to save results...")
    logger.info(f"repeat_fitness keys: {list(repeat_fitness.keys())}")
    logger.info(f"averaged_fitness keys: {list(averaged_fitness.keys())[:10]}")  # First 10
    calculator.save_results(averaged_fitness, fitness_output, repeat_fitness, correlation_analysis)
    
    # Create summary file
    with open(summary_output, 'w') as f:
        f.write("DMS Fitness Analysis Summary\n")
        f.write("=" * 30 + "\n\n")
        f.write(f"Total variants analyzed: {stats['total_mutations']}\n")
        f.write(f"Single mutations processed: {stats['single_mutations']}\n")
        f.write(f"Multi-mutations skipped: {stats['multi_mutations_skipped']}\n")
        f.write(f"Wild type variants: {stats['wild_type_variants']}\n")
        f.write(f"Input CSVs: {stats['input_samples']}\n")
        f.write(f"Output CSVs: {stats['output_samples']}\n")
        f.write(f"Minimum input coverage filter: {min_input_coverage}\n")
        f.write(f"Fitness scores saved to: {fitness_output}\n\n")
        
        f.write("Repeat Correlation Analysis:\n")
        for pair, corr in correlation_analysis['repeat_correlations'].items():
            f.write(f"  {pair}: {corr:.4f}\n")
        
        f.write(f"\nNote: Variants with input coverage < {min_input_coverage} were excluded\n")
        f.write(f"from fitness calculation to ensure reliable estimates.\n")
        f.write(f"Multi-mutations were skipped because fitness calculation\n")
        f.write(f"focuses on single mutations for accurate analysis.\n")
        
        if stats['multi_mutations_skipped'] > 0:
            f.write(f"\nSkipped multi-mutations: {stats['multi_mutations_skipped']}\n")
            f.write("These may represent:\n")
            f.write("1. True co-occurring mutations in the same read\n")
            f.write("2. Position-based grouping artifacts\n")
            f.write("3. Sample-level frequency patterns\n")
            f.write("\nTo analyze true multi-mutations, use read-level analysis\n")
            f.write("of the BAM files to detect which mutations occur together.\n")


if __name__ == "__main__":
    main()
