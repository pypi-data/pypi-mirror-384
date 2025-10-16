"""
Language detection module for SemanticScout.

This module provides project-level language detection capabilities to determine
the primary programming languages used in a codebase.
"""

from .project_language_detector import ProjectLanguageDetector, LanguageDetectionResult

__all__ = ["ProjectLanguageDetector", "LanguageDetectionResult"]
