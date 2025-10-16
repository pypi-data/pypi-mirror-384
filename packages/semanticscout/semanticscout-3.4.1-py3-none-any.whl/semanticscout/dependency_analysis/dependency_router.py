"""
Dependency analysis router for language-aware dependency processing.
"""

import logging
from typing import List, Dict, Any, Optional
from ..dependency_graph.dependency_graph import DependencyGraph
from ..symbol_table.symbol_table import SymbolTable
from ..language_detection.project_language_detector import LanguageDetectionResult
from .strategies import (
    DependencyAnalysisStrategy,
    CSharpDependencyStrategy,
    RustDependencyStrategy,
    PythonDependencyStrategy,
    JavaScriptDependencyStrategy,
    JavaDependencyStrategy,
    DefaultDependencyStrategy
)

logger = logging.getLogger(__name__)


class DependencyAnalysisRouter:
    """
    Routes dependency analysis to appropriate language-specific strategies.
    
    This router analyzes detected project languages and applies the most
    appropriate dependency analysis strategy for each language.
    """
    
    def __init__(self, custom_strategies: Optional[List[DependencyAnalysisStrategy]] = None):
        """
        Initialize the dependency analysis router.
        
        Args:
            custom_strategies: Optional list of custom strategies to add
        """
        self.strategies: List[DependencyAnalysisStrategy] = []
        
        # Register default strategies
        self._register_default_strategies()
        
        # Register custom strategies if provided
        if custom_strategies:
            for strategy in custom_strategies:
                self.register_strategy(strategy)
        
        logger.debug(f"Initialized dependency router with {len(self.strategies)} strategies")
    
    def _register_default_strategies(self) -> None:
        """Register the default built-in strategies."""
        default_strategies = [
            CSharpDependencyStrategy(),
            RustDependencyStrategy(),
            PythonDependencyStrategy(),
            JavaScriptDependencyStrategy(),
            JavaDependencyStrategy(),
            DefaultDependencyStrategy()  # Always last as fallback
        ]

        for strategy in default_strategies:
            self.strategies.append(strategy)
    
    def register_strategy(self, strategy: DependencyAnalysisStrategy) -> None:
        """
        Register a new dependency analysis strategy.
        
        Args:
            strategy: The strategy to register
        """
        # Insert before the default strategy (which should be last)
        if self.strategies and isinstance(self.strategies[-1], DefaultDependencyStrategy):
            self.strategies.insert(-1, strategy)
        else:
            self.strategies.append(strategy)
        
        logger.debug(f"Registered strategy for languages: {strategy.get_supported_languages()}")
    
    def analyze_dependencies(
        self,
        dependency_graph: DependencyGraph,
        symbol_table: SymbolTable,
        detected_languages: LanguageDetectionResult
    ) -> Dict[str, Any]:
        """
        Analyze dependencies using appropriate language-specific strategies.
        
        Args:
            dependency_graph: The dependency graph to analyze
            symbol_table: The symbol table for lookups
            detected_languages: Language detection results
            
        Returns:
            Dictionary with analysis results from all applied strategies
        """
        if not detected_languages or not detected_languages.languages:
            logger.warning("No languages detected - using default strategy")
            return self._apply_default_strategy(dependency_graph, symbol_table, detected_languages)
        
        logger.info(f"Routing dependency analysis for detected languages: {list(detected_languages.languages.keys())}")
        
        results = {
            "primary_language": detected_languages.primary_language,
            "detected_languages": detected_languages.languages,
            "strategies_applied": [],
            "total_resolved": 0,
            "success": True
        }
        
        # Apply strategies for each detected language
        for language, confidence in detected_languages.languages.items():
            strategy = self._find_strategy_for_language(language, confidence)
            
            if strategy:
                logger.info(f"Applying {strategy.__class__.__name__} for {language} (confidence: {confidence:.2f})")
                
                try:
                    strategy_result = strategy.analyze_dependencies(
                        dependency_graph, symbol_table, detected_languages
                    )
                    
                    strategy_result["language"] = language
                    strategy_result["confidence"] = confidence
                    results["strategies_applied"].append(strategy_result)
                    
                    if strategy_result.get("success", False):
                        results["total_resolved"] += strategy_result.get("resolved_dependencies", 0)
                    else:
                        results["success"] = False
                        
                except Exception as e:
                    logger.error(f"Strategy {strategy.__class__.__name__} failed for {language}: {e}")
                    results["strategies_applied"].append({
                        "strategy": strategy.__class__.__name__,
                        "language": language,
                        "confidence": confidence,
                        "success": False,
                        "error": str(e)
                    })
                    results["success"] = False
            else:
                logger.debug(f"No strategy found for {language} with confidence {confidence:.2f}")
        
        # If no strategies were applied, use default
        if not results["strategies_applied"]:
            logger.info("No language-specific strategies applied - using default strategy")
            default_result = self._apply_default_strategy(dependency_graph, symbol_table, detected_languages)
            results.update(default_result)
        
        logger.info(f"Dependency analysis complete. Total resolved: {results['total_resolved']}")
        return results
    
    def _find_strategy_for_language(self, language: str, confidence: float) -> Optional[DependencyAnalysisStrategy]:
        """
        Find the most appropriate strategy for a given language and confidence.
        
        Args:
            language: The programming language
            confidence: The confidence score for this language
            
        Returns:
            The best matching strategy or None
        """
        for strategy in self.strategies:
            supported_languages = strategy.get_supported_languages()
            threshold = strategy.get_confidence_threshold()
            
            # Check if strategy supports this language and confidence is above threshold
            if (language in supported_languages or "*" in supported_languages) and confidence >= threshold:
                return strategy
        
        return None
    
    def _apply_default_strategy(
        self,
        dependency_graph: DependencyGraph,
        symbol_table: SymbolTable,
        detected_languages: Optional[LanguageDetectionResult]
    ) -> Dict[str, Any]:
        """Apply the default fallback strategy."""
        default_strategy = DefaultDependencyStrategy()
        
        if not detected_languages:
            # Create a minimal result for the default strategy
            from ..language_detection.project_language_detector import LanguageDetectionResult
            detected_languages = LanguageDetectionResult(
                primary_language=None,
                languages={},
                total_files=0,
                config_files_found=[],
                confidence=0.0
            )
        
        result = default_strategy.analyze_dependencies(dependency_graph, symbol_table, detected_languages)
        
        return {
            "primary_language": detected_languages.primary_language,
            "detected_languages": detected_languages.languages,
            "strategies_applied": [result],
            "total_resolved": result.get("resolved_dependencies", 0),
            "success": result.get("success", True)
        }
    
    def get_registered_strategies(self) -> List[str]:
        """
        Get a list of all registered strategy names.
        
        Returns:
            List of strategy class names
        """
        return [strategy.__class__.__name__ for strategy in self.strategies]
    
    def get_supported_languages(self) -> List[str]:
        """
        Get a list of all supported languages across all strategies.
        
        Returns:
            List of supported language names
        """
        all_languages = set()
        for strategy in self.strategies:
            languages = strategy.get_supported_languages()
            if "*" not in languages:  # Exclude wildcard from the list
                all_languages.update(languages)
        
        return sorted(list(all_languages))
