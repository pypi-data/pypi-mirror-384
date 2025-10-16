# NGS AI Agent

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/ngs-ai-agent.svg)](https://badge.fury.io/py/ngs-ai-agent)

**AI-powered automated NGS analysis pipeline for Deep Mutational Scanning (DMS) experiments**

NGS AI Agent is a comprehensive, intelligent pipeline that automates Next-Generation Sequencing (NGS) data analysis with AI-powered metadata interpretation and experimental design detection. It supports both amplicon-based and barcode-coupled DMS workflows with minimal user configuration.

## 🚀 Quick Start

```bash
# 1. Create conda environment from environment.yml
conda env create -f environment.yml
conda activate ai-ngs

# 2. Install the package
pip install ngs-ai-agent

# 3. Run analysis with your data
ngs-ai-agent run --input-dir /path/to/fastq/files --metadata experiment.csv --dry-run
```

## ✨ Features

### 🤖 AI-Powered Analysis
- **Intelligent File Matching**: Automatically matches FASTQ files to experimental metadata using AI
- **Pipeline Type Detection**: Automatically detects amplicon-based vs barcode-coupled DMS experiments
- **Condition Classification**: AI-powered classification of samples as input, output, mapping, or control
- **Metadata Interpretation**: Supports CSV, TSV, and Excel metadata files with flexible column naming

### 🧬 Comprehensive DMS Support
- **Amplicon-Based DMS**: Direct sequencing of amplicons for variant calling and fitness calculation
- **Barcode-Coupled DMS**: Long-read barcode-to-variant mapping with short-read barcode counting
- **Paired-End Support**: Full support for paired-end sequencing data
- **Quality Control**: Integrated QC metrics and visualization

### 🔧 Advanced Workflow Management
- **Snakemake Integration**: Robust workflow management with automatic dependency resolution
- **Conda Environment**: Automated environment setup and dependency management
- **Multi-Core Processing**: Efficient parallel processing with configurable core usage
- **Dry Run Mode**: Preview pipeline execution before running

### 📊 Rich Output and Visualization
- **Interactive Reports**: HTML reports with embedded visualizations
- **Fitness Calculations**: Comprehensive fitness score calculations and statistical analysis
- **Variant Analysis**: Detailed variant calling and annotation
- **Publication-Ready Plots**: High-quality figures for manuscripts

## 📋 Requirements

- **Python**: 3.8 or higher
- **Conda**: For environment management
- **Ollama**: For AI capabilities (optional but recommended)
- **Memory**: 8GB+ RAM recommended
- **Storage**: Varies by dataset size

## 🛠️ Installation

### Prerequisites

1. **Install Conda**: Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution)

2. **Clone the Repository**:
```bash
git clone https://github.com/your-org/ngs-ai-agent.git
cd ngs-ai-agent
```

### Step 1: Create Conda Environment

```bash
# Create the conda environment with all bioinformatics dependencies
conda env create -f environment.yml

# Activate the environment
conda activate ai-ngs
```

### Step 2: Install the Package

```bash
# Install from PyPI (recommended)
pip install ngs-ai-agent

# OR install from source for development
pip install -e .
```

## 🎯 Usage

### Basic Usage

```bash
# Make sure you're in the activated conda environment
conda activate ai-ngs

# Run analysis with CSV metadata
ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --reference /path/to/reference.fasta \
  --metadata experiment.csv \
  --outdir /path/to/results \
  --cores 8

# Dry run to preview pipeline
ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --metadata experiment.csv \
  --dry-run
```

### Advanced Usage

```bash
# High-performance run with many cores
ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --reference /path/to/reference.fasta \
  --metadata experiment.xlsx \
  --outdir /path/to/results \
  --cores 32 

# Custom configuration
ngs-ai-agent run \
  --input-dir /path/to/fastq/files \
  --metadata experiment.csv \
  --config /path/to/custom/config.yaml
```

### Command Options

| Option | Short | Description | Required |
|--------|-------|-------------|----------|
| `--input-dir` | `-i` | Directory containing FASTQ files | ✅ |
| `--reference` | `-r` | Reference genome FASTA file | ❌ |
| `--metadata` | `-m` | Experimental metadata file (CSV/TSV/Excel) | ❌ |
| `--config` | `-c` | Configuration file path | ❌ |
| `--cores` | `-j` | Number of cores to use | ❌ |
| `--dry-run` | | Show what would be run without executing | ❌ |
| `--outdir` | `-o` | Override output/results directory | ❌ |

## 📁 Input Data Format

### FASTQ Files
- **Supported formats**: `.fastq.gz`, `.fq.gz`, `.fastq`, `.fq`
- **Paired-end**: Automatically detected and handled
- **Naming**: Flexible naming conventions supported

### Metadata Files
The pipeline supports CSV, TSV, and Excel metadata files with the following columns:

#### Required Columns
- **Sample identification**: `filename1`, `filename`, `sample_name`, or similar
- **Condition**: `condition`, `treatment`, `timepoint`, or similar
- **Replication**: `replication`, `rep`, `replicate`, or similar

#### Optional Columns
- **Paired-end**: `filename2`, `filename_r2`, `file_name_r2` for R2 files
- **Library layout**: `library_layout` (single/paired)
- **Description**: `description`, `sample_description` for AI analysis

#### Example Metadata (CSV)
```csv
filename1,filename2,condition,replication,description
Sample1_R1.fastq.gz,Sample1_R2.fastq.gz,input,1,pre-selection library
Sample2_R1.fastq.gz,Sample2_R2.fastq.gz,output,1,post-selection enriched
Sample3_R1.fastq.gz,Sample3_R2.fastq.gz,mapping,1,PacBio barcode mapping
```

## 🔬 Pipeline Types

### Amplicon-Based DMS
- **Use case**: Direct sequencing of PCR amplicons
- **Workflow**: Quality control → Variant calling → Fitness calculation
- **Output**: Variant frequencies, fitness scores, statistical analysis

### Barcode-Coupled DMS
- **Use case**: Barcode-based variant identification
- **Workflow**: Barcode mapping → Barcode counting → Fitness calculation
- **Output**: Barcode-to-variant maps, fitness scores, enrichment analysis

## 📊 Output Structure

```
results/
├── reports/
│   └── final_report.html          # Interactive HTML report
├── variants/
│   └── final_variants.csv         # Variant calling results
├── fitness/
│   └── fitness_scores.csv         # Fitness calculations
├── plots/
│   ├── summary_plots.html         # Interactive visualizations
│   └── publication_plots/         # High-resolution figures
└── logs/
    └── pipeline.log               # Detailed execution log
```

## ⚙️ Configuration

The pipeline uses YAML configuration files. Key settings include:

```yaml
# AI Settings
ai:
  model: "qwen3-coder:latest"
  endpoint: "http://localhost:11434"

# Pipeline Settings
pipeline:
  threads: 8
  memory: "16G"

# Data Paths
data:
  raw: "data/raw"
  processed: "data/processed"
  results: "results"
```

## 🤖 AI Integration

NGS AI Agent integrates with Ollama for intelligent analysis:

### Setup Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the required model
ollama pull qwen3-coder:latest

# Start Ollama service
ollama serve
```

### AI Capabilities
- **File Matching**: Intelligent matching of files to metadata
- **Condition Detection**: Automatic classification of experimental conditions
- **Pipeline Selection**: Smart detection of appropriate analysis workflow
- **Quality Assessment**: AI-powered quality control recommendations

## 🧪 Examples

### Example 1: Amplicon-Based DMS
```bash
ngs-ai-agent run \
  --input-dir data/amplicon_experiment/ \
  --reference reference.fasta \
  --metadata amplicon_metadata.csv \
  --cores 16
```

### Example 2: Barcode-Coupled DMS
```bash
ngs-ai-agent run \
  --input-dir data/barcode_experiment/ \
  --reference barcode_reference.gb \
  --metadata barcode_metadata.xlsx \
  --cores 32 \
  --outdir results/barcode_analysis
```

## 🐛 Troubleshooting

### Common Issues

**1. Ollama Service Not Running**
```bash
# Start Ollama service
ollama serve

# Check if model is available
ollama list
```

**2. Conda Environment Issues**
```bash
# Recreate environment
conda env remove -n ai-ngs
conda env create -f environment.yml
conda activate ai-ngs
```

**3. Permission Errors**
```bash
# Install with user flag
pip install --user ngs-ai-agent
```

**4. Memory Issues**
```bash
# Reduce cores or increase available memory
ngs-ai-agent run --cores 4 --input-dir /path/to/data --metadata experiment.csv
```

### Getting Help
```bash
# Show help
ngs-ai-agent --help
ngs-ai-agent run --help

# Check version
ngs-ai-agent --version
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone repository
git clone https://github.com/your-org/ngs-ai-agent.git
cd ngs-ai-agent

# Create conda environment
conda env create -f environment.yml
conda activate ai-ngs

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Citation

If you use NGS AI Agent in your research, please cite:

```bibtex
@software{ngs_ai_agent,
  title={NGS AI Agent: AI-powered automated NGS analysis pipeline},
  author={NGS AI Agent Team},
  year={2024},
  url={https://github.com/your-org/ngs-ai-agent},
  license={MIT}
}
```

## 🔗 Links

- **Documentation**: [https://ngs-ai-agent.readthedocs.io/](https://ngs-ai-agent.readthedocs.io/)
- **PyPI Package**: [https://pypi.org/project/ngs-ai-agent/](https://pypi.org/project/ngs-ai-agent/)
- **GitHub Repository**: [https://github.com/your-org/ngs-ai-agent](https://github.com/your-org/ngs-ai-agent)
- **Issue Tracker**: [https://github.com/your-org/ngs-ai-agent/issues](https://github.com/your-org/ngs-ai-agent/issues)

## 🙏 Acknowledgments

- Built with [Snakemake](https://snakemake.readthedocs.io/) for workflow management
- AI capabilities powered by [Ollama](https://ollama.ai/)
- Bioinformatics tools from [Bioconda](https://bioconda.github.io/)
- Visualization with [Plotly](https://plotly.com/) and [Matplotlib](https://matplotlib.org/)

---

**Made with ❤️ for the bioinformatics community**
