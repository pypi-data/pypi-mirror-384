"""
Hybrid Retrieval System for coordinating multiple retrieval strategies.

This module provides:
- Multi-stage retrieval pipeline
- Strategy coordination (semantic, symbol, hybrid, dependency)
- Result ranking and deduplication
- Context expansion integration
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from ..query_analysis import QueryAnalyzer, QueryPlan, QueryIntent, RetrievalStrategy
from ..symbol_table import SymbolTable
from ..dependency_graph import DependencyGraph
from ..retriever.semantic_search import SemanticSearcher, SearchResult
from ..config import get_enhancement_config

logger = logging.getLogger(__name__)


@dataclass
class HybridResult:
    """
    Unified result from hybrid retrieval.
    
    Combines results from multiple retrieval strategies with
    ranking scores and provenance information.
    """
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str
    language: str
    score: float  # Unified ranking score
    sources: List[str] = field(default_factory=list)  # Which strategies found this
    symbol_info: Optional[Dict] = None  # Symbol metadata if from symbol lookup
    dependency_info: Optional[Dict] = None  # Dependency metadata if from graph
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "chunk_type": self.chunk_type,
            "language": self.language,
            "score": self.score,
            "sources": self.sources,
            "symbol_info": self.symbol_info,
            "dependency_info": self.dependency_info,
            "metadata": self.metadata,
        }


class HybridRetriever:
    """
    Hybrid retrieval system coordinating multiple strategies.
    
    Coordinates:
    - Semantic search (existing Chroma DB)
    - Symbol lookup (Symbol Table)
    - Dependency expansion (Dependency Graph)
    - Result ranking and deduplication
    """
    
    def __init__(
        self,
        semantic_searcher: SemanticSearcher,
        symbol_table: Optional[SymbolTable] = None,
        dependency_graph: Optional[DependencyGraph] = None,
        query_analyzer: Optional[QueryAnalyzer] = None,
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            semantic_searcher: Semantic search engine
            symbol_table: Symbol table for symbol lookup
            dependency_graph: Dependency graph for architectural queries
            query_analyzer: Query analyzer for intent classification
        """
        self.semantic_searcher = semantic_searcher
        self.symbol_table = symbol_table
        self.dependency_graph = dependency_graph
        self.query_analyzer = query_analyzer or QueryAnalyzer()
        self.config = get_enhancement_config()
        
        logger.info("Initialized hybrid retriever")
    
    def retrieve(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        expansion_level: str = "medium",
    ) -> List[HybridResult]:
        """
        Retrieve results using optimal strategy based on query analysis.
        
        Args:
            query: User query string
            collection_name: Collection to search
            top_k: Number of results to return
            filters: Optional filters (file_path, symbol_type, etc.)
            expansion_level: Context expansion level
            
        Returns:
            List of hybrid results ranked by relevance
        """
        # Analyze query to determine strategy
        query_plan = self.query_analyzer.analyze_query(query, filters=filters)
        
        logger.info(f"Query plan: intent={query_plan.intent.value}, "
                   f"strategy={query_plan.strategy.value}")
        
        # Route to appropriate retrieval method
        if query_plan.strategy == RetrievalStrategy.SYMBOL_LOOKUP:
            results = self._symbol_retrieval(query_plan, collection_name, top_k)
        elif query_plan.strategy == RetrievalStrategy.SEMANTIC_SEARCH:
            results = self._semantic_retrieval(query_plan, collection_name, top_k, expansion_level)
        elif query_plan.strategy == RetrievalStrategy.HYBRID_RETRIEVAL:
            results = self._hybrid_retrieval(query_plan, collection_name, top_k, expansion_level)
        elif query_plan.strategy == RetrievalStrategy.DEPENDENCY_EXPANSION:
            results = self._dependency_retrieval(query_plan, collection_name, top_k)
        elif query_plan.strategy == RetrievalStrategy.PATTERN_MATCHING:
            results = self._pattern_retrieval(query_plan, collection_name, top_k, expansion_level)
        else:
            # Fallback to semantic search
            results = self._semantic_retrieval(query_plan, collection_name, top_k, expansion_level)
        
        # Rank and deduplicate results
        results = self._rank_and_deduplicate(results, query_plan)
        
        # Limit to top_k
        return results[:top_k]
    
    def _semantic_retrieval(
        self,
        query_plan: QueryPlan,
        collection_name: str,
        top_k: int,
        expansion_level: str,
    ) -> List[HybridResult]:
        """Pure semantic search retrieval."""
        search_results = self.semantic_searcher.search(
            query=query_plan.query,
            collection_name=collection_name,
            top_k=top_k * 2,  # Get more for ranking
            expansion_level=expansion_level,
        )
        
        # Convert to hybrid results
        hybrid_results = []
        for result in search_results:
            hybrid_results.append(HybridResult(
                content=result.content,
                file_path=result.file_path,
                start_line=result.start_line,
                end_line=result.end_line,
                chunk_type=result.chunk_type,
                language=result.language,
                score=result.similarity_score,
                sources=["semantic"],
                metadata=result.metadata,
            ))
        
        return hybrid_results
    
    def _symbol_retrieval(
        self,
        query_plan: QueryPlan,
        collection_name: str,
        top_k: int,
    ) -> List[HybridResult]:
        """Symbol-based retrieval using symbol table."""
        if not self.symbol_table:
            logger.warning("Symbol table not available, falling back to semantic search")
            return self._semantic_retrieval(query_plan, collection_name, top_k, "none")
        
        hybrid_results = []
        
        # Look up each symbol
        for symbol in query_plan.symbols:
            symbol_results = self.symbol_table.lookup_symbol(
                name=symbol,
                symbol_type=query_plan.filters.get('symbol_type')
            )
            
            for sym in symbol_results:
                # Create hybrid result from symbol
                hybrid_results.append(HybridResult(
                    content=f"Symbol: {sym['name']} ({sym['type']})\n"
                           f"File: {sym['file_path']}\n"
                           f"Line: {sym['line_number']}\n"
                           f"Signature: {sym.get('signature', 'N/A')}",
                    file_path=sym['file_path'],
                    start_line=sym['line_number'],
                    end_line=sym.get('end_line_number', sym['line_number']),
                    chunk_type='symbol',
                    language='typescript',  # TODO: detect from file extension
                    score=1.0,  # Exact match
                    sources=["symbol"],
                    symbol_info=sym,
                ))
        
        return hybrid_results
    
    def _hybrid_retrieval(
        self,
        query_plan: QueryPlan,
        collection_name: str,
        top_k: int,
        expansion_level: str,
    ) -> List[HybridResult]:
        """
        Hybrid retrieval combining semantic and symbol strategies.
        
        Multi-stage pipeline:
        1. Symbol lookup for exact matches
        2. Semantic search for conceptual matches
        3. Merge and rank results
        """
        all_results = []
        
        # Stage 1: Symbol lookup
        if query_plan.symbols and self.symbol_table:
            symbol_results = self._symbol_retrieval(query_plan, collection_name, top_k)
            all_results.extend(symbol_results)
            logger.debug(f"Symbol retrieval found {len(symbol_results)} results")
        
        # Stage 2: Semantic search
        semantic_results = self._semantic_retrieval(
            query_plan, collection_name, top_k, expansion_level
        )
        all_results.extend(semantic_results)
        logger.debug(f"Semantic retrieval found {len(semantic_results)} results")
        
        return all_results
    
    def _dependency_retrieval(
        self,
        query_plan: QueryPlan,
        collection_name: str,
        top_k: int,
    ) -> List[HybridResult]:
        """Dependency-based retrieval using dependency graph."""
        if not self.dependency_graph:
            logger.warning("Dependency graph not available, falling back to semantic search")
            return self._semantic_retrieval(query_plan, collection_name, top_k, "none")
        
        hybrid_results = []
        
        # Extract file paths or symbols from query
        if query_plan.symbols:
            # Find dependencies for symbols
            for symbol in query_plan.symbols:
                # Find callers
                if any(kw in query_plan.query.lower() for kw in ['caller', 'callers', 'who calls']):
                    callers = self.dependency_graph.find_callers(symbol)
                    for caller in callers:
                        hybrid_results.append(HybridResult(
                            content=f"Caller: {caller['caller']} calls {symbol}\n"
                                   f"File: {caller['from_file']}\n"
                                   f"Line: {caller.get('line_number', 'N/A')}",
                            file_path=caller['from_file'],
                            start_line=caller.get('line_number', 0),
                            end_line=caller.get('line_number', 0),
                            chunk_type='dependency',
                            language='typescript',
                            score=0.9,
                            sources=["dependency"],
                            dependency_info=caller,
                        ))

                # Find callees
                if any(kw in query_plan.query.lower() for kw in ['callee', 'callees', 'calls what', 'what does', 'does call']):
                    callees = self.dependency_graph.find_callees(symbol)
                    for callee in callees:
                        hybrid_results.append(HybridResult(
                            content=f"Callee: {symbol} calls {callee['callee']}\n"
                                   f"File: {callee['to_file']}\n"
                                   f"Line: {callee.get('line_number', 'N/A')}",
                            file_path=callee['to_file'],
                            start_line=callee.get('line_number', 0),
                            end_line=callee.get('line_number', 0),
                            chunk_type='dependency',
                            language='typescript',
                            score=0.9,
                            sources=["dependency"],
                            dependency_info=callee,
                        ))
        
        return hybrid_results
    
    def _pattern_retrieval(
        self,
        query_plan: QueryPlan,
        collection_name: str,
        top_k: int,
        expansion_level: str,
    ) -> List[HybridResult]:
        """Pattern-based retrieval (similar to semantic for now)."""
        # For now, use semantic search with high expansion
        return self._semantic_retrieval(query_plan, collection_name, top_k, "high")
    
    def _rank_and_deduplicate(
        self,
        results: List[HybridResult],
        query_plan: QueryPlan,
    ) -> List[HybridResult]:
        """
        Rank and deduplicate results.
        
        Deduplication strategy:
        - Same file + overlapping lines = duplicate
        - Merge sources and take highest score
        
        Ranking strategy:
        - Symbol matches score highest (1.0)
        - Dependency matches score high (0.9)
        - Semantic matches use similarity score
        - Boost results matching multiple strategies
        """
        # Deduplicate by file + line range
        seen: Dict[str, HybridResult] = {}
        
        for result in results:
            key = f"{result.file_path}:{result.start_line}-{result.end_line}"
            
            if key in seen:
                # Merge sources and take highest score
                existing = seen[key]
                existing.sources.extend(result.sources)
                existing.sources = list(set(existing.sources))  # Deduplicate sources
                existing.score = max(existing.score, result.score)
                
                # Merge metadata
                if result.symbol_info and not existing.symbol_info:
                    existing.symbol_info = result.symbol_info
                if result.dependency_info and not existing.dependency_info:
                    existing.dependency_info = result.dependency_info
            else:
                seen[key] = result
        
        # Convert back to list
        deduplicated = list(seen.values())

        # Boost multi-source results
        for result in deduplicated:
            if len(result.sources) > 1:
                result.score *= 1.2  # 20% boost for multi-source

        # FILE-LEVEL DEDUPLICATION (NEW)
        # Group chunks by file and merge multiple chunks from same file
        file_groups: Dict[str, List[HybridResult]] = {}
        for result in deduplicated:
            if result.file_path not in file_groups:
                file_groups[result.file_path] = []
            file_groups[result.file_path].append(result)

        # Merge chunks from same file
        file_deduplicated = []
        for file_path, chunks in file_groups.items():
            if len(chunks) == 1:
                # Single chunk, no merging needed
                file_deduplicated.append(chunks[0])
            else:
                # Multiple chunks from same file - merge them
                logger.info(f"Merging {len(chunks)} chunks from {file_path}")

                # Sort chunks by line number
                chunks.sort(key=lambda c: c.start_line)

                # Merge into single result
                merged = chunks[0]  # Start with first chunk
                merged.metadata["chunks_merged"] = len(chunks)

                # Combine content from all chunks
                all_content = []
                for chunk in chunks:
                    all_content.append(f"# Lines {chunk.start_line}-{chunk.end_line}")
                    all_content.append(chunk.content)
                    all_content.append("")  # Blank line separator

                merged.content = "\n".join(all_content)
                merged.end_line = chunks[-1].end_line  # Update end line to last chunk

                # Use highest score
                merged.score = max(c.score for c in chunks)

                # Merge all sources
                all_sources = []
                for chunk in chunks:
                    all_sources.extend(chunk.sources)
                merged.sources = list(set(all_sources))

                file_deduplicated.append(merged)

        # Sort by score (descending)
        file_deduplicated.sort(key=lambda r: r.score, reverse=True)

        return file_deduplicated
