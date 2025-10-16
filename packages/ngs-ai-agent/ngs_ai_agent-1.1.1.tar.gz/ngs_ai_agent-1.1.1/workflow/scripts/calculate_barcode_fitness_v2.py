#!/usr/bin/env python3
"""
Barcode Fitness Calculator V2 for Deep Mutational Scanning
Implements the fitness equation: w_i = log(f_i^out / f_i^in) - log(f_WT^out / f_WT^in)

This version follows the amplicon-based fitness_calculator.py approach:
1. Calculate fitness for each repeat individually
2. Average fitness across repeats
3. Include correlation analysis between repeats
4. Use count=1 approach for missing mutations
5. Proper mutation parsing and classification

Enhanced to calculate fitness for each repeat individually for accurate correlation analysis.
"""

import pandas as pd
import numpy as np
import logging
from collections import defaultdict
import re
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BarcodeFitnessCalculatorV2:
    """
    Calculate fitness scores for barcode-coupled DMS variants
    
    This class implements the fitness calculation using the equation:
    w_i = log(f_i^out / f_i^in) - log(f_WT^out / f_WT^in)
    
    where f_i is the frequency of mutation i in input (in) and output (out) samples.
    
    V2 Features:
    - Per-repeat fitness calculation
    - Averaged fitness across repeats
    - Correlation analysis between repeats
    - Count=1 approach for missing mutations
    - Proper mutation parsing and classification
    """
    
    def __init__(self, min_input_coverage=10, pseudocount=1):
        self.input_samples = []
        self.output_samples = []
        self.min_input_coverage = min_input_coverage
        self.pseudocount = pseudocount
        
    def load_barcode_data(self, input_files, output_files, barcode_map_file):
        """
        Load barcode count data from input and output files
        
        Args:
            input_files: List of input CSV files (before selection)
            output_files: List of output CSV files (after selection)
            barcode_map_file: CSV file with barcode→variant mapping
        """
        logger.info("Loading barcode count data...")
        
        # Load barcode mapping
        logger.info(f"Loading barcode mapping from {barcode_map_file}")
        barcode_mapping = pd.read_csv(barcode_map_file)
        barcode_to_mutation = dict(zip(barcode_mapping['barcode'], barcode_mapping['mutation']))
        
        # Load input samples
        for csv_file in input_files:
            sample_data = self._parse_barcode_csv(csv_file, "input", barcode_to_mutation)
            self.input_samples.append(sample_data)
            
        # Load output samples
        for csv_file in output_files:
            sample_data = self._parse_barcode_csv(csv_file, "output", barcode_to_mutation)
            self.output_samples.append(sample_data)
            
        logger.info(f"Loaded {len(self.input_samples)} input samples and {len(self.output_samples)} output samples")
    
    def _parse_barcode_csv(self, csv_file, sample_type, barcode_to_mutation):
        """Parse barcode count CSV file and map to mutations"""
        variants = defaultdict(dict)
        
        try:
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded CSV with {len(df)} rows from {csv_file}")
            
            # Check for required columns
            required_columns = ['mutation', 'count']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in {csv_file}: {missing_columns}")
                logger.error(f"Available columns: {list(df.columns)}")
                return variants
            
            # Calculate total count for frequency normalization
            total_count = df['count'].sum()
            logger.info(f"Total count in {csv_file}: {total_count:,}")
            
            # Process each mutation
            for _, row in df.iterrows():
                mutation = row['mutation']
                count = row['count']
                frequency = count / total_count if total_count > 0 else 0
                
                # Store variant data
                variants[mutation] = {
                    'frequency': frequency,
                    'count': count,
                    'coverage': count,  # Use count as coverage
                    'type': self._classify_mutation_type(mutation)
                }
                    
                logger.debug(f"Added variant {mutation}: count={count}, frequency={frequency:.6f}")
                    
        except Exception as e:
            logger.error(f"Error parsing CSV file {csv_file}: {e}")
            return variants
        
        logger.info(f"Parsed {len(variants)} variants from {csv_file}")
        return variants
    
    def _classify_mutation_type(self, mutation):
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
        elif mutation.startswith('DEL'):
            return 'deletion'
        elif mutation.startswith('INS'):
            return 'insertion'
        else:
            return 'missense'
    
    def calculate_fitness_scores_individual(self):
        """
        Calculate fitness scores for each individual repeat
        
        Returns:
            dict: Dictionary with repeat-specific fitness scores
        """
        logger.info("Calculating individual repeat fitness scores...")
        
        # Calculate fitness for each repeat
        repeat_fitness = {}
        
        for rep_idx in range(len(self.input_samples)):
            input_sample = self.input_samples[rep_idx]
            output_sample = self.output_samples[rep_idx]
            
            # Get wild-type frequencies for this repeat
            wt_input_freq = input_sample.get('WT', {}).get('frequency', 0.001)
            
            # Handle missing WT in output - use count=1 approach
            if 'WT' in output_sample:
                wt_output_freq = output_sample['WT'].get('frequency', 0.001)
            else:
                # Calculate WT frequency using count=1 and total sample count
                total_output_count = sum(output_sample.get(mut, {}).get('count', 0) for mut in output_sample.keys())
                wt_output_freq = self.pseudocount / (total_output_count + self.pseudocount) if total_output_count > 0 else 0.001
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
                    continue
                
                # Get frequencies for this repeat
                # If mutation is missing from output, use count=1 to calculate frequency
                if mutation in output_sample:
                    f_out = output_sample[mutation].get('frequency', 0.001)
                else:
                    # Calculate frequency using count=1 and total sample count
                    total_output_count = sum(output_sample.get(mut, {}).get('count', 0) for mut in output_sample.keys())
                    f_out = self.pseudocount / (total_output_count + self.pseudocount) if total_output_count > 0 else 0.001
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
        
        # Calculate average frequencies across replicates
        input_freqs = self._average_frequencies(self.input_samples)
        output_freqs = self._average_frequencies(self.output_samples)
        
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
            wt_output_freq = self.pseudocount / (total_output_count + self.pseudocount) if total_output_count > 0 else 0.001
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
                
            # Get frequencies
            # If mutation is missing from output, use count=1 to calculate frequency
            if mutation in output_freqs:
                f_out = output_freqs.get(mutation, 0.001)
            else:
                # Calculate frequency using count=1 and total sample count across all output samples
                total_output_count = sum(
                    sum(output_sample.get(mut, {}).get('count', 0) for mut in output_sample.keys())
                    for output_sample in self.output_samples
                )
                f_out = self.pseudocount / (total_output_count + self.pseudocount) if total_output_count > 0 else 0.001
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
    
    def _parse_mutation_string(self, mutation_string):
        """
        Parse mutation string to extract reference AA, alternative AA, and position
        
        Args:
            mutation_string: String like "T32Y" (missense) or "R61=" (synonymous)
            
        Returns:
            tuple: (ref_aa, alt_aa, position)
        """
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
                    'type': 'wildtype',
                    'ref_amino_acid': 'WT',
                    'alt_amino_acid': 'WT',
                    'amino_acid_position': 0
                })
            else:
                # Parse mutation string to extract amino acid information
                ref_aa, alt_aa, position = self._parse_mutation_string(mutation)
                
                # Determine mutation type
                mutation_type = self._classify_mutation_type(mutation)
                
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
        print(f"\n=== Barcode Fitness Calculation V2 Summary ===")
        print(f"Input samples: {len(self.input_samples)}")
        print(f"Output samples: {len(self.output_samples)}")
        print(f"Total mutations processed: {len(fitness_scores)}")
        print(f"Single mutations: {len([m for m in fitness_scores.keys() if m != 'WT' and '_' not in m])}")
        print(f"Multi-mutations: {len([m for m in fitness_scores.keys() if '_' in m])}")
        print(f"Wild-type fitness: {fitness_scores.get('WT', 'N/A')}")
        if fitness_scores:
            valid_fitness = [f for f in fitness_scores.values() if isinstance(f, (int, float)) and not np.isnan(f)]
            if valid_fitness:
                print(f"Fitness range: {min(valid_fitness):.4f} to {max(valid_fitness):.4f}")
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
            'multi_mutations': len([m for m in all_mutations if '_' in m]),
            'wild_type_variants': len([m for m in all_mutations if m == 'WT']),
            'input_samples': len(self.input_samples),
            'output_samples': len(self.output_samples)
        }
        
        return stats


def main():
    """Main function for Snakemake script execution"""
    # Get parameters from Snakemake
    input_files = snakemake.input.input_counts
    output_files = snakemake.input.output_counts
    barcode_map_file = snakemake.input.barcode_map
    
    fitness_output = snakemake.output.fitness_scores
    annotated_output = snakemake.output.annotated_fitness
    summary_output = snakemake.output.analysis_summary
    
    min_input_coverage = snakemake.params.min_input_coverage
    pseudocount = snakemake.params.pseudocount
    
    # Create output directories
    Path(fitness_output).parent.mkdir(parents=True, exist_ok=True)
    Path(summary_output).parent.mkdir(parents=True, exist_ok=True)
    
    # Create fitness calculator
    calculator = BarcodeFitnessCalculatorV2(min_input_coverage=min_input_coverage, pseudocount=pseudocount)
    
    # Load data
    calculator.load_barcode_data(input_files, output_files, barcode_map_file)
    
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
    
    # Create annotated_fitness.csv (same as fitness_scores.csv for barcode DMS)
    calculator.save_results(averaged_fitness, annotated_output, repeat_fitness, correlation_analysis)
    
    # Create summary file
    with open(summary_output, 'w') as f:
        f.write("Barcode DMS Fitness Analysis V2 Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total variants analyzed: {stats['total_mutations']}\n")
        f.write(f"Single mutations processed: {stats['single_mutations']}\n")
        f.write(f"Multi-mutations processed: {stats['multi_mutations']}\n")
        f.write(f"Wild type variants: {stats['wild_type_variants']}\n")
        f.write(f"Input samples: {stats['input_samples']}\n")
        f.write(f"Output samples: {stats['output_samples']}\n")
        f.write(f"Minimum input coverage filter: {min_input_coverage}\n")
        f.write(f"Pseudocount for missing mutations: {pseudocount}\n")
        f.write(f"Fitness scores saved to: {fitness_output}\n")
        f.write(f"Annotated fitness saved to: {annotated_output}\n\n")
        
        f.write("Repeat Correlation Analysis:\n")
        for pair, corr in correlation_analysis['repeat_correlations'].items():
            f.write(f"  {pair}: {corr:.4f}\n")
        
        f.write(f"\nNote: Variants with input coverage < {min_input_coverage} were excluded\n")
        f.write(f"from fitness calculation to ensure reliable estimates.\n")
        f.write(f"Missing mutations in output samples use count={pseudocount} approach\n")
        f.write(f"for biologically meaningful fitness calculations.\n")
        f.write(f"Per-repeat fitness calculation enables correlation analysis\n")
        f.write(f"for quality control and reproducibility assessment.\n")
    
    logger.info("Barcode fitness calculation V2 complete!")


if __name__ == "__main__":
    main()
