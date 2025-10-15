# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-14

### Added
- Initial release of NGS AI Agent
- AI-powered automated NGS analysis pipeline
- Support for both amplicon-based and barcode-coupled DMS
- Intelligent file matching using AI
- Automatic pipeline type detection
- Comprehensive CLI interface
- Support for CSV, TSV, and Excel metadata files
- Integration with Ollama for AI capabilities
- Conda environment management
- System resource monitoring
- Colored output and progress indicators
- Dry run functionality
- Comprehensive error handling and logging

### Features
- **Pipeline Types**: Direct amplicon DMS and barcode-coupled DMS
- **AI Integration**: Uses Ollama with qwen3-coder model for intelligent analysis
- **File Formats**: Supports FASTQ, FASTA, GenBank, CSV, TSV, Excel
- **Metadata Analysis**: Automatic condition detection (input, output, mapping, control)
- **System Integration**: Automatic conda environment setup and service checking
- **Cross-Platform**: Works on Linux, macOS, and Windows
- **Extensible**: Modular design for easy extension

### Technical Details
- Built with Python 3.8+
- Uses Snakemake for workflow management
- Integrates with conda for dependency management
- Supports multi-core processing
- Comprehensive logging and error reporting
- Type hints throughout codebase
