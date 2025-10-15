#!/usr/bin/env python3
"""
NGS AI Agent - Main CLI Interface
AI-powered automated NGS analysis pipeline
"""

import os
import sys
import argparse
import logging
from typing import List, Optional

from .core import NGSAIAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="NGS AI Agent - AI-powered automated NGS analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set up environment
  ngs-ai-agent setup

  # Run analysis with CSV metadata (recommended)
  ngs-ai-agent run --input-dir /path/to/fastq/files --reference /path/to/ref.fasta --metadata experiment.csv

  # Run with Excel metadata
  ngs-ai-agent run --input-dir /path/to/fastq/files --reference /path/to/ref.fasta --metadata experiment.xlsx

  # Dry run to check pipeline
  ngs-ai-agent run --input-dir /path/to/fastq/files --metadata experiment.csv --dry-run

  # Run with specific cores
  ngs-ai-agent run --input-dir /path/to/fastq/files --metadata experiment.csv --cores 16

  # High-performance run with many cores
  ngs-ai-agent run --input-dir /path/to/fastq/files --reference /path/to/ref.fasta --metadata experiment.csv --cores 32
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up conda environment')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run NGS analysis pipeline')
    
    # Arguments for run command
    run_parser.add_argument('--input-dir', '-i', required=True,
                           help='Directory containing FASTQ files')
    run_parser.add_argument('--reference', '-r', 
                           help='Reference genome FASTA file')
    run_parser.add_argument('--metadata', '-m',
                           help='Experimental metadata file (CSV, TSV, or Excel)')
    run_parser.add_argument('--config', '-c', default='config/config.yaml',
                           help='Configuration file path')
    run_parser.add_argument('--cores', '-j', type=int,
                           help='Number of cores to use')
    run_parser.add_argument('--dry-run', action='store_true',
                           help='Show what would be run without executing')
    run_parser.add_argument('--outdir', '-o',
                           help='Override output/results directory (default from config)')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize agent
    config_path = getattr(args, 'config', 'config/config.yaml')
    agent = NGSAIAgent(config_path)
    
    if args.command == 'setup':
        success = agent.setup_environment()
        sys.exit(0 if success else 1)
        
    elif args.command == 'run':
        # Discover input files
        input_files = agent.discover_input_files(args.input_dir)
        
        if not input_files:
            agent.print_error("No FASTQ files found in input directory")
            sys.exit(1)
        
        # Run pipeline
        success = agent.run_pipeline(
            input_files=input_files,
            reference_path=args.reference,
            metadata_file=args.metadata,
            dry_run=args.dry_run,
            cores=args.cores,
            outdir=args.outdir
        )
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()