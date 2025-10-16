"""
Ollama client for AI-powered NGS pipeline orchestration
"""
import json
import re
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import ollama
import yaml
from datetime import datetime

# Set up logger
logger = logging.getLogger(__name__)


class OllamaOrchestrator:
    """AI orchestrator using Ollama for NGS pipeline automation"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the Ollama orchestrator"""
        self.config = self._load_config(config_path)
        self.model = self.config['ai']['model']
        self.client = ollama.Client()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def load_metadata_from_file(self, metadata_file: str) -> Dict:
        """
        Load metadata from CSV, TSV, or Excel file
        
        Args:
            metadata_file: Path to metadata file (.csv, .tsv, .xlsx)
            
        Returns:
            Dictionary with parsed metadata
        """
        try:
            import pandas as pd
            
            # Determine file format and load
            if metadata_file.endswith('.xlsx'):
                df = pd.read_excel(metadata_file)
            elif metadata_file.endswith('.tsv'):
                df = pd.read_csv(metadata_file, sep='\t')
            else:  # Default to CSV
                df = pd.read_csv(metadata_file)
            
            # Try to find filename columns with flexible naming
            filename1_col = None
            filename2_col = None
            
            for col in ['filename1', 'filename', 'file_name', 'sample_name']:
                if col in df.columns:
                    filename1_col = col
                    break
            
            for col in ['filename2', 'filename_r2', 'file_name_r2']:
                if col in df.columns:
                    filename2_col = col
                    break
            
            if not filename1_col:
                raise ValueError("No filename1 column found. Expected one of: filename1, filename, file_name, sample_name")
            
            # Map common column variations to standard names
            column_mapping = {
                'sample_name': ['sample_name', 'sample', 'library_ID', 'library_id', 'title'],
                'replication': ['replication', 'replicate', 'rep'],
                'library_layout': ['library_layout', 'layout', 'paired'],
                'sequencing_platform': ['sequencing_platform', 'platform', 'instrument_model'],
                'library_strategy': ['library_strategy', 'strategy', 'method'],
                'condition': ['condition', 'design_description', 'description', 'treatment']
            }
            
            # Create standardized column mapping
            std_columns = {}
            for std_name, possible_names in column_mapping.items():
                for possible_name in possible_names:
                    if possible_name in df.columns:
                        std_columns[std_name] = possible_name
                        break
            
            # Convert to structured metadata
            metadata = {
                'experiment_type': 'deep_mutational_scanning',
                'samples': {},
                'file_mapping': {}
            }
            
            for _, row in df.iterrows():
                # Use flexible column mapping
                sample_name = str(row[std_columns.get('sample_name', filename1_col)])
                replication = int(row[std_columns.get('replication', 'replication')]) if pd.notna(row.get(std_columns.get('replication', 'replication'))) else 1
                
                # Get other metadata with fallbacks
                library_layout = row.get(std_columns.get('library_layout'), 'single')
                sequencing_platform = row.get(std_columns.get('sequencing_platform'), 'unknown')
                library_strategy = row.get(std_columns.get('library_strategy'), 'unknown')
                condition_desc = row.get(std_columns.get('condition'), str(row[std_columns.get('sample_name', filename1_col)]))
                
                # Create sample entry
                if sample_name not in metadata['samples']:
                    metadata['samples'][sample_name] = {
                        'replication': replication,
                        'library_layout': library_layout,
                        'sequencing_platform': sequencing_platform,
                        'library_strategy': library_strategy,
                        'files': []
                    }
                
                # Process R1 file
                filename1 = str(row[filename1_col])
                if not filename1.endswith('.fastq.gz') and not filename1.endswith('.fq.gz'):
                    filename1 = filename1 + '.fastq.gz'  # Add extension if missing
                
                # Add R1 file mapping
                metadata['file_mapping'][filename1] = {
                    'sample_name': sample_name,
                    'replication': replication,
                    'library_layout': library_layout,
                    'sequencing_platform': sequencing_platform,
                    'library_strategy': library_strategy,
                    'read_type': 'R1',
                    'condition': self._extract_condition_from_description(condition_desc),
                    'is_paired': library_layout == 'paired'
                }
                metadata['samples'][sample_name]['files'].append(filename1)
                
                # Process R2 file if it exists and is paired-end
                if filename2_col and library_layout == 'paired' and pd.notna(row[filename2_col]):
                    filename2 = str(row[filename2_col])
                    if not filename2.endswith('.fastq.gz') and not filename2.endswith('.fq.gz'):
                        filename2 = filename2 + '.fastq.gz'  # Add extension if missing
                    
                    # Add R2 file mapping
                    metadata['file_mapping'][filename2] = {
                        'sample_name': sample_name,
                        'replication': replication,
                        'library_layout': library_layout,
                        'sequencing_platform': sequencing_platform,
                        'library_strategy': library_strategy,
                        'read_type': 'R2',
                        'condition': self._extract_condition_from_description(condition_desc),
                        'is_paired': library_layout == 'paired'
                    }
                    metadata['samples'][sample_name]['files'].append(filename2)
            
            return metadata
            
        except Exception as e:
            print(f"Error loading metadata file: {e}")
            raise
    
    def _extract_condition_from_description(self, description: str) -> str:
        """Use AI to extract condition from design description"""
        
        # First try rule-based detection for common patterns
        desc_lower = description.lower()
        
        # Check for barcode-coupled DMS mapping samples (long-read)
        if any(keyword in desc_lower for keyword in ['variant mapping', 'long-read', 'pacbio', 'nanopore', 'mapping']):
            return 'mapping'
        
        # Check for output/post-selection samples first (more specific)
        if any(keyword in desc_lower for keyword in ['post_selection_sample', 'post-selection', 'output', 'selected', 'enriched', 'rescue', 't1', 't2', 'after']):
            return 'output'
        
        # Check for input/pre-selection samples
        if any(keyword in desc_lower for keyword in ['pre_selection_sample', 'pre-selection', 'input', 'library', 'plasmid', 't0', 'before']):
            return 'input'
        
        # Check for control samples (no-antibody, VSVG, etc.)
        if any(keyword in desc_lower for keyword in ['no-antibody', 'no_antibody', 'vsvg', 'control']):
            # Determine if it's input or output control based on other context
            if 'vsvg' in desc_lower:
                return 'output'  # VSVG is typically the selection condition
            else:
                return 'input'   # no-antibody is typically the input control
        
        # Fallback to AI-based extraction
        prompt = f"""
        Analyze this experimental description for a Deep Mutational Scanning experiment and determine the experimental condition type:
        
        Description: "{description}"
        
        Based on this description, classify it as one of these condition types:
        - "mapping": Long-read sequencing data used for barcode-to-variant mapping (PacBio, Nanopore, etc.)
        - "input": Input/reference library, plasmid library, pre-selection samples, no-antibody controls
        - "output": Output/selected samples, rescued variants, enriched samples, post-selection samples, antibody selections
        - "control": Control samples, mock treatments, negative controls
        - "unknown": If the condition cannot be determined
        
        Respond with ONLY the condition type (mapping, input, output, control, or unknown).
        """
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            condition = response['message']['content'].strip().lower()
            
            # Validate response
            valid_conditions = ['input', 'output', 'control', 'unknown']
            if condition in valid_conditions:
                return condition
            else:
                # Fallback to rule-based if AI response is invalid
                return self._fallback_extract_condition(description)
                
        except Exception as e:
            print(f"AI condition extraction failed: {e}")
            return self._fallback_extract_condition(description)
    
    def _fallback_extract_condition(self, description: str) -> str:
        """Fallback rule-based condition extraction"""
        description_lower = description.lower()
        
        # Common condition patterns for DMS - check more specific patterns first
        if any(keyword in description_lower for keyword in ['output', 'rescue', 'selected', 'enriched']):
            return 'output'
        elif any(keyword in description_lower for keyword in ['input', 'plasmid', 'library', 'reference']):
            return 'input'
        elif any(keyword in description_lower for keyword in ['control', 'mock', 'negative']):
            return 'control'
        else:
            return 'unknown'
    


    def detect_and_validate_metadata_from_table(self, file_paths: List[str], metadata_file: str) -> Dict[str, Dict]:
        """
        Use AI to detect, validate, and assign metadata based on tabular metadata file
        
        Args:
            file_paths: List of FASTQ file paths
            metadata_file: Path to CSV/TSV/Excel metadata file
            
        Returns:
            Dictionary with validated and assigned metadata for each file
        """
        print("🤖 Using AI to analyze metadata and match files...")
        
        # Load metadata from table
        table_metadata = self.load_metadata_from_file(metadata_file)
        
        validated_metadata = {}
        unmatched_files = []
        
        for filepath in file_paths:
            filename = os.path.basename(filepath)
            
            # Try exact filename match first
            if filename in table_metadata['file_mapping']:
                validated_metadata[filepath] = table_metadata['file_mapping'][filename].copy()
                print(f"  ✅ Exact match: {filename}")
            else:
                # Try AI-powered intelligent matching
                matched_metadata = self._ai_intelligent_file_match(filename, table_metadata['file_mapping'])
                if matched_metadata:
                    validated_metadata[filepath] = matched_metadata
                    print(f"  🧠 AI matched: {filename}")
                else:
                    # Try fuzzy matching as fallback
                    matched = False
                    for table_filename, file_meta in table_metadata['file_mapping'].items():
                        if self._fuzzy_filename_match(filename, table_filename):
                            validated_metadata[filepath] = file_meta.copy()
                            matched = True
                            print(f"  🔍 Fuzzy matched: {filename}")
                            break
                    
                    if not matched:
                        unmatched_files.append(filepath)
                        print(f"  ❌ No match: {filename}")
        
        if unmatched_files:
            print(f"❌ Error: Could not match {len(unmatched_files)} files to metadata:")
            for f in unmatched_files:
                print(f"  - {os.path.basename(f)}")
            raise ValueError(f"All files must be matched to metadata. Unmatched files: {unmatched_files}")
        
        return validated_metadata
    
    def _ai_intelligent_file_match(self, actual_filename: str, file_mapping: Dict) -> Optional[Dict]:
        """Use AI to intelligently match files to metadata entries"""
        
        # Create a list of available filenames from metadata
        available_files = list(file_mapping.keys())
        
        prompt = f"""
        You are helping match actual FASTQ filenames to metadata entries. 
        
        Actual filename to match: "{actual_filename}"
        
        Available filenames in metadata:
        {chr(10).join([f'- {f}' for f in available_files])}
        
        Your task:
        1. Find the best match for the actual filename from the available options
        2. Consider that sequencer output often has additional identifiers, barcodes, lane numbers
        3. Focus on core sample identifiers, read type (R1/R2), and file extensions
        4. The files might have different naming conventions but represent the same sample
        
        Examples of matches:
        - "Sample4_TGACCAAT_L001_R1_001.fastq.gz" matches "Sample4_R1.fastq.gz"
        - "NEP_input1_rep1_read1.fq.gz" matches "NEP_input1_R1.fastq.gz"
        
        If you find a good match, respond with ONLY the matching filename from the list.
        If no good match exists, respond with "NO_MATCH".
        """
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            matched_filename = response['message']['content'].strip()
            
            # Validate that the response is one of the available files
            if matched_filename in file_mapping:
                return file_mapping[matched_filename].copy()
            elif matched_filename == "NO_MATCH":
                return None
            else:
                # AI returned invalid response, fallback to None
                return None
                
        except Exception as e:
            print(f"  ⚠️  AI file matching failed: {e}")
            return None

    def _fuzzy_filename_match(self, actual_filename: str, table_filename: str) -> bool:
        """Check if filenames match with some flexibility"""
        import re
        
        # Remove common suffixes and extensions
        actual_clean = re.sub(r'\.(fastq|fq)(\.gz)?$', '', actual_filename, flags=re.IGNORECASE)
        table_clean = re.sub(r'\.(fastq|fq)(\.gz)?$', '', table_filename, flags=re.IGNORECASE)
        
        # Check various matching strategies
        strategies = [
            # Exact match
            actual_clean.lower() == table_clean.lower(),
            # Table filename is substring of actual
            table_clean.lower() in actual_clean.lower(),
            # Actual filename is substring of table
            actual_clean.lower() in table_clean.lower(),
            # Remove underscores and compare
            actual_clean.replace('_', '').lower() == table_clean.replace('_', '').lower()
        ]
        
        return any(strategies)

    def detect_and_validate_metadata(self, file_paths: List[str], metadata_file: str) -> Dict[str, Dict]:
        """
        Detect, validate, and assign metadata from tabular metadata file
        This is now the main metadata detection method
        
        Args:
            file_paths: List of FASTQ file paths
            metadata_file: Path to CSV/TSV/Excel metadata file
            
        Returns:
            Dictionary with validated and assigned metadata for each file
        """
        return self.detect_and_validate_metadata_from_table(file_paths, metadata_file)
    

    
    # Basic metadata creation method removed - metadata is always required
    

    
    def clean_filenames_from_table_metadata(self, file_paths: List[str], file_metadata: Dict[str, Dict], output_dir: str = "data/processed") -> Dict[str, str]:
        """
        Generate clean, standardized filenames based on tabular metadata
        
        Args:
            file_paths: Original file paths
            file_metadata: File metadata from table (from detect_and_validate_metadata_from_table)
            output_dir: Directory for cleaned files
            
        Returns:
            Dictionary mapping original paths to new paths
        """
        cleaned_paths = {}
        
        for original_path in file_paths:
            meta = file_metadata.get(original_path, {})
            
            # Generate standardized filename based on DMS experiment structure
            sample_name = meta.get('sample_name', 'unknown')
            condition = meta.get('condition', 'unknown')
            replication = meta.get('replication', 1)
            read_type = meta.get('read_type', 'single')
            
            # Clean sample name and condition
            sample_name = re.sub(r'[^a-zA-Z0-9]', '_', sample_name)
            condition = re.sub(r'[^a-zA-Z0-9]', '_', condition)
            
            # Build new filename: samplename_condition_rep#_readtype
            parts = [sample_name, condition]
            
            if replication:
                parts.append(f"rep{replication}")
                
            if read_type != 'single':
                parts.append(read_type)
            
            new_filename = "_".join(parts) + ".fastq.gz"
            new_path = os.path.join(output_dir, new_filename)
            cleaned_paths[original_path] = new_path
            
        return cleaned_paths

    # Basic filename cleaning method removed - metadata is always required
    
    def configure_pipeline_from_table(self, file_paths: List[str], metadata_file: str, reference_genome: Optional[str] = None) -> Dict:
        """
        Configure pipeline based on tabular metadata file
        
        Args:
            file_paths: Input FASTQ files
            metadata_file: Path to CSV/TSV/Excel metadata file
            reference_genome: Optional reference genome path
            
        Returns:
            Pipeline configuration dictionary
        """
        # Load and validate metadata from table
        file_metadata = self.detect_and_validate_metadata_from_table(file_paths, metadata_file)
        
        # Determine if paired-end
        is_paired = any(meta.get('is_paired', False) for meta in file_metadata.values())
        
        # Group samples by condition and replicate
        conditions = {}
        for filepath, meta in file_metadata.items():
            condition = meta.get('condition', 'unknown')
            replicate = meta.get('replication', 1)  # Note: using 'replication' from table
            
            if condition not in conditions:
                conditions[condition] = {}
                
            if replicate not in conditions[condition]:
                conditions[condition][replicate] = {
                    'files': [],
                    'metadata': meta
                }
            
            conditions[condition][replicate]['files'].append(filepath)
        
        # Auto-detect DMS pipeline type
        dms_pipeline_type = self._detect_dms_pipeline_type(file_metadata, file_paths)
        
        # Generate pipeline config optimized for DMS
        pipeline_config = {
            'conditions': conditions,
            'is_paired_end': is_paired,
            'experiment_type': 'deep_mutational_scanning',
            'dms_pipeline_type': dms_pipeline_type,
            'reference_genome': reference_genome,
            'pipeline_type': 'deep_mutational_scanning',
            'fitness_calculation': {
                'input_condition': self._identify_input_condition(conditions),
                'output_conditions': self._identify_output_conditions(conditions),
                'replicates': self._count_replicates(conditions)
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return pipeline_config
    
    def _detect_dms_pipeline_type(self, file_metadata: Dict, file_paths: List[str]) -> str:
        """
        Auto-detect DMS pipeline type based on metadata and file characteristics
        
        Returns:
            'direct_amplicon' or 'barcode_coupled'
        """
        # Check metadata for explicit pipeline type
        for filepath, meta in file_metadata.items():
            # Look for explicit pipeline type in metadata
            if 'pipeline_type' in meta:
                return meta['pipeline_type']
            if 'dms_type' in meta:
                return meta['dms_type']
            if 'barcode' in str(meta).lower():
                return 'barcode_coupled'
        
        # Check for mixed platform types (strong indicator of barcode-coupled)
        platforms = set()
        library_strategies = set()
        for filepath, meta in file_metadata.items():
            platform = meta.get('sequencing_platform', meta.get('platform', '')).upper()
            strategy = meta.get('library_strategy', '').upper()
            platforms.add(platform)
            library_strategies.add(strategy)
        
        # If we have both PacBio/Nanopore AND Illumina, it's likely barcode-coupled
        has_long_read = any(p in platforms for p in ['PACBIO', 'NANOPORE', 'ONT'])
        has_short_read = 'ILLUMINA' in platforms
        has_synthetic_long_read = 'SYNTHETIC-LONG-READ' in library_strategies
        
        if (has_long_read and has_short_read) or has_synthetic_long_read:
            logger.info("Detected mixed platform data - likely barcode-coupled DMS")
            return 'barcode_coupled'
        
        # Analyze file characteristics using AI
        detection_prompt = f"""
        Analyze these NGS files and metadata to determine the DMS pipeline type:
        
        Files: {[os.path.basename(f) for f in file_paths]}
        
        Metadata summary:
        {self._summarize_metadata_for_detection(file_metadata)}
        
        Determine if this is:
        1. "direct_amplicon" - Direct amplicon sequencing for variant calling
        2. "barcode_coupled" - Barcode-coupled DMS with long-read barcode→variant mapping
        
        Look for indicators like:
        - Long-read data (PacBio, Oxford Nanopore) → barcode_coupled
        - Barcode mentions in metadata → barcode_coupled  
        - Short amplicon sequencing → direct_amplicon
        - Mixed long/short read data → barcode_coupled
        
        Respond with ONLY: "direct_amplicon" or "barcode_coupled"
        """
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": detection_prompt}],
                options={"temperature": 0.1}
            )
            
            detected_type = response['message']['content'].strip().lower()
            if detected_type in ['direct_amplicon', 'barcode_coupled']:
                logger.info(f"AI detected DMS pipeline type: {detected_type}")
                return detected_type
            else:
                logger.warning(f"AI returned unexpected pipeline type: {detected_type}, defaulting to direct_amplicon")
                return 'direct_amplicon'
                
        except Exception as e:
            logger.error(f"Failed to detect DMS pipeline type: {e}")
            # Default to direct amplicon if detection fails
            return 'direct_amplicon'
    
    def _summarize_metadata_for_detection(self, file_metadata: Dict) -> str:
        """Create a summary of metadata for pipeline type detection"""
        summary_parts = []
        
        for filepath, meta in file_metadata.items():
            filename = os.path.basename(filepath)
            condition = meta.get('condition', 'unknown')
            sequencing_type = meta.get('sequencing_platform', meta.get('platform', 'unknown'))
            library_type = meta.get('library_layout', meta.get('layout', 'unknown'))
            
            summary_parts.append(f"File: {filename}, Condition: {condition}, Platform: {sequencing_type}, Layout: {library_type}")
        
        return "\n".join(summary_parts)
    
    def _identify_input_condition(self, conditions: Dict) -> str:
        """Identify the input/control condition for fitness calculation"""
        # Look for common input condition names
        input_keywords = ['input', 'plasmid', 'library', 'control', 'reference', 't0', 'before']
        
        for condition_name in conditions.keys():
            if any(keyword in condition_name.lower() for keyword in input_keywords):
                return condition_name
                
        # If no clear input found, return the first condition
        return list(conditions.keys())[0] if conditions else 'unknown'
    
    def _identify_output_conditions(self, conditions: Dict) -> List[str]:
        """Identify output/selected conditions for fitness calculation"""
        input_condition = self._identify_input_condition(conditions)
        return [cond for cond in conditions.keys() if cond != input_condition]
    
    def _count_replicates(self, conditions: Dict) -> Dict[str, int]:
        """Count replicates for each condition"""
        replicate_counts = {}
        for condition, replicates in conditions.items():
            replicate_counts[condition] = len(replicates)
        return replicate_counts
    
    # Basic pipeline configuration method removed - metadata is always required
    
    def generate_report_insights(self, results_data: Dict) -> str:
        """
        Generate AI-powered insights for the analysis report
        
        Args:
            results_data: Dictionary containing analysis results
            
        Returns:
            Generated report text with insights
        """
        prompt = f"""
        Analyze the following Deep Mutational Scanning results and provide scientific insights:
        
        Results summary:
        - Total variants analyzed: {results_data.get('total_variants', 'N/A')}
        - Significant variants: {results_data.get('significant_variants', 'N/A')}
        - Fitness score range: {results_data.get('fitness_range', 'N/A')}
        
        Please provide:
        1. A brief summary of the key findings
        2. Identification of hotspot regions or amino acids with strong effects
        3. Potential biological implications
        4. Recommendations for follow-up experiments
        
        Keep the analysis scientific but accessible.
        """
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response['message']['content']
        except Exception as e:
            return f"AI report generation failed: {e}"
