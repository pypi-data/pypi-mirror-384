#!/usr/bin/env python3
"""
Create heatmap visualization for Deep Mutational Scanning results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DMSHeatmapGenerator:
    """Generate heatmaps for Deep Mutational Scanning data"""
    
    def __init__(self, colormap="RdBu_r", figsize=(12, 8), dpi=300, exclude_multi_mutations=True):
        self.colormap = colormap
        self.figsize = figsize
        self.dpi = dpi
        self.exclude_multi_mutations = exclude_multi_mutations
        
        # Standard amino acid order
        self.amino_acids = ['A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H', 'I', 
                           'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y', 'V', '*']
    
    def create_heatmaps(self, fitness_file, output_png, output_html):
        """
        Create both static and interactive heatmaps
        
        Args:
            fitness_file: Input fitness CSV file
            output_png: Output PNG file path
            output_html: Output HTML file path
        """
        logger.info("Creating DMS heatmaps...")
        
        # Load fitness data
        fitness_df = pd.read_csv(fitness_file)
        logger.info(f"Loaded fitness data with {len(fitness_df)} rows")
        
        # Create heatmap matrix
        heatmap_matrix = self._create_heatmap_matrix(fitness_df)
        
        # Check if matrix is empty
        if heatmap_matrix.empty or heatmap_matrix.shape[1] == 0:
            logger.warning("Heatmap matrix is empty. Creating placeholder plots.")
            self._create_empty_plots(output_png, output_html)
            return
        
        # Create static heatmap
        self._create_static_heatmap(heatmap_matrix, output_png)
        
        # Create interactive heatmap
        self._create_interactive_heatmap(heatmap_matrix, fitness_df, output_html)
        
        logger.info(f"Heatmaps created: {output_png}, {output_html}")
    
    def _create_empty_plots(self, output_png, output_html):
        """Create placeholder plots when no data is available"""
        logger.info("Creating empty placeholder plots")
        
        # Create empty static plot
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No variants available for heatmap\nCheck your data and pipeline', 
                ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
        plt.title('Deep Mutational Scanning Heatmap\n(No Data Available)', fontsize=16)
        plt.axis('off')
        plt.savefig(output_png, dpi=150, bbox_inches='tight')
        plt.close()
        
        # Create empty interactive plot
        fig = go.Figure()
        fig.add_annotation(
            text="No variants available for heatmap<br>Check your data and pipeline",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title="Deep Mutational Scanning Heatmap (No Data Available)",
            xaxis_title="Amino Acid Position",
            yaxis_title="Amino Acid Substitution"
        )
        fig.write_html(output_html)
    
    def _create_heatmap_matrix(self, fitness_df):
        """Create matrix for heatmap visualization"""
        logger.info(f"Creating heatmap matrix from {len(fitness_df)} variants")
        logger.info(f"Available columns: {list(fitness_df.columns)}")
        
        # Check if required columns exist
        required_columns = ['alt_amino_acid', 'amino_acid_position', 'fitness_score']
        missing_columns = [col for col in required_columns if col not in fitness_df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            logger.error(f"Available columns: {list(fitness_df.columns)}")
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Filter for non-WT mutations (exclude wild type)
        filtered_df = fitness_df[
            (fitness_df['mutation'] != 'WT') & 
            (fitness_df['fitness_score'].notna())
        ].copy()
        
        # Optionally filter out multi-mutations (those with '_' in mutation name)
        if self.exclude_multi_mutations:
            original_count = len(filtered_df)
            filtered_df = filtered_df[~filtered_df['mutation'].str.contains('_', na=False)]
            excluded_count = original_count - len(filtered_df)
            if excluded_count > 0:
                logger.info(f"Excluded {excluded_count} multi-mutations from heatmap")
        
        logger.info(f"Filtered to {len(filtered_df)} non-WT variants for heatmap")
        
        if filtered_df.empty:
            logger.warning("No variants found for heatmap. Creating empty matrix.")
            # Create empty matrix with proper structure
            empty_matrix = pd.DataFrame(index=self.amino_acids, columns=[])
            return empty_matrix
        
        # Create pivot table
        heatmap_matrix = filtered_df.pivot_table(
            index='alt_amino_acid',
            columns='amino_acid_position',
            values='fitness_score',
            aggfunc='mean'
        )
        
        # Reindex to ensure all amino acids are present
        heatmap_matrix = heatmap_matrix.reindex(self.amino_acids)
        
        # Fill NaN values with 0 for visualization
        heatmap_matrix = heatmap_matrix.fillna(0)
        
        logger.info(f"Heatmap matrix created with shape: {heatmap_matrix.shape}")
        return heatmap_matrix
    
    def _create_static_heatmap(self, heatmap_matrix, output_file):
        """Create static heatmap using matplotlib/seaborn"""
        logger.info(f"Creating static heatmap with matrix shape: {heatmap_matrix.shape}")
        
        try:
            plt.figure(figsize=self.figsize, dpi=self.dpi)
            
            # Create heatmap
            ax = sns.heatmap(
                heatmap_matrix,
                cmap=self.colormap,
                center=0,
                cbar_kws={'label': 'Fitness Score'},
                xticklabels=True,
                yticklabels=True,
                linewidths=0.1
            )
            
            # Customize plot
            plt.title('Deep Mutational Scanning Heatmap\nFitness Effects by Position and Amino Acid', 
                     fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Amino Acid Position', fontsize=12, fontweight='bold')
            plt.ylabel('Amino Acid Substitution', fontsize=12, fontweight='bold')
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save plot
            plt.savefig(output_file, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Static heatmap saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error creating static heatmap: {e}")
            # Create a simple error plot
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, f'Error creating heatmap:\n{str(e)}', 
                    ha='center', va='center', transform=plt.gca().transAxes, fontsize=12)
            plt.title('Heatmap Creation Error', fontsize=14)
            plt.axis('off')
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close()
            raise
    
    def _create_interactive_heatmap(self, heatmap_matrix, fitness_df, output_file):
        """Create interactive heatmap using plotly"""
        logger.info(f"Creating interactive heatmap with matrix shape: {heatmap_matrix.shape}")
        
        try:
            # Prepare data for plotly
            z_values = heatmap_matrix.values
            x_labels = [str(col) for col in heatmap_matrix.columns]
            y_labels = list(heatmap_matrix.index)
            
            # Create hover text with additional information
            hover_text = self._create_hover_text(heatmap_matrix, fitness_df)
            
            # Create main heatmap
            fig = go.Figure(data=go.Heatmap(
                z=z_values,
                x=x_labels,
                y=y_labels,
                hovertemplate='Position: %{x}<br>Amino Acid: %{y}<br>Fitness Score: %{z:.3f}<br>%{text}<extra></extra>',
                text=hover_text,
                colorscale=self._convert_colormap_to_plotly(),
                zmid=0,
                colorbar=dict(title="Fitness Score")
            ))
            
            # Update layout
            fig.update_layout(
                title={
                    'text': 'Deep Mutational Scanning Heatmap<br><sub>Fitness Effects by Position and Amino Acid</sub>',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18}
                },
                xaxis_title='Amino Acid Position',
                yaxis_title='Amino Acid Substitution',
                width=max(800, len(x_labels) * 20),
                height=600,
                font=dict(size=12)
            )
            
            # Add subplot with fitness distribution
            fig_combined = make_subplots(
                rows=2, cols=1,
                row_heights=[0.8, 0.2],
                subplot_titles=('Fitness Heatmap', 'Fitness Distribution'),
                vertical_spacing=0.1
            )
            
            # Add heatmap to subplot
            fig_combined.add_trace(
                go.Heatmap(
                    z=z_values,
                    x=x_labels,
                    y=y_labels,
                    hovertemplate='Position: %{x}<br>Amino Acid: %{y}<br>Fitness Score: %{z:.3f}<extra></extra>',
                    colorscale=self._convert_colormap_to_plotly(),
                    zmid=0,
                    showscale=True,
                    colorbar=dict(title="Fitness Score", x=1.02)
                ),
                row=1, col=1
            )
            
            # Add fitness distribution histogram
            fitness_values = fitness_df['fitness_score'].dropna()
            fig_combined.add_trace(
                go.Histogram(
                    x=fitness_values,
                    nbinsx=50,
                    name='Fitness Distribution',
                    marker_color='skyblue',
                    opacity=0.7
                ),
                row=2, col=1
            )
            
            # Update combined layout
            fig_combined.update_layout(
                title={
                    'text': 'Deep Mutational Scanning Analysis',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18}
                },
                width=max(800, len(x_labels) * 15),
                height=800,
                showlegend=False
            )
            
            fig_combined.update_xaxes(title_text="Amino Acid Position", row=1, col=1)
            fig_combined.update_yaxes(title_text="Amino Acid Substitution", row=1, col=1)
            fig_combined.update_xaxes(title_text="Fitness Score", row=2, col=1)
            fig_combined.update_yaxes(title_text="Frequency", row=2, col=1)
            
            # Save interactive plot
            fig_combined.write_html(output_file)
            
            logger.info(f"Interactive heatmap saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error creating interactive heatmap: {e}")
            # Create a simple error plot
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating heatmap:<br>{str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(
                title="Heatmap Creation Error",
                xaxis_title="Amino Acid Position",
                yaxis_title="Amino Acid Substitution"
            )
            fig.write_html(output_file)
            raise
    
    def _create_hover_text(self, heatmap_matrix, fitness_df):
        """Create hover text matrix with additional information"""
        hover_matrix = []
        
        for aa in heatmap_matrix.index:
            hover_row = []
            for pos in heatmap_matrix.columns:
                # Find corresponding data
                subset = fitness_df[
                    (fitness_df['alt_amino_acid'] == aa) & 
                    (fitness_df['amino_acid_position'] == pos)
                ]
                
                if not subset.empty:
                    row = subset.iloc[0]
                    
                    # Build hover text with available columns
                    hover_parts = [f"Mutation: {row['ref_amino_acid']}{pos}{aa}"]
                    
                    # Add type if available
                    if 'type' in row:
                        hover_parts.append(f"Type: {row['type']}")
                    elif 'mutation_type' in row:
                        hover_parts.append(f"Type: {row['mutation_type']}")
                    
                    # Add fitness score
                    if 'fitness_score' in row:
                        hover_parts.append(f"Fitness: {row['fitness_score']:.4f}")
                    
                    # Add frequency if available
                    if 'frequency' in row:
                        hover_parts.append(f"Frequency: {row['frequency']:.4f}")
                    
                    # Add coverage if available
                    if 'coverage' in row:
                        hover_parts.append(f"Coverage: {row['coverage']}")
                    
                    hover_text = "<br>".join(hover_parts)
                else:
                    hover_text = "No data"
                
                hover_row.append(hover_text)
            hover_matrix.append(hover_row)
        
        return hover_matrix
    
    def _convert_colormap_to_plotly(self):
        """Convert matplotlib colormap to plotly format"""
        if self.colormap == "RdBu_r":
            return "RdBu_r"
        elif self.colormap == "viridis":
            return "Viridis"
        elif self.colormap == "plasma":
            return "Plasma"
        else:
            return "RdBu_r"  # Default fallback


def main():
    """Main function for Snakemake script execution"""
    # Snakemake variables
    fitness_file = snakemake.input.fitness
    output_png = snakemake.output.heatmap
    output_html = snakemake.output.interactive
    
    logger.info(f"Starting heatmap generation...")
    logger.info(f"Fitness file: {fitness_file}")
    logger.info(f"Output PNG: {output_png}")
    logger.info(f"Output HTML: {output_html}")
    
    # Parameters with defaults
    try:
        colormap = snakemake.params.colormap
        figsize = snakemake.params.figsize
        dpi = snakemake.params.dpi
        exclude_multi_mutations = snakemake.params.exclude_multi_mutations
        logger.info(f"Parameters: colormap={colormap}, figsize={figsize}, dpi={dpi}, exclude_multi_mutations={exclude_multi_mutations}")
    except AttributeError as e:
        logger.warning(f"Some parameters not found, using defaults: {e}")
        colormap = "RdBu_r"
        figsize = (12, 8)
        dpi = 300
        exclude_multi_mutations = True  # Default to excluding multi-mutations
    
    # Create heatmap generator
    generator = DMSHeatmapGenerator(
        colormap=colormap,
        figsize=figsize,
        dpi=dpi,
        exclude_multi_mutations=exclude_multi_mutations
    )
    
    # Generate heatmaps
    generator.create_heatmaps(fitness_file, output_png, output_html)
    
    logger.info("Heatmap generation completed successfully!")


if __name__ == "__main__":
    main()
