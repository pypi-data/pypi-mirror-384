"""
Project language detection for SemanticScout.

This module analyzes project structure, file extensions, and configuration files
to determine the primary programming languages used in a codebase.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import Counter
import json

logger = logging.getLogger(__name__)


@dataclass
class LanguageDetectionResult:
    """Result of project language detection."""
    primary_language: Optional[str]
    languages: Dict[str, float]  # language -> confidence score (0.0-1.0)
    total_files: int
    config_files_found: List[str]
    confidence: float  # Overall confidence in detection (0.0-1.0)


class ProjectLanguageDetector:
    """
    Detects the primary programming language(s) of a project.
    
    Uses multiple strategies:
    1. Configuration file detection (Cargo.toml, package.json, *.csproj, etc.)
    2. File extension statistics
    3. Project structure analysis
    """
    
    # Configuration files that indicate specific languages
    CONFIG_FILE_INDICATORS = {
        "rust": ["Cargo.toml", "Cargo.lock"],
        "c_sharp": ["*.csproj", "*.sln", "*.fsproj", "*.vbproj", "global.json"],
        "python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "poetry.lock"],
        "javascript": ["package.json", "package-lock.json", "yarn.lock"],
        "typescript": ["tsconfig.json", "tslint.json"],
        "java": ["pom.xml", "build.gradle", "gradle.properties"],
        "go": ["go.mod", "go.sum"],
        "php": ["composer.json", "composer.lock"],
        "ruby": ["Gemfile", "Gemfile.lock", "*.gemspec"],
        "swift": ["Package.swift", "*.xcodeproj", "*.xcworkspace"],
        "kotlin": ["build.gradle.kts"],
    }
    
    # File extensions mapped to languages
    EXTENSION_TO_LANGUAGE = {
        ".rs": "rust",
        ".cs": "c_sharp",
        ".fs": "c_sharp",  # F#
        ".vb": "c_sharp",  # VB.NET
        ".py": "python",
        ".pyi": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".go": "go",
        ".php": "php",
        ".rb": "ruby",
        ".swift": "swift",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".scala": "scala",
        ".clj": "clojure",
        ".hs": "haskell",
        ".elm": "elm",
        ".dart": "dart",
        ".lua": "lua",
        ".r": "r",
        ".R": "r",
    }
    
    # Minimum confidence threshold for language detection
    MIN_CONFIDENCE_THRESHOLD = 0.1
    
    # Configuration file confidence boost
    CONFIG_FILE_CONFIDENCE_BOOST = 0.4
    
    def __init__(self, include_extensions: Optional[Set[str]] = None):
        """
        Initialize the language detector.
        
        Args:
            include_extensions: Optional set of file extensions to consider.
                               If None, uses all known extensions.
        """
        self.include_extensions = include_extensions or set(self.EXTENSION_TO_LANGUAGE.keys())
    
    def detect_languages(self, root_path: Path) -> LanguageDetectionResult:
        """
        Detect the primary language(s) of a project.
        
        Args:
            root_path: Root directory of the project
            
        Returns:
            LanguageDetectionResult with detected languages and confidence scores
        """
        if not root_path.exists() or not root_path.is_dir():
            raise ValueError(f"Invalid project path: {root_path}")
        
        logger.info(f"Detecting project languages in: {root_path}")
        
        # Step 1: Detect configuration files
        config_files = self._detect_config_files(root_path)
        config_languages = self._analyze_config_files(config_files)
        
        # Step 2: Analyze file extensions
        file_stats = self._analyze_file_extensions(root_path)
        extension_languages = self._calculate_extension_confidence(file_stats)
        
        # Step 3: Combine results
        combined_languages = self._combine_language_scores(config_languages, extension_languages)
        
        # Step 4: Determine primary language and overall confidence
        primary_language = self._determine_primary_language(combined_languages)
        overall_confidence = self._calculate_overall_confidence(combined_languages, config_files)
        
        result = LanguageDetectionResult(
            primary_language=primary_language,
            languages=combined_languages,
            total_files=sum(file_stats.values()),
            config_files_found=config_files,
            confidence=overall_confidence
        )
        
        logger.info(f"Language detection complete. Primary: {primary_language}, "
                   f"Confidence: {overall_confidence:.2f}, Languages: {combined_languages}")
        
        return result
    
    def _detect_config_files(self, root_path: Path) -> List[str]:
        """Detect configuration files that indicate specific languages."""
        found_files = []
        
        # Check for exact filename matches
        for files_list in self.CONFIG_FILE_INDICATORS.values():
            for pattern in files_list:
                if "*" in pattern:
                    # Handle glob patterns
                    try:
                        matches = list(root_path.glob(pattern))
                        found_files.extend([str(f.relative_to(root_path)) for f in matches])
                    except Exception as e:
                        logger.debug(f"Error globbing pattern {pattern}: {e}")
                else:
                    # Handle exact filenames
                    config_file = root_path / pattern
                    if config_file.exists():
                        found_files.append(pattern)
        
        logger.debug(f"Found configuration files: {found_files}")
        return found_files
    
    def _analyze_config_files(self, config_files: List[str]) -> Dict[str, float]:
        """Analyze configuration files to determine language confidence."""
        language_scores = {}
        
        for config_file in config_files:
            for language, patterns in self.CONFIG_FILE_INDICATORS.items():
                for pattern in patterns:
                    if self._matches_pattern(config_file, pattern):
                        current_score = language_scores.get(language, 0.0)
                        language_scores[language] = min(1.0, current_score + self.CONFIG_FILE_CONFIDENCE_BOOST)
                        logger.debug(f"Config file {config_file} indicates {language} "
                                   f"(score: {language_scores[language]:.2f})")
                        break
        
        return language_scores

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches a pattern (supports basic glob)."""
        if "*" in pattern:
            # Simple glob matching for *.ext patterns
            if pattern.startswith("*"):
                return filename.endswith(pattern[1:])
            elif pattern.endswith("*"):
                return filename.startswith(pattern[:-1])
        return filename == pattern

    def _analyze_file_extensions(self, root_path: Path) -> Dict[str, int]:
        """Analyze file extensions in the project."""
        extension_counts = Counter()

        try:
            # Walk through all files in the project
            for file_path in root_path.rglob("*"):
                if file_path.is_file():
                    extension = file_path.suffix.lower()
                    if extension in self.include_extensions:
                        extension_counts[extension] += 1
        except Exception as e:
            logger.warning(f"Error analyzing file extensions: {e}")

        logger.debug(f"File extension counts: {dict(extension_counts)}")
        return dict(extension_counts)

    def _calculate_extension_confidence(self, file_stats: Dict[str, int]) -> Dict[str, float]:
        """Calculate language confidence based on file extension statistics."""
        if not file_stats:
            return {}

        total_files = sum(file_stats.values())
        language_file_counts = Counter()

        # Map extensions to languages and count files
        for extension, count in file_stats.items():
            language = self.EXTENSION_TO_LANGUAGE.get(extension)
            if language:
                language_file_counts[language] += count

        # Calculate confidence scores (percentage of total files)
        language_scores = {}
        for language, count in language_file_counts.items():
            confidence = count / total_files
            if confidence >= self.MIN_CONFIDENCE_THRESHOLD:
                language_scores[language] = confidence

        logger.debug(f"Extension-based language scores: {language_scores}")
        return language_scores

    def _combine_language_scores(self, config_scores: Dict[str, float],
                                extension_scores: Dict[str, float]) -> Dict[str, float]:
        """Combine configuration file and extension-based scores."""
        all_languages = set(config_scores.keys()) | set(extension_scores.keys())
        combined_scores = {}

        for language in all_languages:
            config_score = config_scores.get(language, 0.0)
            extension_score = extension_scores.get(language, 0.0)

            # Weighted combination: config files have higher weight
            combined_score = (config_score * 0.6) + (extension_score * 0.4)

            # Boost if both indicators are present
            if config_score > 0 and extension_score > 0:
                combined_score = min(1.0, combined_score * 1.2)

            combined_scores[language] = combined_score

        return combined_scores

    def _determine_primary_language(self, language_scores: Dict[str, float]) -> Optional[str]:
        """Determine the primary language from scores."""
        if not language_scores:
            return None

        # Return language with highest confidence
        return max(language_scores.items(), key=lambda x: x[1])[0]

    def _calculate_overall_confidence(self, language_scores: Dict[str, float],
                                    config_files: List[str]) -> float:
        """Calculate overall confidence in the detection."""
        if not language_scores:
            return 0.0

        # Base confidence is the highest language score
        max_score = max(language_scores.values())

        # Boost confidence if configuration files were found
        if config_files:
            max_score = min(1.0, max_score + 0.2)

        # Reduce confidence if too many languages detected (unclear project)
        if len(language_scores) > 3:
            max_score *= 0.8

        return max_score
