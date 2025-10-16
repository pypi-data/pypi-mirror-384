#!/usr/bin/env python3
"""
Generate QC report for barcode-coupled DMS analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from pathlib import Path
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_barcode_data(count_files, barcode_map_file):
    """Load and combine barcode count data"""
    
    # Load barcode mapping
    barcode_mapping = pd.read_csv(barcode_map_file)
    
    # Load count data
    all_data = []
    for count_file in count_files:
        sample_name = Path(count_file).stem.replace('_barcode_counts', '')
        df = pd.read_csv(count_file)
        df['sample'] = sample_name
        all_data.append(df)
    
    combined_data = pd.concat(all_data, ignore_index=True)
    
    return combined_data, barcode_mapping

def generate_barcode_qc_plots(combined_data, barcode_mapping, output_file):
    """Generate QC plots for barcode analysis"""
    
    # Set up the plot
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Barcode-coupled DMS QC Report', fontsize=16, fontweight='bold')
    
    # Plot 1: Barcode count distribution
    ax1 = axes[0, 0]
    combined_data['count'].hist(bins=50, ax=ax1, alpha=0.7)
    ax1.set_xlabel('Barcode Count')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Barcode Count Distribution')
    ax1.set_yscale('log')
    
    # Plot 2: Mutation type distribution
    ax2 = axes[0, 1]
    mutation_types = combined_data['mutation'].apply(classify_mutation_type).value_counts()
    mutation_types.plot(kind='bar', ax=ax2)
    ax2.set_xlabel('Mutation Type')
    ax2.set_ylabel('Count')
    ax2.set_title('Mutation Type Distribution')
    ax2.tick_params(axis='x', rotation=45)
    
    # Plot 3: Sample coverage comparison
    ax3 = axes[0, 2]
    sample_totals = combined_data.groupby('sample')['count'].sum()
    sample_totals.plot(kind='bar', ax=ax3)
    ax3.set_xlabel('Sample')
    ax3.set_ylabel('Total Reads')
    ax3.set_title('Total Reads per Sample')
    ax3.tick_params(axis='x', rotation=45)
    
    # Plot 4: Barcode mapping efficiency
    ax4 = axes[1, 0]
    mapped_counts = combined_data[combined_data['mutation'] != 'UNMAPPED']['count'].sum()
    unmapped_counts = combined_data[combined_data['mutation'] == 'UNMAPPED']['count'].sum()
    
    mapping_data = pd.Series([mapped_counts, unmapped_counts], 
                           index=['Mapped', 'Unmapped'])
    mapping_data.plot(kind='pie', ax=ax4, autopct='%1.1f%%')
    ax4.set_title('Barcode Mapping Efficiency')
    ax4.set_ylabel('')
    
    # Plot 5: Top variants by abundance
    ax5 = axes[1, 1]
    top_variants = combined_data.groupby('mutation')['count'].sum().nlargest(20)
    top_variants.plot(kind='barh', ax=ax5)
    ax5.set_xlabel('Total Count')
    ax5.set_ylabel('Mutation')
    ax5.set_title('Top 20 Most Abundant Variants')
    
    # Plot 6: Barcode mapping coverage
    ax6 = axes[1, 2]
    barcode_coverage = barcode_mapping['count'].hist(bins=30, ax=ax6, alpha=0.7)
    ax6.set_xlabel('Barcode Coverage in Long Reads')
    ax6.set_ylabel('Frequency')
    ax6.set_title('Barcode Mapping Coverage Distribution')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"QC plots saved to {output_file}")

def classify_mutation_type(mutation):
    """Classify mutation type for QC reporting"""
    
    if mutation == 'WT':
        return 'Wild-type'
    elif mutation == 'UNMAPPED':
        return 'Unmapped'
    elif '_' in mutation:
        return 'Multiple'
    elif mutation.endswith('*'):
        return 'Nonsense'
    elif 'DEL' in mutation:
        return 'Deletion'
    elif 'INS' in mutation:
        return 'Insertion'
    else:
        return 'Missense'

def generate_qc_html_report(combined_data, barcode_mapping, output_file):
    """Generate HTML QC report"""
    
    # Calculate summary statistics
    total_reads = combined_data['count'].sum()
    unique_barcodes = len(combined_data)
    unique_variants = combined_data['mutation'].nunique()
    
    mapped_reads = combined_data[combined_data['mutation'] != 'UNMAPPED']['count'].sum()
    mapping_efficiency = (mapped_reads / total_reads) * 100
    
    mutation_type_counts = combined_data['mutation'].apply(classify_mutation_type).value_counts()
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Barcode-coupled DMS QC Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .metric {{ background-color: #e8f6f3; padding: 10px; margin: 10px 0; border-radius: 5px; }}
            .warning {{ background-color: #fdf2e9; border-left: 4px solid #f39c12; }}
            .success {{ background-color: #eafaf1; border-left: 4px solid #27ae60; }}
        </style>
    </head>
    <body>
        <h1>Barcode-coupled DMS QC Report</h1>
        
        <h2>Summary Statistics</h2>
        <div class="metric">
            <strong>Total Reads:</strong> {total_reads:,}<br>
            <strong>Unique Barcodes:</strong> {unique_barcodes:,}<br>
            <strong>Unique Variants:</strong> {unique_variants:,}<br>
            <strong>Mapping Efficiency:</strong> {mapping_efficiency:.1f}%
        </div>
        
        <h2>Sample Overview</h2>
        <table>
            <tr><th>Sample</th><th>Total Reads</th><th>Unique Variants</th><th>Top Variant</th></tr>
    """
    
    # Add sample statistics
    for sample in combined_data['sample'].unique():
        sample_data = combined_data[combined_data['sample'] == sample]
        sample_reads = sample_data['count'].sum()
        sample_variants = len(sample_data)
        top_variant = sample_data.loc[sample_data['count'].idxmax(), 'mutation']
        
        html_content += f"""
            <tr>
                <td>{sample}</td>
                <td>{sample_reads:,}</td>
                <td>{sample_variants:,}</td>
                <td>{top_variant}</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>Mutation Type Distribution</h2>
        <table>
            <tr><th>Mutation Type</th><th>Count</th><th>Percentage</th></tr>
    """
    
    # Add mutation type statistics
    for mut_type, count in mutation_type_counts.items():
        percentage = (count / unique_barcodes) * 100
        html_content += f"""
            <tr>
                <td>{mut_type}</td>
                <td>{count:,}</td>
                <td>{percentage:.1f}%</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>Quality Metrics</h2>
    """
    
    # Add quality assessments
    if mapping_efficiency > 80:
        html_content += '<div class="metric success"><strong>✓ Good mapping efficiency</strong></div>'
    elif mapping_efficiency > 60:
        html_content += '<div class="metric warning"><strong>⚠ Moderate mapping efficiency</strong></div>'
    else:
        html_content += '<div class="metric warning"><strong>✗ Low mapping efficiency - check barcode library quality</strong></div>'
    
    if unique_variants > 1000:
        html_content += '<div class="metric success"><strong>✓ Good variant diversity</strong></div>'
    else:
        html_content += '<div class="metric warning"><strong>⚠ Limited variant diversity</strong></div>'
    
    html_content += """
        <h2>Recommendations</h2>
        <ul>
            <li>Check barcode mapping efficiency - should be >80% for good quality libraries</li>
            <li>Verify mutation type distribution matches expectations</li>
            <li>Ensure adequate coverage for rare variants</li>
            <li>Consider filtering low-coverage barcodes in downstream analysis</li>
        </ul>
    </body>
    </html>
    """
    
    # Save HTML report
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    logger.info(f"HTML QC report saved to {output_file}")

if __name__ == "__main__":
    # Get parameters from Snakemake
    count_files = snakemake.input.barcode_counts
    barcode_map_file = snakemake.input.barcode_map
    output_file = snakemake.output.qc_report
    
    # Create output directory
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading barcode data...")
    combined_data, barcode_mapping = load_barcode_data(count_files, barcode_map_file)
    
    # Generate plots
    plot_file = output_file.replace('.html', '_plots.png')
    logger.info("Generating QC plots...")
    generate_barcode_qc_plots(combined_data, barcode_mapping, plot_file)
    
    # Generate HTML report
    logger.info("Generating HTML QC report...")
    generate_qc_html_report(combined_data, barcode_mapping, output_file)
    
    logger.info("Barcode QC report generation complete!")
