"""
Context expansion module for enhancing search results with surrounding context,
dependencies, and relationships.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ContextExpansionConfig:
    """Configuration for context expansion."""

    # Neighbor expansion
    neighbor_radius: int = 2
    max_neighbor_lines: int = 500

    # Import expansion
    include_imports: bool = True
    max_imports_per_chunk: int = 5
    max_chunks_per_import: int = 3

    # File context expansion
    include_file_context: bool = True

    # Reference expansion
    include_references: bool = False
    max_reference_depth: int = 1

    # Dependency expansion (NEW)
    include_dependencies: bool = True
    max_dependency_depth: int = 2
    max_dependencies_per_file: int = 10
    include_transitive_deps: bool = False

    # Caller/Callee expansion (NEW)
    include_callers: bool = True
    include_callees: bool = True
    max_callers_per_symbol: int = 5
    max_callees_per_symbol: int = 5
    caller_callee_depth: int = 1

    # Boundary detection (NEW)
    enable_boundary_detection: bool = True
    max_expansion_ratio: float = 10.0  # Max expanded_lines / original_lines
    relevance_threshold: float = 0.3  # Min relevance score for expansion

    # Chunk merging
    merge_adjacent_chunks: bool = True
    max_merge_gap: int = 5

    # Global limits
    max_expanded_chunks: int = 50
    max_total_lines: int = 2000


@dataclass
class MergedChunk:
    """Merged chunk from multiple source chunks."""

    content: str
    file_path: str
    start_line: int
    end_line: int
    source_chunk_ids: List[str]
    language: str
    metadata: Dict[str, Any]

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1


@dataclass
class ExpansionStats:
    """Statistics about expansion operation."""

    original_lines: int
    expanded_lines: int
    neighbors_added: int
    imports_added: int
    references_added: int
    dependencies_added: int  # NEW
    callers_added: int  # NEW
    callees_added: int  # NEW
    file_context_added: bool
    chunks_merged: int
    boundary_limited: bool  # NEW: Whether expansion was limited by boundary detection
    expansion_time_ms: float


@dataclass
class ExpandedResult:
    """Result of context expansion."""

    original_chunk: Dict[str, Any]
    expanded_chunks: List[Dict[str, Any]]
    merged_chunks: List[MergedChunk]
    expansion_stats: ExpansionStats

    @property
    def total_lines(self) -> int:
        """Total lines in expanded result."""
        return sum(chunk.line_count for chunk in self.merged_chunks)

    @property
    def total_chunks(self) -> int:
        """Total number of chunks (original + expanded)."""
        return 1 + len(self.expanded_chunks)


class ContextExpander:
    """
    Post-retrieval context expansion system.

    Expands search results with surrounding context, dependencies, and relationships
    to achieve higher context depth and completeness.
    """

    def __init__(
        self,
        vector_store,
        config: Optional[ContextExpansionConfig] = None,
        symbol_table=None,  # NEW: Optional SymbolTable for caller/callee expansion
        dependency_graph=None,  # NEW: Optional DependencyGraph for dependency expansion
    ):
        """
        Initialize the context expander.

        Args:
            vector_store: ChromaVectorStore instance
            config: Configuration for expansion (uses defaults if None)
            symbol_table: Optional SymbolTable for caller/callee expansion
            dependency_graph: Optional DependencyGraph for dependency expansion
        """
        self.vector_store = vector_store
        self.config = config or ContextExpansionConfig()
        self.symbol_table = symbol_table
        self.dependency_graph = dependency_graph
        self._expansion_cache = {}  # Cache expanded results

    def expand_chunk(
        self,
        chunk: Dict[str, Any],
        collection_name: str,
        expansion_level: str = "medium",
    ) -> ExpandedResult:
        """
        Expand a chunk with surrounding context based on expansion level.

        Args:
            chunk: Original search result chunk
            collection_name: Collection to search
            expansion_level: 'none', 'low', 'medium', 'high'

        Returns:
            ExpandedResult with expanded chunks and stats
        """
        import time

        start_time = time.time()

        # Check cache
        chunk_id = chunk.get("chunk_id", "")
        cache_key = f"{chunk_id}_{expansion_level}"
        if cache_key in self._expansion_cache:
            return self._expansion_cache[cache_key]

        # Configure expansion based on level
        if expansion_level == "none":
            return self._create_unexpanded_result(chunk)

        config = self._get_config_for_level(expansion_level)

        # Perform expansion
        expanded_chunks = []
        stats = {
            "neighbors_added": 0,
            "imports_added": 0,
            "references_added": 0,
            "dependencies_added": 0,
            "callers_added": 0,
            "callees_added": 0,
            "file_context_added": False,
            "boundary_limited": False,
        }

        # 1. File context expansion
        if config["include_file_context"]:
            file_chunk = self.expand_with_file_context(chunk, collection_name)
            if file_chunk:
                expanded_chunks.append(file_chunk)
                stats["file_context_added"] = True

        # 1.5. Smart context expansion (NEW) - class declarations, constructors for methods
        if expansion_level in ["medium", "high"]:
            smart_context = self.expand_with_smart_context(chunk, collection_name)
            expanded_chunks.extend(smart_context)
            stats["smart_context_added"] = len(smart_context)

        # 2. Neighbor expansion
        if config["neighbor_radius"] > 0:
            neighbors = self.expand_with_neighbors(
                chunk, collection_name, radius=config["neighbor_radius"]
            )
            expanded_chunks.extend(neighbors)
            stats["neighbors_added"] = len(neighbors)

        # 3. Import expansion
        if config["include_imports"]:
            imports = self.expand_with_imports(chunk, collection_name)
            expanded_chunks.extend(imports)
            stats["imports_added"] = len(imports)

        # 4. Reference expansion
        if config["include_references"]:
            references = self.expand_with_references(chunk, collection_name)
            expanded_chunks.extend(references)
            stats["references_added"] = len(references)

        # 5. Dependency expansion (NEW)
        if config.get("include_dependencies", False) and self.dependency_graph:
            dependencies = self.expand_with_dependencies(chunk, collection_name, config)
            expanded_chunks.extend(dependencies)
            stats["dependencies_added"] = len(dependencies)

        # 6. Caller/Callee expansion (NEW)
        if self.symbol_table:
            if config.get("include_callers", False):
                callers = self.expand_with_callers(chunk, collection_name, config)
                expanded_chunks.extend(callers)
                stats["callers_added"] = len(callers)

            if config.get("include_callees", False):
                callees = self.expand_with_callees(chunk, collection_name, config)
                expanded_chunks.extend(callees)
                stats["callees_added"] = len(callees)

        # 7. Apply boundary detection (NEW)
        if config.get("enable_boundary_detection", False):
            expanded_chunks, boundary_limited = self._apply_boundary_detection(
                chunk, expanded_chunks, config
            )
            stats["boundary_limited"] = boundary_limited

        # 8. Merge chunks
        all_chunks = [chunk] + expanded_chunks
        merged_chunks = self.merge_chunks(all_chunks)

        # Calculate stats
        original_lines = chunk["metadata"].get("end_line", 0) - chunk["metadata"].get(
            "start_line", 0
        ) + 1
        expanded_lines = sum(c.line_count for c in merged_chunks)
        expansion_time_ms = (time.time() - start_time) * 1000

        expansion_stats = ExpansionStats(
            original_lines=original_lines,
            expanded_lines=expanded_lines,
            neighbors_added=stats["neighbors_added"],
            imports_added=stats["imports_added"],
            references_added=stats["references_added"],
            dependencies_added=stats["dependencies_added"],
            callers_added=stats["callers_added"],
            callees_added=stats["callees_added"],
            file_context_added=stats["file_context_added"],
            chunks_merged=len(all_chunks) - len(merged_chunks),
            boundary_limited=stats["boundary_limited"],
            expansion_time_ms=expansion_time_ms,
        )

        result = ExpandedResult(
            original_chunk=chunk,
            expanded_chunks=expanded_chunks,
            merged_chunks=merged_chunks,
            expansion_stats=expansion_stats,
        )

        # Cache result
        self._expansion_cache[cache_key] = result

        return result

    def expand_with_neighbors(
        self, chunk: Dict[str, Any], collection_name: str, radius: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Retrieve neighboring chunks from the same file.

        Args:
            chunk: Original chunk
            collection_name: Collection to search
            radius: Number of chunks before/after to retrieve

        Returns:
            List of neighboring chunks
        """
        try:
            metadata = chunk.get("metadata", {})
            file_path = metadata.get("file_path", "")
            start_line = metadata.get("start_line", 0)
            end_line = metadata.get("end_line", 0)

            if not file_path:
                return []

            # Estimate average chunk size (assume ~50 lines per chunk)
            avg_chunk_lines = 50
            search_start = max(1, start_line - (radius * avg_chunk_lines))
            search_end = end_line + (radius * avg_chunk_lines)

            # Get chunks in line range
            neighbors = self.vector_store.get_chunks_by_line_range(
                collection_name, file_path, search_start, search_end
            )

            # Filter out the original chunk
            chunk_id = chunk.get("chunk_id", "")
            neighbors = [n for n in neighbors if n.get("chunk_id") != chunk_id]

            return neighbors[:radius * 2]  # Limit to radius chunks before and after

        except Exception as e:
            logger.warning(f"Failed to expand with neighbors: {e}")
            return []

    def expand_with_imports(
        self, chunk: Dict[str, Any], collection_name: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks for imported symbols.

        Args:
            chunk: Original chunk
            collection_name: Collection to search

        Returns:
            List of chunks for imported symbols
        """
        try:
            metadata = chunk.get("metadata", {})
            imports = metadata.get("imports", [])

            if not imports:
                return []

            # Limit imports to process
            imports = imports[: self.config.max_imports_per_chunk]

            imported_chunks = []
            # For now, we'll skip import resolution as it requires more complex logic
            # This would need to parse import statements and find corresponding files
            # TODO: Implement import resolution in future iteration

            return imported_chunks

        except Exception as e:
            logger.warning(f"Failed to expand with imports: {e}")
            return []

    def expand_with_file_context(
        self, chunk: Dict[str, Any], collection_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve file-level chunk for this chunk's file.

        Args:
            chunk: Original chunk
            collection_name: Collection to search

        Returns:
            File-level chunk or None
        """
        try:
            metadata = chunk.get("metadata", {})
            file_path = metadata.get("file_path", "")

            if not file_path:
                return None

            # Get all chunks from file
            file_chunks = self.vector_store.get_chunks_by_file(collection_name, file_path)

            # Find file-level chunk (chunk_type="file_context", nesting_level=0)
            for fc in file_chunks:
                fc_metadata = fc.get("metadata", {})
                if (
                    fc_metadata.get("chunk_type") == "file_context"
                    and fc_metadata.get("nesting_level") == 0
                ):
                    return fc

            return None

        except Exception as e:
            logger.warning(f"Failed to expand with file context: {e}")
            return None

    def expand_with_smart_context(
        self, chunk: Dict[str, Any], collection_name: str
    ) -> List[Dict[str, Any]]:
        """
        Expand method chunks with class declarations, constructors, and imports.

        For high-relevance method chunks (similarity > 0.6), automatically includes:
        - Class declaration (if method is in a class)
        - Constructor (if class has constructor)
        - File-level imports

        Args:
            chunk: Original chunk
            collection_name: Collection to search

        Returns:
            List of context chunks (max 3)
        """
        try:
            metadata = chunk.get("metadata", {})
            chunk_type = metadata.get("chunk_type", "")
            file_path = metadata.get("file_path", "")
            similarity = metadata.get("similarity_score", 0.0)

            # Only apply to method/function chunks with high relevance
            if chunk_type not in ["function_definition", "method_definition", "function", "method"]:
                return []

            if similarity < 0.6:
                logger.debug(f"Skipping smart context for {file_path} (similarity {similarity:.2f} < 0.6)")
                return []

            logger.info(f"Adding smart context for {file_path} (similarity {similarity:.2f})")

            context_chunks = []

            # Query for class declaration chunk
            class_chunk = self._find_class_declaration(chunk, collection_name)
            if class_chunk:
                class_chunk["metadata"]["is_context"] = True
                class_chunk["metadata"]["context_type"] = "class_declaration"
                context_chunks.append(class_chunk)
                logger.debug(f"Added class declaration context for {file_path}")

            # Query for constructor chunk
            constructor_chunk = self._find_constructor(chunk, collection_name)
            if constructor_chunk:
                constructor_chunk["metadata"]["is_context"] = True
                constructor_chunk["metadata"]["context_type"] = "constructor"
                context_chunks.append(constructor_chunk)
                logger.debug(f"Added constructor context for {file_path}")

            # Query for imports chunk (file_context)
            imports_chunk = self._find_imports(chunk, collection_name)
            if imports_chunk:
                imports_chunk["metadata"]["is_context"] = True
                imports_chunk["metadata"]["context_type"] = "imports"
                context_chunks.append(imports_chunk)
                logger.debug(f"Added imports context for {file_path}")

            # Limit to max 3 context chunks
            return context_chunks[:3]

        except Exception as e:
            logger.warning(f"Failed to expand with smart context: {e}")
            return []

    def _find_class_declaration(
        self, chunk: Dict[str, Any], collection_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find class declaration chunk for a method."""
        try:
            metadata = chunk.get("metadata", {})
            file_path = metadata.get("file_path", "")

            # Query for class_definition chunks in same file
            results = self.vector_store.search(
                collection_name=collection_name,
                query_embedding=None,  # No semantic search, just metadata filter
                top_k=5,
                filter_metadata={
                    "file_path": file_path,
                    "chunk_type": "class_definition"
                }
            )

            if results and len(results) > 0:
                return results[0]  # Return first class declaration

            return None
        except Exception as e:
            logger.debug(f"Failed to find class declaration: {e}")
            return None

    def _find_constructor(
        self, chunk: Dict[str, Any], collection_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find constructor chunk for a method."""
        try:
            metadata = chunk.get("metadata", {})
            file_path = metadata.get("file_path", "")
            language = metadata.get("language", "")

            # Constructor patterns by language
            constructor_patterns = {
                "python": "__init__",
                "csharp": ".ctor",
                "javascript": "constructor",
                "typescript": "constructor",
                "java": "<init>",
            }

            constructor_name = constructor_patterns.get(language)
            if not constructor_name:
                return None

            # Query for constructor chunks in same file
            results = self.vector_store.search(
                collection_name=collection_name,
                query_embedding=None,
                top_k=5,
                filter_metadata={
                    "file_path": file_path,
                }
            )

            # Filter for constructor by content
            for result in results:
                content = result.get("content", "")
                if constructor_name in content:
                    return result

            return None
        except Exception as e:
            logger.debug(f"Failed to find constructor: {e}")
            return None

    def _find_imports(
        self, chunk: Dict[str, Any], collection_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find imports/file_context chunk."""
        try:
            metadata = chunk.get("metadata", {})
            file_path = metadata.get("file_path", "")

            # Query for file_context chunks in same file
            results = self.vector_store.search(
                collection_name=collection_name,
                query_embedding=None,
                top_k=5,
                filter_metadata={
                    "file_path": file_path,
                    "chunk_type": "file_context"
                }
            )

            if results and len(results) > 0:
                return results[0]

            return None
        except Exception as e:
            logger.debug(f"Failed to find imports: {e}")
            return None

    def expand_with_references(
        self, chunk: Dict[str, Any], collection_name: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks with reference relationships.

        Args:
            chunk: Original chunk
            collection_name: Collection to search

        Returns:
            List of related chunks
        """
        try:
            metadata = chunk.get("metadata", {})
            referenced_by = metadata.get("referenced_by", [])

            if not referenced_by:
                return []

            # Retrieve chunks by ID
            related_chunks = []
            for ref_id in referenced_by[: self.config.max_reference_depth]:
                ref_chunk = self.vector_store.get_chunk_by_id(collection_name, ref_id)
                if ref_chunk:
                    related_chunks.append(ref_chunk)

            return related_chunks

        except Exception as e:
            logger.warning(f"Failed to expand with references: {e}")
            return []

    def merge_chunks(self, chunks: List[Dict[str, Any]]) -> List[MergedChunk]:
        """
        Merge overlapping or adjacent chunks from the same file.

        Args:
            chunks: List of chunks to merge

        Returns:
            List of merged chunks
        """
        if not chunks:
            return []

        # Group chunks by file_path
        chunks_by_file = defaultdict(list)
        for chunk in chunks:
            file_path = chunk.get("metadata", {}).get("file_path", "")
            if file_path:
                chunks_by_file[file_path].append(chunk)

        merged_results = []

        # Merge chunks for each file
        for file_path, file_chunks in chunks_by_file.items():
            # Sort by start_line
            file_chunks.sort(key=lambda x: x.get("metadata", {}).get("start_line", 0))

            # Merge adjacent/overlapping chunks
            current_merged = None

            for chunk in file_chunks:
                metadata = chunk.get("metadata", {})
                start_line = metadata.get("start_line", 0)
                end_line = metadata.get("end_line", 0)
                chunk_id = chunk.get("chunk_id", "")

                if current_merged is None:
                    # Start new merged chunk
                    current_merged = MergedChunk(
                        content=chunk.get("content", ""),
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        source_chunk_ids=[chunk_id],
                        language=metadata.get("language", ""),
                        metadata=metadata,
                    )
                else:
                    # Check if adjacent or overlapping
                    gap = start_line - current_merged.end_line
                    if gap <= self.config.max_merge_gap:
                        # Merge chunks
                        current_merged.content += "\n" + chunk.get("content", "")
                        current_merged.end_line = max(current_merged.end_line, end_line)
                        current_merged.source_chunk_ids.append(chunk_id)
                    else:
                        # Save current merged chunk and start new one
                        merged_results.append(current_merged)
                        current_merged = MergedChunk(
                            content=chunk.get("content", ""),
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            source_chunk_ids=[chunk_id],
                            language=metadata.get("language", ""),
                            metadata=metadata,
                        )

            # Add last merged chunk
            if current_merged:
                merged_results.append(current_merged)

        return merged_results

    def _create_unexpanded_result(self, chunk: Dict[str, Any]) -> ExpandedResult:
        """Create an ExpandedResult with no expansion."""
        metadata = chunk.get("metadata", {})
        original_lines = metadata.get("end_line", 0) - metadata.get("start_line", 0) + 1

        merged_chunk = MergedChunk(
            content=chunk.get("content", ""),
            file_path=metadata.get("file_path", ""),
            start_line=metadata.get("start_line", 0),
            end_line=metadata.get("end_line", 0),
            source_chunk_ids=[chunk.get("chunk_id", "")],
            language=metadata.get("language", ""),
            metadata=metadata,
        )

        stats = ExpansionStats(
            original_lines=original_lines,
            expanded_lines=original_lines,
            neighbors_added=0,
            imports_added=0,
            references_added=0,
            dependencies_added=0,
            callers_added=0,
            callees_added=0,
            file_context_added=False,
            chunks_merged=0,
            boundary_limited=False,
            expansion_time_ms=0.0,
        )

        return ExpandedResult(
            original_chunk=chunk,
            expanded_chunks=[],
            merged_chunks=[merged_chunk],
            expansion_stats=stats,
        )

    def _get_config_for_level(self, level: str) -> Dict[str, Any]:
        """Get expansion configuration for a given level."""
        configs = {
            "low": {
                "neighbor_radius": 1,
                "include_file_context": True,
                "include_imports": False,
                "include_references": False,
                "include_dependencies": False,
                "include_callers": False,
                "include_callees": False,
                "enable_boundary_detection": True,
            },
            "medium": {
                "neighbor_radius": 2,
                "include_file_context": True,
                "include_imports": True,
                "include_references": False,
                "include_dependencies": True,
                "include_callers": True,
                "include_callees": False,
                "enable_boundary_detection": True,
            },
            "high": {
                "neighbor_radius": 3,
                "include_file_context": True,
                "include_imports": True,
                "include_references": True,
                "include_dependencies": True,
                "include_callers": True,
                "include_callees": True,
                "enable_boundary_detection": True,
            },
        }

        return configs.get(level, configs["medium"])

    def expand_with_dependencies(
        self,
        chunk: Dict[str, Any],
        collection_name: str,
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Expand chunk with file dependencies from the dependency graph.

        Args:
            chunk: Original chunk
            collection_name: Collection name
            config: Expansion configuration

        Returns:
            List of dependency chunks
        """
        if not self.dependency_graph:
            return []

        try:
            file_path = chunk["metadata"].get("file_path", "")
            if not file_path:
                return []

            # Get file dependencies
            max_deps = config.get("max_dependencies_per_file", 10)
            depth = config.get("max_dependency_depth", 2)
            include_transitive = config.get("include_transitive_deps", False)

            dependencies = []

            # Get direct dependencies
            direct_deps = self.dependency_graph.get_file_dependencies(
                file_path, self.symbol_table, depth=1
            )

            for dep in list(direct_deps)[:max_deps]:
                # Extract file path from dependency dict
                dep_file = dep.get('to_file', '')
                if not dep_file:
                    continue
                # Get chunks from dependency file
                dep_chunks = self._get_chunks_from_file(dep_file, collection_name)
                dependencies.extend(dep_chunks[:2])  # Limit to 2 chunks per file

            # Get transitive dependencies if enabled
            if include_transitive and depth > 1:
                for dep in list(direct_deps)[:5]:  # Limit transitive search
                    dep_file = dep.get('to_file', '')
                    if not dep_file:
                        continue
                    transitive_deps = self.dependency_graph.get_file_dependencies(
                        dep_file, self.symbol_table, depth=1
                    )
                    for trans_dep in list(transitive_deps)[:3]:
                        trans_dep_file = trans_dep.get('to_file', '')
                        if trans_dep_file and trans_dep_file != file_path:  # Avoid cycles
                            trans_chunks = self._get_chunks_from_file(
                                trans_dep_file, collection_name
                            )
                            dependencies.extend(trans_chunks[:1])

            return dependencies

        except Exception as e:
            logger.warning(f"Failed to expand with dependencies: {e}")
            return []

    def expand_with_callers(
        self,
        chunk: Dict[str, Any],
        collection_name: str,
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Expand chunk with caller symbols from the symbol table.

        Args:
            chunk: Original chunk
            collection_name: Collection name
            config: Expansion configuration

        Returns:
            List of caller chunks
        """
        if not self.symbol_table:
            return []

        try:
            # Extract symbols from chunk metadata
            symbols = chunk["metadata"].get("symbols", [])
            if not symbols:
                return []

            max_callers = config.get("max_callers_per_symbol", 5)
            callers = []

            for symbol in symbols[:3]:  # Limit to first 3 symbols
                symbol_name = symbol.get("name", "")
                if not symbol_name:
                    continue

                # Find callers of this symbol
                caller_symbols = self.symbol_table.find_callers(
                    symbol_name, collection_name
                )

                for caller in list(caller_symbols)[:max_callers]:
                    # Get chunks containing the caller
                    caller_chunks = self._get_chunks_from_file(
                        caller["file_path"], collection_name, caller["line_number"]
                    )
                    callers.extend(caller_chunks[:1])

            return callers

        except Exception as e:
            logger.warning(f"Failed to expand with callers: {e}")
            return []

    def expand_with_callees(
        self,
        chunk: Dict[str, Any],
        collection_name: str,
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Expand chunk with callee symbols from the symbol table.

        Args:
            chunk: Original chunk
            collection_name: Collection name
            config: Expansion configuration

        Returns:
            List of callee chunks
        """
        if not self.symbol_table:
            return []

        try:
            # Extract symbols from chunk metadata
            symbols = chunk["metadata"].get("symbols", [])
            if not symbols:
                return []

            max_callees = config.get("max_callees_per_symbol", 5)
            callees = []

            for symbol in symbols[:3]:  # Limit to first 3 symbols
                symbol_name = symbol.get("name", "")
                if not symbol_name:
                    continue

                # Find callees of this symbol
                callee_symbols = self.symbol_table.find_callees(
                    symbol_name, collection_name
                )

                for callee in list(callee_symbols)[:max_callees]:
                    # Get chunks containing the callee
                    callee_chunks = self._get_chunks_from_file(
                        callee["file_path"], collection_name, callee["line_number"]
                    )
                    callees.extend(callee_chunks[:1])

            return callees

        except Exception as e:
            logger.warning(f"Failed to expand with callees: {e}")
            return []

    def _apply_boundary_detection(
        self,
        original_chunk: Dict[str, Any],
        expanded_chunks: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], bool]:
        """
        Apply intelligent boundary detection to prevent over-expansion.

        Args:
            original_chunk: Original chunk
            expanded_chunks: List of expanded chunks
            config: Expansion configuration

        Returns:
            Tuple of (filtered_chunks, was_limited)
        """
        if not expanded_chunks:
            return expanded_chunks, False

        # Calculate original size
        original_lines = original_chunk["metadata"].get("end_line", 0) - original_chunk[
            "metadata"
        ].get("start_line", 0) + 1

        # Calculate expanded size
        expanded_lines = sum(
            chunk["metadata"].get("end_line", 0)
            - chunk["metadata"].get("start_line", 0)
            + 1
            for chunk in expanded_chunks
        )

        # Check expansion ratio
        max_ratio = config.get("max_expansion_ratio", 10.0)
        if expanded_lines > original_lines * max_ratio:
            # Sort by relevance and limit
            sorted_chunks = sorted(
                expanded_chunks,
                key=lambda c: c.get("score", 0.0),
                reverse=True,
            )

            # Keep chunks until we hit the ratio limit
            filtered_chunks = []
            current_lines = 0
            max_lines = int(original_lines * max_ratio)

            for chunk in sorted_chunks:
                chunk_lines = chunk["metadata"].get("end_line", 0) - chunk[
                    "metadata"
                ].get("start_line", 0) + 1
                if current_lines + chunk_lines <= max_lines:
                    filtered_chunks.append(chunk)
                    current_lines += chunk_lines
                else:
                    break

            return filtered_chunks, True

        # Check relevance threshold
        relevance_threshold = config.get("relevance_threshold", 0.3)
        filtered_chunks = [
            chunk
            for chunk in expanded_chunks
            if chunk.get("score", 1.0) >= relevance_threshold
        ]

        was_limited = len(filtered_chunks) < len(expanded_chunks)
        return filtered_chunks, was_limited

    def _get_chunks_from_file(
        self,
        file_path: str,
        collection_name: str,
        target_line: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get chunks from a specific file.

        Args:
            file_path: File path
            collection_name: Collection name
            target_line: Optional target line number

        Returns:
            List of chunks from the file
        """
        try:
            # Query vector store for chunks from this file
            results = self.vector_store.query(
                collection_name=collection_name,
                query_texts=[""],  # Empty query to get all chunks
                n_results=100,
                where={"file_path": file_path},
            )

            if not results or not results.get("documents"):
                return []

            chunks = []
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                chunk = {
                    "content": doc,
                    "metadata": metadata,
                    "score": 0.5,  # Default score for dependency chunks
                }

                # If target line specified, prioritize chunks near it
                if target_line:
                    start_line = metadata.get("start_line", 0)
                    end_line = metadata.get("end_line", 0)
                    if start_line <= target_line <= end_line:
                        chunk["score"] = 1.0  # High score for exact match
                    else:
                        # Score based on distance
                        distance = min(
                            abs(start_line - target_line), abs(end_line - target_line)
                        )
                        chunk["score"] = max(0.3, 1.0 - (distance / 100.0))

                chunks.append(chunk)

            # Sort by score if target line specified
            if target_line:
                chunks.sort(key=lambda c: c["score"], reverse=True)

            return chunks

        except Exception as e:
            logger.warning(f"Failed to get chunks from file {file_path}: {e}")
            return []

