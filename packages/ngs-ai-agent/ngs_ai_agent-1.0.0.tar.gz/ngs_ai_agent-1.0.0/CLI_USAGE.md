# NGS AI Agent - CLI Usage Guide

The NGS AI Agent now provides a comprehensive CLI interface that replaces the shell scripts with a more robust and feature-rich Python-based command-line tool.

## Quick Start

### Basic Usage
```bash
# Set up environment
./ngs-ai-agent setup

# Run analysis (replaces both run_pipeline.sh and run_pipeline_server.sh)
./ngs-ai-agent run --input-dir /path/to/fastq/files --reference /path/to/ref.fasta --metadata experiment.csv

# High-performance run with many cores
./ngs-ai-agent run --input-dir /path/to/fastq/files --reference /path/to/ref.fasta --metadata experiment.csv --cores 32
```

## Commands

### 1. Setup Command
```bash
./ngs-ai-agent setup
```
- Sets up the conda environment (`ai-ngs`)
- Installs all required dependencies
- Only needs to be run once

### 2. Run Command
```bash
./ngs-ai-agent run [OPTIONS]
```
- Pipeline execution (replaces both `run_pipeline.sh` and `run_pipeline_server.sh`)
- Automatically detects system resources and optimizes performance
- Supports all pipeline types (amplicon-based and barcode-based DMS)

## Options

### Required Options
- `--input-dir, -i DIR`: Directory containing FASTQ files

### Optional Options
- `--reference, -r FILE`: Reference genome FASTA file
- `--metadata, -m FILE`: Experimental metadata file (CSV, TSV, or Excel)
- `--config, -c FILE`: Configuration file path (default: config/config.yaml)
- `--cores, -j NUM`: Number of cores to use
- `--dry-run`: Show what would be run without executing
- `--outdir, -o DIR`: Override output/results directory

## Examples

### 1. Basic Analysis with CSV Metadata
```bash
./ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --reference /path/to/ref.fasta \
  --metadata experiment.csv
```

### 2. Analysis with Excel Metadata
```bash
./ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --reference /path/to/ref.fasta \
  --metadata experiment.xlsx
```

### 3. Dry Run to Check Pipeline
```bash
./ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --metadata experiment.csv \
  --dry-run
```

### 4. High-Performance Run
```bash
./ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --reference /path/to/ref.fasta \
  --metadata experiment.csv \
  --cores 32
```

### 5. Custom Output Directory
```bash
./ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --metadata experiment.csv \
  --outdir /custom/results/path
```

## Features

### System Checks
The CLI automatically performs comprehensive system checks:

1. **Conda Environment**: Verifies the `ai-ngs` environment exists
2. **Ollama Service**: Checks if the AI service is running
3. **System Resources**: Displays available CPU cores and memory
4. **Model Availability**: Verifies the `qwen3-coder:latest` model is available

### Colored Output
- 🔵 **Blue**: Status messages and information
- 🟢 **Green**: Success messages
- 🟡 **Yellow**: Warnings
- 🔴 **Red**: Errors

### AI-Powered Features
- **Intelligent File Matching**: Uses AI to match files to metadata
- **Pipeline Type Detection**: Automatically detects amplicon vs barcode-coupled DMS
- **Condition Detection**: Classifies samples as input, output, mapping, or control
- **Metadata Analysis**: Processes CSV, TSV, and Excel files

### Pipeline Types Supported
1. **Direct Amplicon DMS**: Direct sequencing of amplicons
2. **Barcode-Coupled DMS**: Barcode-based variant mapping

## Migration from Shell Scripts

### From `run_pipeline.sh`
```bash
# Old way
./run_pipeline.sh --input-dir results/NEP/data --reference resources/reference.fasta --metadata results/NEP/data/my_experiment.csv --cores 4

# New way
./ngs-ai-agent run --input-dir results/NEP/data --reference resources/reference.fasta --metadata results/NEP/data/my_experiment.csv --cores 4
```

### From `run_pipeline_server.sh`
```bash
# Old way
./run_pipeline_server.sh --input-dir results/H5_entry/data/ --reference results/H5_entry/ref/PacBio_amplicon.gb --metadata results/H5_entry/data/SRA_metadata_H5_entry.xlsx --outdir /data2/yiquan2/ngs-ai-agent/results/H5_entry --cores 32

# New way
./ngs-ai-agent run --input-dir results/H5_entry/data/ --reference results/H5_entry/ref/PacBio_amplicon.gb --metadata results/H5_entry/data/SRA_metadata_H5_entry.xlsx --outdir /data2/yiquan2/ngs-ai-agent/results/H5_entry --cores 32
```

## Benefits of CLI over Shell Scripts

1. **Cross-Platform**: Works on Linux, macOS, and Windows
2. **Better Error Handling**: More robust error detection and reporting
3. **System Integration**: Automatic environment and service checks
4. **Colored Output**: Better visual feedback
5. **Extensible**: Easy to add new features and commands
6. **Type Safety**: Python's type system prevents many common errors
7. **Logging**: Comprehensive logging for debugging
8. **Configuration**: More flexible configuration management

## Troubleshooting

### Common Issues

1. **Conda Environment Not Found**
   ```bash
   ./ngs-ai-agent setup
   ```

2. **Ollama Service Not Running**
   ```bash
   ollama serve
   ```

3. **Model Not Available**
   ```bash
   ollama pull qwen3-coder:latest
   ```

4. **Permission Denied**
   ```bash
   chmod +x ngs-ai-agent
   ```

### Getting Help
```bash
./ngs-ai-agent --help
./ngs-ai-agent run --help
```

## Advanced Usage

### Custom Configuration
```bash
./ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --metadata experiment.csv \
  --config /path/to/custom/config.yaml
```

### Debug Mode
```bash
./ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --metadata experiment.csv \
  --dry-run
```

The CLI provides a modern, robust, and user-friendly interface for running the NGS AI Agent pipeline, with all the functionality of the original shell scripts plus many additional features and improvements.
