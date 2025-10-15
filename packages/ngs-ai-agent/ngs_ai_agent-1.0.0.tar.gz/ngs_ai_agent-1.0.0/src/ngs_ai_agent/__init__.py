"""
NGS AI Agent - AI-powered automated NGS analysis pipeline

A comprehensive pipeline for analyzing Next-Generation Sequencing (NGS) data
with AI-powered metadata analysis and automated workflow execution.
"""

__version__ = "1.0.0"
__author__ = "NGS AI Agent Team"
__email__ = "contact@ngs-ai-agent.com"
__description__ = "AI-powered automated NGS analysis pipeline"

# Import main components
from .cli import main
from .core import NGSAIAgent

__all__ = [
    "main",
    "NGSAIAgent",
    "__version__",
    "__author__",
    "__email__",
    "__description__",
]
