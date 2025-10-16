"""
Query Analysis Engine for intelligent query interpretation and routing.

This module provides:
- Query intent classification
- Symbol and term extraction
- Retrieval strategy selection
- Query plan generation
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict
from enum import Enum

from ..config import get_enhancement_config

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Query intent classification."""
    SEMANTIC = "semantic"  # Natural language, conceptual queries
    SYMBOL = "symbol"  # Exact symbol lookup
    HYBRID = "hybrid"  # Combination of semantic and symbol
    ARCHITECTURAL = "architectural"  # Dependency/flow queries
    PATTERN = "pattern"  # Code pattern queries


class RetrievalStrategy(Enum):
    """Retrieval strategy selection."""
    SEMANTIC_SEARCH = "semantic_search"  # Pure semantic search
    SYMBOL_LOOKUP = "symbol_lookup"  # Exact symbol lookup
    HYBRID_RETRIEVAL = "hybrid_retrieval"  # Combined approach
    DEPENDENCY_EXPANSION = "dependency_expansion"  # Dependency-based expansion
    PATTERN_MATCHING = "pattern_matching"  # Pattern-based search


@dataclass
class QueryPlan:
    """
    Query execution plan.
    
    Contains all information needed to execute a query optimally.
    """
    query: str
    intent: QueryIntent
    strategy: RetrievalStrategy
    symbols: List[str] = field(default_factory=list)
    terms: List[str] = field(default_factory=list)
    filters: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


class QueryAnalyzer:
    """
    Intelligent query analyzer for intent classification and routing.
    
    Analyzes queries to determine:
    - Query intent (semantic, symbol, hybrid, architectural)
    - Extracted symbols and terms
    - Optimal retrieval strategy
    """
    
    # Patterns for symbol detection
    SYMBOL_PATTERNS = [
        r'\b([A-Z][a-zA-Z0-9_]*)\b',  # PascalCase (classes, interfaces)
        r'\b([a-z][a-zA-Z0-9_]+)\s*\(',  # function calls with parens
        r'\b([a-z][a-zA-Z0-9_]+)\s+(?:function|class|interface|type|method)\b',  # declarations
        r'`([a-zA-Z_][a-zA-Z0-9_]*)`',  # backtick-quoted symbols
        r'\b([a-z]+[A-Z][a-zA-Z0-9_]*)\b',  # camelCase (starts lowercase, has uppercase)
        r'(?:of|for|does)\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # symbols after "of", "for", or "does"
    ]
    
    # Keywords indicating architectural queries
    ARCHITECTURAL_KEYWORDS = {
        'flow', 'dependency', 'dependencies', 'depends', 'imports', 'uses',
        'calls', 'callers', 'callees', 'caller', 'callee', 'path', 'route', 'routes',
        'connection', 'connections', 'relationship', 'relationships',
        'architecture', 'structure', 'hierarchy', 'who calls', 'calls what',
        'find all', 'what does'
    }
    
    # Keywords indicating pattern queries
    PATTERN_KEYWORDS = {
        'pattern', 'patterns', 'similar', 'like', 'example', 'examples',
        'usage', 'usages', 'how to', 'best practice', 'common'
    }
    
    # Keywords indicating exact symbol lookup
    EXACT_KEYWORDS = {
        'function', 'class', 'interface', 'type', 'method', 'property',
        'variable', 'const', 'definition', 'declaration'
    }
    
    def __init__(self):
        """Initialize the query analyzer."""
        self.config = get_enhancement_config()
        logger.info("Initialized query analyzer")
    
    def analyze_query(self, query: str, filters: Optional[Dict] = None) -> QueryPlan:
        """
        Analyze a query and generate an execution plan.
        
        Args:
            query: User query string
            filters: Optional filters (file_path, symbol_type, etc.)
            
        Returns:
            QueryPlan with intent, strategy, and extracted information
        """
        # Normalize query
        normalized_query = self._normalize_query(query)
        
        # Extract symbols and terms
        symbols = self._extract_symbols(normalized_query)
        terms = self._extract_terms(normalized_query)
        
        # Classify intent
        intent = self._classify_intent(normalized_query, symbols, terms)
        
        # Select strategy
        strategy = self._select_strategy(intent, symbols, terms)
        
        # Build query plan
        plan = QueryPlan(
            query=query,
            intent=intent,
            strategy=strategy,
            symbols=symbols,
            terms=terms,
            filters=filters or {},
            metadata={
                'normalized_query': normalized_query,
                'has_symbols': len(symbols) > 0,
                'has_terms': len(terms) > 0,
            }
        )
        
        logger.debug(f"Query plan: intent={intent.value}, strategy={strategy.value}, "
                    f"symbols={len(symbols)}, terms={len(terms)}")
        
        return plan
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query text.
        
        Args:
            query: Raw query string
            
        Returns:
            Normalized query string
        """
        # Convert to lowercase for analysis (preserve original for display)
        normalized = query.strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _extract_symbols(self, query: str) -> List[str]:
        """
        Extract potential symbol names from query.
        
        Args:
            query: Query string
            
        Returns:
            List of extracted symbol names
        """
        symbols = set()
        
        # Apply symbol patterns
        for pattern in self.SYMBOL_PATTERNS:
            matches = re.finditer(pattern, query)
            for match in matches:
                symbol = match.group(1)
                # Filter out common words
                if len(symbol) > 2 and not self._is_common_word(symbol):
                    symbols.add(symbol)
        
        return list(symbols)
    
    def _extract_terms(self, query: str) -> List[str]:
        """
        Extract key terms from query.
        
        Args:
            query: Query string
            
        Returns:
            List of key terms
        """
        # Convert to lowercase for term extraction
        query_lower = query.lower()
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
            'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z][a-z0-9_]*\b', query_lower)
        
        # Filter stop words and short words
        terms = [w for w in words if w not in stop_words and len(w) > 2]
        
        return terms
    
    def _classify_intent(self, query: str, symbols: List[str], terms: List[str]) -> QueryIntent:
        """
        Classify query intent.
        
        Args:
            query: Normalized query string
            symbols: Extracted symbols
            terms: Extracted terms
            
        Returns:
            QueryIntent classification
        """
        query_lower = query.lower()
        
        # Check for architectural keywords
        if any(keyword in query_lower for keyword in self.ARCHITECTURAL_KEYWORDS):
            return QueryIntent.ARCHITECTURAL
        
        # Check for pattern keywords
        if any(keyword in query_lower for keyword in self.PATTERN_KEYWORDS):
            return QueryIntent.PATTERN
        
        # Check for exact symbol lookup
        if any(keyword in query_lower for keyword in self.EXACT_KEYWORDS):
            if symbols:
                return QueryIntent.SYMBOL
        
        # Hybrid if we have both symbols and semantic terms
        if symbols and len(terms) > 2:
            return QueryIntent.HYBRID
        
        # Symbol if we have clear symbol references
        if symbols and len(symbols) >= 1:
            return QueryIntent.SYMBOL
        
        # Default to semantic
        return QueryIntent.SEMANTIC
    
    def _select_strategy(self, intent: QueryIntent, symbols: List[str], 
                        terms: List[str]) -> RetrievalStrategy:
        """
        Select optimal retrieval strategy based on intent.
        
        Args:
            intent: Classified query intent
            symbols: Extracted symbols
            terms: Extracted terms
            
        Returns:
            RetrievalStrategy selection
        """
        # Architectural queries use dependency expansion
        if intent == QueryIntent.ARCHITECTURAL:
            return RetrievalStrategy.DEPENDENCY_EXPANSION
        
        # Pattern queries use pattern matching
        if intent == QueryIntent.PATTERN:
            return RetrievalStrategy.PATTERN_MATCHING
        
        # Symbol queries with exact match
        if intent == QueryIntent.SYMBOL and symbols:
            return RetrievalStrategy.SYMBOL_LOOKUP
        
        # Hybrid queries combine approaches
        if intent == QueryIntent.HYBRID:
            return RetrievalStrategy.HYBRID_RETRIEVAL
        
        # Default to semantic search
        return RetrievalStrategy.SEMANTIC_SEARCH
    
    def _is_common_word(self, word: str) -> bool:
        """
        Check if a word is a common English word (not a symbol).
        
        Args:
            word: Word to check
            
        Returns:
            True if common word, False otherwise
        """
        common_words = {
            'get', 'set', 'add', 'remove', 'delete', 'update', 'create',
            'find', 'search', 'list', 'show', 'display', 'render', 'load',
            'save', 'open', 'close', 'start', 'stop', 'run', 'execute',
            'handle', 'process', 'validate', 'check', 'test', 'build',
            'make', 'new', 'old', 'first', 'last', 'next', 'previous'
        }
        
        return word.lower() in common_words
