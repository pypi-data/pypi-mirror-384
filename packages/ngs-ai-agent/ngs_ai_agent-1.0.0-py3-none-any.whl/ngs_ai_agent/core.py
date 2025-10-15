"""
NGS AI Agent Core Module
Contains the main NGSAIAgent class and core functionality
"""

import os
import sys
import yaml
import subprocess
from pathlib import Path
import logging
from typing import List, Optional
import json
import shutil
import time

from .ai_orchestrator.ollama_client import OllamaOrchestrator

logger = logging.getLogger(__name__)


class NGSAIAgent:
    """Main NGS AI Agent class"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the NGS AI Agent"""
        self.config_path = config_path
        self.config = self._load_config()
        self.orchestrator = OllamaOrchestrator(config_path)
        # Use current working directory as project root for pip-installed package
        self.project_root = Path.cwd()
        
        # Color codes for output
        self.colors = {
            'RED': '\033[0;31m',
            'GREEN': '\033[0;32m',
            'YELLOW': '\033[1;33m',
            'BLUE': '\033[0;34m',
            'NC': '\033[0m'  # No Color
        }
    
    def print_status(self, message: str):
        """Print status message with blue color"""
        print(f"{self.colors['BLUE']}[NGS-AI-AGENT]{self.colors['NC']} {message}")
    
    def print_success(self, message: str):
        """Print success message with green color"""
        print(f"{self.colors['GREEN']}[SUCCESS]{self.colors['NC']} {message}")
    
    def print_warning(self, message: str):
        """Print warning message with yellow color"""
        print(f"{self.colors['YELLOW']}[WARNING]{self.colors['NC']} {message}")
    
    def print_error(self, message: str):
        """Print error message with red color"""
        print(f"{self.colors['RED']}[ERROR]{self.colors['NC']} {message}")
        
    def _load_config(self) -> dict:
        """Load configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
    
    def setup_environment(self):
        """Set up the conda environment"""
        logger.info("Setting up conda environment...")
        
        env_file = self.project_root / "environment.yml"
        if not env_file.exists():
            logger.error("Environment file not found: environment.yml")
            return False
        
        try:
            # Check if environment already exists
            result = subprocess.run(
                ["conda", "env", "list", "--json"],
                capture_output=True,
                text=True,
                check=True
            )
            
            env_name = "ai-ngs"
            if env_name not in result.stdout:
                # Create environment
                logger.info(f"Creating conda environment: {env_name}")
                subprocess.run(
                    ["conda", "env", "create", "-f", str(env_file)],
                    check=True
                )
                logger.info("Environment created successfully!")
            else:
                logger.info(f"Environment '{env_name}' already exists")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set up environment: {e}")
            return False
    
    def check_conda_environment(self) -> bool:
        """Check if conda environment exists"""
        self.print_status("Checking conda environment...")
        try:
            result = subprocess.run(
                ["conda", "env", "list", "--json"],
                capture_output=True,
                text=True,
                check=True
            )
            env_data = json.loads(result.stdout)
            
            # Handle conda output format - envs is a list of paths
            if 'envs' in env_data:
                env_paths = env_data.get('envs', [])
                env_names = [Path(env_path).name for env_path in env_paths]
            else:
                # Fallback: parse from stdout directly
                env_names = []
                for line in result.stdout.split('\n'):
                    if 'ai-ngs' in line:
                        env_names.append('ai-ngs')
                        break
            
            if 'ai-ngs' in env_names:
                self.print_success("Using conda environment: ai-ngs")
                return True
            else:
                self.print_warning("Conda environment 'ai-ngs' not found. Setting up...")
                return self.setup_environment()
                
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            self.print_warning(f"Could not check conda environment: {e}")
            self.print_status("Continuing anyway (assuming environment is available)...")
            return True  # Continue anyway
    
    def check_ollama_service(self) -> bool:
        """Check if Ollama service is running"""
        self.print_status("Checking Ollama service...")
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Check if qwen3-coder model is available
                if "qwen3-coder:latest" in result.stdout:
                    self.print_success("Ollama model qwen3-coder:latest is available")
                    return True
                else:
                    self.print_warning("Model qwen3-coder:latest not found. You may need to run: ollama pull qwen3-coder:latest")
                    return True  # Service is running, just missing model
            else:
                self.print_warning("Ollama service not detected. Please start it with: ollama serve")
                self.print_status("Continuing anyway (some AI features may not work)...")
                return True  # Continue anyway
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.print_warning("Ollama service not detected. Please start it with: ollama serve")
            self.print_status("Continuing anyway (some AI features may not work)...")
            return True  # Continue anyway
    
    def check_system_resources(self) -> dict:
        """Check available system resources"""
        self.print_status("Checking system resources...")
        
        # Get CPU count
        cpu_count = os.cpu_count()
        self.print_status(f"Available CPU cores: {cpu_count}")
        
        # Get memory info (Linux)
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            for line in meminfo.split('\n'):
                if 'MemTotal:' in line:
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / 1024 / 1024
                    self.print_status(f"Available memory: {mem_gb:.0f}GB")
                    break
        except:
            self.print_warning("Could not determine memory information")
            mem_gb = 0
        
        return {
            'cpu_count': cpu_count,
            'memory_gb': mem_gb
        }
    
    def discover_input_files(self, input_dir: str) -> List[str]:
        """Discover FASTQ files in input directory"""
        logger.info(f"Discovering FASTQ files in: {input_dir}")
        
        input_path = Path(input_dir)
        if not input_path.exists():
            logger.error(f"Input directory does not exist: {input_dir}")
            return []
        
        # Find FASTQ files
        fastq_patterns = ["*.fastq.gz", "*.fq.gz", "*.fastq", "*.fq"]
        fastq_files = []
        
        for pattern in fastq_patterns:
            fastq_files.extend(input_path.glob(pattern))
        
        fastq_files = [str(f.absolute()) for f in fastq_files]
        
        logger.info(f"Found {len(fastq_files)} FASTQ files")
        return fastq_files
    
    def prepare_reference(self, reference_path: Optional[str] = None) -> bool:
        """Prepare reference genome file"""
        if reference_path and os.path.exists(reference_path):
            logger.info(f"Using provided reference: {reference_path}")
            # Copy to resources directory if not already there
            target_ref = self.project_root / "resources" / "reference.fasta"
            target_ref.parent.mkdir(parents=True, exist_ok=True)
            
            if not target_ref.exists() or str(Path(reference_path).absolute()) != str(target_ref.absolute()):
                shutil.copy2(reference_path, target_ref)
                logger.info(f"Copied reference to: {target_ref}")
            else:
                logger.info("Provided reference is already at resources/reference.fasta; skipping copy")
        else:
            logger.info("No reference provided, using placeholder")
            # Create a placeholder reference
            target_ref = self.project_root / "resources" / "reference.fasta"
            target_ref.parent.mkdir(parents=True, exist_ok=True)
            
            placeholder_seq = """>placeholder_reference
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
"""
            with open(target_ref, 'w') as f:
                f.write(placeholder_seq)
        
        return target_ref.exists()
    
    def run_pipeline(self, input_files: List[str], reference_path: Optional[str] = None, 
                    metadata_file: Optional[str] = None, dry_run: bool = False, cores: int = None,
                    outdir: Optional[str] = None) -> bool:
        """Run the Snakemake pipeline"""
        logger.info("Running NGS AI Agent pipeline...")
        
        # System checks
        if not self.check_conda_environment():
            self.print_error("Failed to set up conda environment!")
            return False
        
        if not self.check_ollama_service():
            self.print_warning("Ollama service issues detected, but continuing...")
        
        resources = self.check_system_resources()
        
        # Display run information
        self.print_status("=== NGS AI Agent Pipeline ===")
        self.print_status(f"Input directory: {os.path.dirname(input_files[0]) if input_files else 'N/A'}")
        self.print_status(f"Reference genome: {reference_path or 'Placeholder (auto-generated)'}")
        self.print_status(f"Metadata file: {metadata_file or 'None (basic mode)'}")
        self.print_status(f"CPU cores: {cores or 'Default'}")
        self.print_status(f"Configuration: {self.config_path}")
        self.print_status(f"Dry run: {dry_run}")
        self.print_status("==============================")
        
        if dry_run:
            self.print_status("DRY RUN MODE - No actual execution")
        
        # Prepare reference
        if not self.prepare_reference(reference_path):
            logger.error("Failed to prepare reference genome")
            return False
        # Ensure Snakefile uses the prepared reference under resources/
        prepared_ref = str(self.project_root / "resources" / "reference.fasta")
        self.config.setdefault("reference_genome", prepared_ref)
        self.config["reference_genome"] = prepared_ref
        logger.info(f"Configured reference_genome: {self.config['reference_genome']}")
        
        # Copy input files to raw data directory
        raw_data_dir = Path(self.config["data"]["raw"])
        raw_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file is required for this pipeline
        if not metadata_file or not os.path.exists(metadata_file):
            logger.error("Metadata file is required but not provided or not found.")
            logger.error("Please provide a valid CSV, TSV, or Excel metadata file.")
            return False
        
        logger.info(f"Loading experimental metadata from: {metadata_file}")
        
        # Validate file format
        if not metadata_file.endswith(('.csv', '.tsv', '.xlsx')):
            logger.error(f"Unsupported metadata format. Please use CSV, TSV, or Excel files.")
            return False
        
        # Use tabular metadata for file organization
        file_metadata = self.orchestrator.detect_and_validate_metadata_from_table(
            input_files, metadata_file
        )
        cleaned_paths = self.orchestrator.clean_filenames_from_table_metadata(
            input_files, file_metadata, "data/raw"
        )
        logger.info("Files organized using tabular metadata")
        
        # Clean up existing symlinks in raw_data_dir
        raw_data_path = Path(raw_data_dir)
        if raw_data_path.exists():
            for existing_file in raw_data_path.glob("*.fastq.gz"):
                if existing_file.is_symlink():
                    existing_file.unlink()
                    logger.info(f"Removed existing symlink: {existing_file}")
        
        # Create symlinks for input files
        for original_path, cleaned_path in cleaned_paths.items():
            # Extract just the filename from the cleaned path
            filename = Path(cleaned_path).name
            target_path = raw_data_path / filename
            if not target_path.exists():
                target_path.symlink_to(Path(original_path).absolute())
                logger.info(f"Linked: {original_path} -> {target_path}")
        
        # Update config with input directory and metadata file
        self.config["input_directory"] = str(Path(input_files[0]).parent.absolute())
        self.config["metadata_file"] = str(Path(metadata_file).absolute())
        
        # Override output directory if specified
        if outdir:
            self.config["data"]["results"] = str(Path(outdir).absolute())
            logger.info(f"Overriding results directory to: {self.config['data']['results']}")

        # Save updated config to file
        with open(self.project_root / self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        
        # Prepare Snakemake command
        snakemake_cmd = [
            "snakemake",
            "--snakefile", str(self.project_root / "workflow" / "Snakefile"),
            "--configfile", str(self.project_root / self.config_path),
            "--directory", str(self.project_root)
        ]
        
        if cores:
            snakemake_cmd.extend(["--cores", str(cores)])
        else:
            snakemake_cmd.extend(["--cores", str(self.config["pipeline"]["threads"])])
        
        if dry_run:
            snakemake_cmd.append("--dry-run")
            snakemake_cmd.append("--printshellcmds")
        
        # Add other useful options
        snakemake_cmd.extend([
            "--use-conda",
            "--conda-frontend", "conda",
            "--rerun-incomplete",
            "--printshellcmds"
        ])
        
        try:
            logger.info(f"Running command: {' '.join(snakemake_cmd)}")
            result = subprocess.run(snakemake_cmd, check=True, cwd=self.project_root)
            
            if dry_run:
                self.print_success("Dry run completed successfully!")
                self.print_status("The pipeline is ready to run. Remove --dry-run to execute.")
            else:
                self.print_success("Pipeline completed successfully!")
                self.print_status("Results are available in the 'results/' directory")
                self.print_status("Open results/reports/final_report.html to view the analysis report")
                self._print_results_summary()
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error("Pipeline failed! Check the logs for details.")
            logger.error(f"Pipeline failed: {e}")
            return False
    
    def _print_results_summary(self):
        """Print summary of results"""
        # Read results dir from config (default to project_root/results)
        configured_results = self.config.get("data", {}).get("results", "results")
        results_dir = Path(configured_results)
        
        if results_dir.exists():
            self.print_status(f"Results directory: {results_dir.absolute()}")
            
            # List key result files
            key_files = [
                "reports/final_report.html",
                "variants/final_variants.csv",
                "fitness/fitness_scores.csv",
                "plots/summary_plots.html"
            ]
            
            for file_path in key_files:
                full_path = results_dir / file_path
                if full_path.exists():
                    self.print_success(f"✓ {file_path}")
                else:
                    self.print_warning(f"⚠ {file_path} (not found)")
        else:
            self.print_warning(f"Results directory not found: {results_dir}")
