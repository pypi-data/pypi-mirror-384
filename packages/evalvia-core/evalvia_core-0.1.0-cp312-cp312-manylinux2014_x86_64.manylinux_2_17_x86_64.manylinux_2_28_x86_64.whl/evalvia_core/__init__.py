"""
Evalvia Core Module

A comprehensive module for processing question papers and answersheets using AI-powered evaluation.
"""

# Import main classes and exceptions from the core file
from .evalvia import (
    Evalvia,           # Main class
    EvlaviaConfig,     # Configuration class
    EvlaviaError,      # Base exception
    ConfigurationError,
    ProcessingError,
    ValidationError
)

# Optional: Expose version or other metadata
__version__ = "0.1.0"
__author__ = "Rahul Dilare"

# You can add more imports here if you want to expose other components
# For example, if you want to allow importing handlers directly:
# from .llm_handler import LLMHandler
# from .extractor_client import ExtractorClient
# But keep it minimal to avoid cluttering the public API.