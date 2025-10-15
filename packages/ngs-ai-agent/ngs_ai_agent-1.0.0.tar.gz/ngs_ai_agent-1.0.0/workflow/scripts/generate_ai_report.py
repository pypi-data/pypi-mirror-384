#!/usr/bin/env python3
"""
AI Report Generator for Deep Mutational Scanning
Uses Ollama to analyze fitness data and generate scientific insights
"""

import pandas as pd
import numpy as np
import os
import sys
import logging
from pathlib import Path
import requests
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIReportGenerator:
    """Generate AI-powered reports for DMS analysis"""
    
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "qwen3-coder:latest"
    
    def generate_report(self, fitness_file, heatmap_file, output_file):
        """Generate comprehensive AI report"""
        logger.info("Generating AI-powered DMS report...")
        
        # Load and analyze fitness data
        fitness_data = self._load_fitness_data(fitness_file)
        if fitness_data is None:
            logger.error("Failed to load fitness data")
            return
        
        # Generate AI insights
        insights = self._generate_ai_insights(fitness_data)
        
        # Create HTML report
        self._create_html_report(fitness_data, insights, heatmap_file, output_file)
        
        logger.info(f"AI report generated: {output_file}")
    
    def _load_fitness_data(self, fitness_file):
        """Load and analyze fitness data"""
        try:
            df = pd.read_csv(fitness_file)
            logger.info(f"Loaded fitness data: {len(df)} variants")
            
            # Basic statistics
            stats = {
                'total_variants': len(df),
                'fitness_range': f"{df['fitness_score'].min():.3f} to {df['fitness_score'].max():.3f}",
                'mean_fitness': f"{df['fitness_score'].mean():.3f}",
                'std_fitness': f"{df['fitness_score'].std():.3f}",
                'wild_type_count': len(df[df['mutation'] == 'WT']),
                # Updated mutation type classification
                'missense_mutations': len(df[df['type'] == 'missense']),
                'synonymous_mutations': len(df[df['type'] == 'synonymous']),
                'nonsense_mutations': len(df[df['type'] == 'nonsense']),
                'deletion_mutations': len(df[df['type'] == 'deletion']),
                'insertion_mutations': len(df[df['type'] == 'insertion']),
                # Legacy support for older data
                'single_mutations': len(df[df['type'].isin(['single_mutation', 'missense', 'synonymous', 'nonsense', 'deletion', 'insertion'])]),
                'multi_mutations': len(df[df['type'].isin(['multi_mutation', 'multi_mutation_haplotype'])]),
                # Fitness impact classification
                'deleterious_count': len(df[df['fitness_score'] < -0.5]),
                'beneficial_count': len(df[df['fitness_score'] > 0.5]),
                'neutral_count': len(df[(df['fitness_score'] >= -0.5) & (df['fitness_score'] <= 0.5)])
            }
            
            # Top variants by fitness
            top_beneficial = df[df['fitness_score'] > 0].nlargest(5, 'fitness_score')
            top_deleterious = df[df['fitness_score'] < 0].nsmallest(5, 'fitness_score')
            
            # Mutation type fitness analysis
            mutation_type_stats = self._analyze_mutation_type_fitness(df)
            
            return {
                'dataframe': df,
                'statistics': stats,
                'top_beneficial': top_beneficial,
                'top_deleterious': top_deleterious,
                'mutation_type_fitness': mutation_type_stats
            }
            
        except Exception as e:
            logger.error(f"Error loading fitness data: {e}")
            return None
    
    def _analyze_mutation_type_fitness(self, df):
        """Analyze fitness statistics by mutation type"""
        mutation_types = ['missense', 'synonymous', 'nonsense', 'deletion', 'insertion', 'wild_type']
        type_stats = {}
        
        for mut_type in mutation_types:
            if mut_type == 'wild_type':
                subset = df[df['mutation'] == 'WT']
            else:
                subset = df[df['type'] == mut_type]
            
            if len(subset) > 0:
                type_stats[mut_type] = {
                    'count': len(subset),
                    'mean_fitness': subset['fitness_score'].mean(),
                    'std_fitness': subset['fitness_score'].std(),
                    'min_fitness': subset['fitness_score'].min(),
                    'max_fitness': subset['fitness_score'].max(),
                    'median_fitness': subset['fitness_score'].median()
                }
            else:
                type_stats[mut_type] = {
                    'count': 0,
                    'mean_fitness': 0,
                    'std_fitness': 0,
                    'min_fitness': 0,
                    'max_fitness': 0,
                    'median_fitness': 0
                }
        
        return type_stats
    
    def _generate_ai_insights(self, fitness_data):
        """Generate AI insights using Ollama"""
        try:
            # Prepare data summary for AI analysis
            data_summary = self._prepare_data_summary(fitness_data)
            
            # Create prompt for AI analysis
            prompt = self._create_analysis_prompt(data_summary)
            
            # Get AI insights
            insights = self._query_ollama(prompt)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return self._generate_fallback_insights(fitness_data)
    
    def _prepare_data_summary(self, fitness_data):
        """Prepare data summary for AI analysis"""
        df = fitness_data['dataframe']
        stats = fitness_data['statistics']
        
        summary = f"""
Deep Mutational Scanning (DMS) Analysis Summary:

Dataset Overview:
- Total variants analyzed: {stats['total_variants']}
- Fitness score range: {stats['fitness_range']}
- Mean fitness: {stats['mean_fitness']} ± {stats['std_fitness']}

Detailed Mutation Type Analysis:
- Wild type variants: {stats['wild_type_count']}
- Missense mutations (amino acid changes): {stats['missense_mutations']}
- Synonymous mutations (silent, no AA change): {stats['synonymous_mutations']}
- Nonsense mutations (stop codons): {stats['nonsense_mutations']}
- Deletion mutations: {stats['deletion_mutations']}
- Insertion mutations: {stats['insertion_mutations']}
- Multi-mutation haplotypes: {stats['multi_mutations']}

Fitness Impact Classification:
- Deleterious variants (fitness < -0.5): {stats['deleterious_count']}
- Neutral variants (-0.5 ≤ fitness ≤ 0.5): {stats['neutral_count']}
- Beneficial variants (fitness > 0.5): {stats['beneficial_count']}

Top Beneficial Variants:
{self._format_top_variants(fitness_data['top_beneficial'])}

Top Deleterious Variants:
{self._format_top_variants(fitness_data['top_deleterious'])}

Fitness by Mutation Type:
{self._format_mutation_type_fitness(fitness_data['mutation_type_fitness'])}

Please provide a comprehensive scientific analysis of these DMS results, including:
1. Overall fitness landscape interpretation with attention to different mutation types
2. Key biological insights, particularly regarding synonymous vs missense effects
3. Analysis of indel (insertion/deletion) impacts on protein function
4. Potential functional implications of the mutation spectrum
5. Recommendations for follow-up experiments
6. Quality assessment considering the mutation type distribution
"""
        return summary
    
    def _format_top_variants(self, variants_df):
        """Format top variants for display"""
        if variants_df.empty:
            return "None found"
        
        formatted = []
        for _, row in variants_df.iterrows():
            formatted.append(f"- {row['mutation']}: fitness = {row['fitness_score']:.3f}")
        
        return "\n".join(formatted)
    
    def _format_mutation_type_fitness(self, type_stats):
        """Format mutation type fitness statistics"""
        formatted = []
        for mut_type, stats in type_stats.items():
            if stats['count'] > 0:
                formatted.append(
                    f"- {mut_type.title()}: {stats['count']} variants, "
                    f"mean fitness = {stats['mean_fitness']:.3f} ± {stats['std_fitness']:.3f}, "
                    f"range = {stats['min_fitness']:.3f} to {stats['max_fitness']:.3f}"
                )
            else:
                formatted.append(f"- {mut_type.title()}: No variants found")
        
        return "\n".join(formatted)
    
    def _create_analysis_prompt(self, data_summary):
        """Create prompt for AI analysis"""
        return f"""
You are a computational biologist specializing in Deep Mutational Scanning (DMS) analysis. 
Please analyze the following DMS dataset and provide comprehensive scientific insights.

{data_summary}

Please provide a detailed analysis that includes:

1. **Executive Summary**: Brief overview of key findings
2. **Data Quality Assessment**: Evaluation of experimental design and data quality
3. **Fitness Landscape Analysis**: Interpretation of the overall fitness distribution
4. **Biological Insights**: Key functional implications and biological significance
5. **Variant Classification**: Analysis of beneficial, neutral, and deleterious variants
6. **Experimental Recommendations**: Suggestions for follow-up experiments
7. **Limitations and Caveats**: Discussion of experimental limitations

Format your response in clear, scientific language suitable for a research report.
"""
    
    def _query_ollama(self, prompt):
        """Query Ollama for AI insights"""
        try:
            logger.info("Attempting to connect to Ollama...")
            
            # Check if Ollama is running
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                logger.info(f"Ollama connection test: {response.status_code}")
                
                if response.status_code != 200:
                    logger.warning(f"Ollama not accessible (status: {response.status_code}), using fallback analysis")
                    return None
                    
            except requests.exceptions.ConnectionError:
                logger.warning("Cannot connect to Ollama server. Is it running?")
                return None
            except Exception as e:
                logger.warning(f"Error testing Ollama connection: {e}")
                return None
            
            # Check if the model is available
            try:
                model_response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                if model_response.status_code == 200:
                    models = model_response.json().get('models', [])
                    model_names = [m.get('name', '') for m in models]
                    logger.info(f"Available Ollama models: {model_names}")
                    
                    if self.model not in model_names:
                        logger.warning(f"Model {self.model} not found. Available: {model_names}")
                        # Try to use the first available model
                        if model_names:
                            self.model = model_names[0]
                            logger.info(f"Using available model: {self.model}")
                        else:
                            logger.warning("No models available, using fallback analysis")
                            return None
                else:
                    logger.warning(f"Could not check available models: {model_response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Error checking available models: {e}")
            
            logger.info(f"Querying Ollama model: {self.model}")
            
            # Query the model
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            logger.info("Sending request to Ollama...")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            logger.info(f"Ollama response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', 'No response from AI model')
                logger.info(f"AI response length: {len(ai_response)} characters")
                return ai_response
            else:
                logger.warning(f"Ollama query failed: {response.status_code}")
                logger.warning(f"Response content: {response.text}")
                return None
                
        except Exception as e:
            logger.warning(f"Error querying Ollama: {e}")
            return None
    
    def _generate_fallback_insights(self, fitness_data):
        """Generate fallback insights when AI is not available"""
        stats = fitness_data['statistics']
        
        insights = f"""
**Fallback Analysis (AI Model Unavailable)**

**Executive Summary:**
This Deep Mutational Scanning analysis examined {stats['total_variants']} variants, 
revealing a fitness landscape ranging from {stats['fitness_range']}.

**Key Findings:**
- **Fitness Distribution**: The mean fitness score is {stats['mean_fitness']} ± {stats['std_fitness']}
- **Variant Impact**: {stats['deleterious_count']} variants show deleterious effects, 
  {stats['beneficial_count']} show beneficial effects, and {stats['neutral_count']} are neutral
- **Mutation Types**: {stats['single_mutations']} single mutations and {stats['multi_mutations']} multi-mutations analyzed

**Biological Interpretation:**
The fitness distribution suggests a protein that is relatively tolerant to mutations, 
with most variants showing moderate fitness effects. The presence of beneficial variants 
indicates potential for protein engineering and optimization.

**Recommendations:**
1. Focus follow-up studies on variants with extreme fitness scores
2. Investigate the structural basis of beneficial mutations
3. Validate deleterious variants through functional assays
4. Consider epistatic interactions in multi-mutation variants

**Data Quality:**
The dataset includes {stats['wild_type_count']} wild-type controls, providing 
a robust baseline for fitness calculations. The fitness score distribution appears 
reasonable for DMS experiments.
"""
        return insights
    
    def _create_html_report(self, fitness_data, insights, heatmap_file, output_file):
        """Create comprehensive HTML report"""
        stats = fitness_data['statistics']
        
        # Create output directory
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NGS AI Agent - Deep Mutational Scanning Report</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 40px; 
            line-height: 1.6;
            color: #333;
        }}
        .header {{ 
            color: #2c3e50; 
            border-bottom: 3px solid #3498db; 
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .section {{ 
            margin: 30px 0; 
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .insights {{ 
            background-color: #e8f4fd; 
            padding: 25px; 
            border-radius: 8px; 
            border: 1px solid #b3d9f2;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #ddd;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            color: #666;
            margin-top: 10px;
        }}
        .top-variants {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .variant-item {{
            padding: 8px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 3px solid #3498db;
        }}
        .beneficial {{ border-left-color: #27ae60; }}
        .deleterious {{ border-left-color: #e74c3c; }}
        .files-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .file-link {{
            display: inline-block;
            padding: 10px 20px;
            margin: 10px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        .file-link:hover {{
            background: #2980b9;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧬 Deep Mutational Scanning Analysis Report</h1>
        <p><strong>Generated by NGS AI Agent</strong> | Comprehensive DMS Analysis</p>
    </div>
    
    <div class="section">
        <h2>📊 Dataset Overview</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_variants']}</div>
                <div class="stat-label">Total Variants</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['fitness_range']}</div>
                <div class="stat-label">Fitness Range</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['mean_fitness']}</div>
                <div class="stat-label">Mean Fitness</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['std_fitness']}</div>
                <div class="stat-label">Std Dev</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>🔬 Detailed Mutation Analysis</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['missense_mutations']}</div>
                <div class="stat-label">Missense<br><small>(AA changes)</small></div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['synonymous_mutations']}</div>
                <div class="stat-label">Synonymous<br><small>(silent)</small></div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['nonsense_mutations']}</div>
                <div class="stat-label">Nonsense<br><small>(stop codons)</small></div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['deletion_mutations']}</div>
                <div class="stat-label">Deletions<br><small>(indels)</small></div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['insertion_mutations']}</div>
                <div class="stat-label">Insertions<br><small>(indels)</small></div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['multi_mutations']}</div>
                <div class="stat-label">Multi-Mutations<br><small>(haplotypes)</small></div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['wild_type_count']}</div>
                <div class="stat-label">Wild Type<br><small>(reference)</small></div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Fitness Impact Distribution</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['deleterious_count']}</div>
                <div class="stat-label">Deleterious</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['neutral_count']}</div>
                <div class="stat-label">Neutral</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['beneficial_count']}</div>
                <div class="stat-label">Beneficial</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>🏆 Top Variants</h2>
        <div class="top-variants">
            <h3>Most Beneficial Variants</h3>
            {self._format_html_variants(fitness_data['top_beneficial'], 'beneficial')}
            
            <h3>Most Deleterious Variants</h3>
            {self._format_html_variants(fitness_data['top_deleterious'], 'deleterious')}
        </div>
    </div>
    
    <div class="section">
        <h2>🤖 AI-Generated Insights</h2>
        <div class="insights">{insights}</div>
    </div>
    
    <div class="section">
        <h2>📁 Analysis Files</h2>
        <div class="files-section">
            <a href="../dms/fitness_scores.csv" class="file-link">📊 Fitness Scores (CSV)</a>
            <a href="../visualization/dms_heatmap.png" class="file-link">🔥 Mutational Effects Heatmap</a>
            <a href="../visualization/dms_heatmap.html" class="file-link">🌐 Interactive Heatmap</a>
        </div>
    </div>
    
    <div class="section">
        <h2>📝 Report Information</h2>
        <p><strong>Generated:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Pipeline:</strong> NGS AI Agent v1.0</strong></p>
        <p><strong>Analysis Type:</strong> Deep Mutational Scanning (DMS)</strong></p>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html_content)
    
    def _format_html_variants(self, variants_df, variant_type):
        """Format variants for HTML display"""
        if variants_df.empty:
            return "<p>None found</p>"
        
        html = ""
        for _, row in variants_df.iterrows():
            html += f'<div class="variant-item {variant_type}">'
            html += f'<strong>{row["mutation"]}</strong>: fitness = {row["fitness_score"]:.3f}'
            html += '</div>'
        
        return html


def main():
    """Main function for Snakemake script execution"""
    try:
        # Snakemake variables
        fitness_file = snakemake.input.fitness_scores
        heatmap_file = snakemake.input.heatmap
        output_file = snakemake.output.report
        
        logger.info(f"Starting AI report generation...")
        logger.info(f"Fitness file: {fitness_file}")
        logger.info(f"Heatmap file: {heatmap_file}")
        logger.info(f"Output file: {output_file}")
        
        # Validate inputs
        if not os.path.exists(fitness_file):
            raise FileNotFoundError(f"Fitness file not found: {fitness_file}")
        
        if not os.path.exists(heatmap_file):
            logger.warning(f"Heatmap file not found: {heatmap_file}")
        
        # Create report generator
        generator = AIReportGenerator()
        
        # Generate report
        generator.generate_report(fitness_file, heatmap_file, output_file)
        
        logger.info("AI report generation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        # Create a simple error report
        error_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Error - AI Report Generation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; color: #e74c3c; }}
        .error {{ background-color: #fdf2f2; padding: 20px; border: 2px solid #e74c3c; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>❌ AI Report Generation Failed</h1>
    <div class="error">
        <h2>Error Details:</h2>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><strong>Time:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Please check the pipeline logs for more details.</p>
    </div>
</body>
</html>
"""
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Write error report
        with open(output_file, 'w') as f:
            f.write(error_html)
        
        # Re-raise the exception for Snakemake to handle
        raise


if __name__ == "__main__":
    main()
