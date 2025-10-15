#!/usr/bin/env python3
"""
Setup script for NGS AI Agent
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "NGS AI Agent - AI-powered automated NGS analysis pipeline"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="ngs-ai-agent",
    version="1.0.0",
    author="NGS AI Agent Team",
    author_email="contact@ngs-ai-agent.com",
    description="AI-powered automated NGS analysis pipeline",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/ngs-ai-agent",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "ngs-ai-agent=ngs_ai_agent.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ngs_ai_agent": [
            "config/*.yaml",
            "workflow/*.smk",
            "workflow/rules/*.smk",
            "environment.yml",
        ],
    },
    zip_safe=False,
    keywords="ngs, bioinformatics, ai, genomics, sequencing, pipeline",
    project_urls={
        "Bug Reports": "https://github.com/your-org/ngs-ai-agent/issues",
        "Source": "https://github.com/your-org/ngs-ai-agent",
        "Documentation": "https://ngs-ai-agent.readthedocs.io/",
    },
)