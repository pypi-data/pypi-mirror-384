#!/usr/bin/env python3
"""
Create additional fitness visualization plots
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FitnessPlotter:
    """Create various fitness-related plots"""
    
    def __init__(self, figsize=(10, 6), dpi=300):
        self.figsize = figsize
        self.dpi = dpi
    
    def create_fitness_plots(self, fitness_file, output_file):
        """
        Create fitness distribution and other plots
        
        Args:
            fitness_file: Input fitness CSV file
            output_file: Output PNG file path
        """
        logger.info("Creating fitness distribution plots...")
        
        # Load fitness data
        fitness_df = pd.read_csv(fitness_file)
        
        # Create multi-panel figure
        fig, axes = plt.subplots(2, 2, figsize=(15, 10), dpi=self.dpi)
        fig.suptitle('Deep Mutational Scanning Fitness Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Fitness distribution histogram
        self._plot_fitness_distribution(fitness_df, axes[0, 0])
        
        # Plot 2: Fitness by mutation type
        self._plot_fitness_by_mutation_type(fitness_df, axes[0, 1])
        
        # Plot 3: Fitness by position
        self._plot_fitness_by_position(fitness_df, axes[1, 0])
        
        # Plot 4: Coverage vs fitness
        self._plot_coverage_vs_fitness(fitness_df, axes[1, 1])
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Fitness plots created: {output_file}")
    
    def _plot_fitness_distribution(self, fitness_df, ax):
        """Plot fitness score distribution"""
        fitness_scores = fitness_df['fitness_score'].dropna()
        
        ax.hist(fitness_scores, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        ax.axvline(fitness_scores.mean(), color='red', linestyle='--', 
                  label=f'Mean: {fitness_scores.mean():.2f}')
        ax.axvline(0, color='black', linestyle='-', alpha=0.5, label='Neutral')
        
        ax.set_xlabel('Fitness Score')
        ax.set_ylabel('Frequency')
        ax.set_title('Fitness Score Distribution')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_fitness_by_mutation_type(self, fitness_df, ax):
        """Plot fitness scores by mutation type"""
        mutation_types = ['synonymous', 'missense', 'nonsense']
        
        # Filter for relevant mutation types
        filtered_df = fitness_df[fitness_df['mutation_type'].isin(mutation_types)]
        
        if not filtered_df.empty:
            sns.boxplot(data=filtered_df, x='mutation_type', y='fitness_score', ax=ax)
            ax.set_xlabel('Mutation Type')
            ax.set_ylabel('Fitness Score')
            ax.set_title('Fitness by Mutation Type')
            ax.axhline(0, color='black', linestyle='--', alpha=0.5)
            
            # Rotate x-axis labels
            ax.tick_params(axis='x', rotation=45)
        else:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Fitness by Mutation Type')
    
    def _plot_fitness_by_position(self, fitness_df, ax):
        """Plot fitness scores along protein sequence"""
        # Group by position and calculate mean fitness
        position_fitness = fitness_df.groupby('amino_acid_position')['fitness_score'].agg(['mean', 'std']).reset_index()
        
        if not position_fitness.empty:
            ax.plot(position_fitness['amino_acid_position'], position_fitness['mean'], 
                   marker='o', markersize=3, alpha=0.7)
            
            # Add error bars if std is available
            if 'std' in position_fitness.columns:
                ax.fill_between(position_fitness['amino_acid_position'],
                              position_fitness['mean'] - position_fitness['std'],
                              position_fitness['mean'] + position_fitness['std'],
                              alpha=0.3)
            
            ax.axhline(0, color='black', linestyle='--', alpha=0.5)
            ax.set_xlabel('Amino Acid Position')
            ax.set_ylabel('Mean Fitness Score')
            ax.set_title('Fitness Along Protein Sequence')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Fitness Along Protein Sequence')
    
    def _plot_coverage_vs_fitness(self, fitness_df, ax):
        """Plot coverage vs fitness score"""
        # Remove outliers for better visualization
        q1 = fitness_df['coverage'].quantile(0.25)
        q3 = fitness_df['coverage'].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        filtered_df = fitness_df[
            (fitness_df['coverage'] >= lower_bound) & 
            (fitness_df['coverage'] <= upper_bound)
        ]
        
        if not filtered_df.empty:
            ax.scatter(filtered_df['coverage'], filtered_df['fitness_score'], 
                      alpha=0.6, s=20)
            
            # Add trend line
            z = np.polyfit(filtered_df['coverage'], filtered_df['fitness_score'], 1)
            p = np.poly1d(z)
            ax.plot(filtered_df['coverage'], p(filtered_df['coverage']), 
                   "r--", alpha=0.8, label=f'Trend line')
            
            ax.set_xlabel('Coverage')
            ax.set_ylabel('Fitness Score')
            ax.set_title('Coverage vs Fitness Score')
            ax.axhline(0, color='black', linestyle='--', alpha=0.5)
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Coverage vs Fitness Score')


def main():
    """Main function for Snakemake script execution"""
    # Snakemake variables
    fitness_file = snakemake.input.fitness
    output_file = snakemake.output.histogram
    
    # Create plotter
    plotter = FitnessPlotter()
    
    # Create plots
    plotter.create_fitness_plots(fitness_file, output_file)


if __name__ == "__main__":
    main()
