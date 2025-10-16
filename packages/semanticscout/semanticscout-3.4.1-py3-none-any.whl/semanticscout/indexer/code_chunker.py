"""
Code chunking module for splitting code files into semantic chunks using AST parsing.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
import warnings

# Suppress the FutureWarning from tree-sitter
warnings.filterwarnings('ignore', category=FutureWarning, module='tree_sitter')

from tree_sitter import Node, Language, Parser
try:
    # Try new API (tree-sitter-languages >= 1.10.0)
    from tree_sitter_languages import get_language
    USE_NEW_API = True
except ImportError:
    # Fall back to old API
    from tree_sitter_languages import get_parser
    USE_NEW_API = False

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """Represents a semantic chunk of code."""

    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str  # e.g., "function", "class", "method", "module"
    language: str
    metadata: dict  # Additional metadata (enhanced with imports, exports, references, etc.)

    @property
    def content_hash(self) -> str:
        """Generate MD5 hash of chunk content for change detection."""
        import hashlib
        return hashlib.md5(self.content.encode()).hexdigest()


class ASTCodeChunker:
    """
    Chunks code files into semantic units using Abstract Syntax Tree parsing.
    """

    # Language file extension mapping
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "c_sharp",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
    }

    # Node types that represent semantic boundaries for different languages
    # CRITICAL: Removed class_declaration to force method-level chunking for better granularity
    # This prevents huge chunks containing entire classes (which caused import-only results)
    CHUNK_NODE_TYPES = {
        "python": ["function_definition", "class_definition"],  # Keep class for Python (smaller classes)
        "javascript": ["function_declaration", "method_definition"],  # Removed class_declaration
        "typescript": ["function_declaration", "method_definition"],  # Removed class_declaration
        "java": ["method_declaration"],  # Removed class_declaration
        "c": ["function_definition"],
        "cpp": ["function_definition"],  # Removed class_specifier
        "go": ["function_declaration", "method_declaration"],
        "rust": ["function_item", "impl_item"],  # Removed struct_item
        "ruby": ["method"],  # Removed class
        "php": ["function_definition"],  # Removed class_declaration
        "c_sharp": ["method_declaration"],  # Removed class_declaration - CRITICAL FIX
        "swift": ["function_declaration"],  # Removed class_declaration
        "kotlin": ["function_declaration"],  # Removed class_declaration
        "scala": ["function_definition"],  # Removed class_definition
    }

    # Import node types for different languages
    IMPORT_NODE_TYPES = {
        "python": ["import_statement", "import_from_statement"],
        "javascript": ["import_statement"],
        "typescript": ["import_statement"],
        "java": ["import_declaration"],
        "c": ["preproc_include"],
        "cpp": ["preproc_include"],
        "go": ["import_declaration"],
        "rust": ["use_declaration"],
        "ruby": [],  # Special handling required (method calls)
        "php": ["namespace_use_declaration", "require_expression", "require_once_expression", "include_expression", "include_once_expression"],
        "c_sharp": ["using_directive"],
        "swift": ["import_declaration"],
        "kotlin": ["import_header"],
        "scala": ["import_declaration"],
    }

    # Export node types for different languages
    EXPORT_NODE_TYPES = {
        "javascript": ["export_statement"],
        "typescript": ["export_statement"],
        "rust": ["use_declaration"],  # Check for 'pub' modifier
    }

    def __init__(
        self,
        min_chunk_size: int = 500,
        max_chunk_size: int = 3000,  # INCREASED from 1500
        overlap_size: int = 50,
        include_decorators: bool = True,  # NEW
        include_type_hints: bool = True,  # NEW
        include_comments: bool = True,  # NEW
        create_file_chunks: bool = True,  # NEW
    ):
        """
        Initialize the code chunker.

        Args:
            min_chunk_size: Minimum characters per chunk
            max_chunk_size: Maximum characters per chunk (increased to 3000)
            overlap_size: Number of characters to overlap between chunks
            include_decorators: Include decorators/annotations in chunks
            include_type_hints: Include type hints in chunks
            include_comments: Include leading comments in chunks
            create_file_chunks: Create file-level chunks with imports
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.include_decorators = include_decorators
        self.include_type_hints = include_type_hints
        self.include_comments = include_comments
        self.create_file_chunks = create_file_chunks
        self._parsers = {}  # Cache parsers by language

    def chunk_file(
        self,
        file_path: Path,
        content: str,
        file_metadata: Optional[Dict[str, Any]] = None
    ) -> List[CodeChunk]:
        """
        Chunk a code file into semantic units.

        Args:
            file_path: Path to the file
            content: File content as string
            file_metadata: Optional metadata to add to all chunks (e.g., file_type, test_penalty)

        Returns:
            List of CodeChunk objects
        """
        # Detect language from file extension
        language = self._detect_language(file_path)

        if not language:
            logger.warning(f"Unknown language for {file_path}, using fallback chunking")
            return self._fallback_chunk(file_path, content, "unknown", file_metadata)

        # Try AST-based chunking
        try:
            chunks = self._ast_chunk(file_path, content, language, file_metadata)
            if chunks:
                logger.info(f"Created {len(chunks)} AST chunks from {file_path}")
                return chunks
        except Exception as e:
            logger.warning(f"AST parsing failed for {file_path}: {e}, using fallback")

        # Fallback to character-based chunking
        return self._fallback_chunk(file_path, content, language, file_metadata)

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name or None if unknown
        """
        suffix = file_path.suffix.lower()
        return self.LANGUAGE_MAP.get(suffix)

    def _get_parser(self, language: str):
        """
        Get or create a tree-sitter parser for the given language.

        Args:
            language: Language name

        Returns:
            Parser instance or None if language not supported
        """
        if language in self._parsers:
            return self._parsers[language]

        try:
            if USE_NEW_API:
                # New API: get_language() returns Language, create Parser manually
                lang = get_language(language)
                parser = Parser()
                parser.set_language(lang)
            else:
                # Old API: get_parser() returns Parser directly
                parser = get_parser(language)

            self._parsers[language] = parser
            return parser
        except Exception as e:
            import traceback
            logger.warning(f"Could not create parser for {language}: {e}")
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            return None

    def _ast_chunk(
        self,
        file_path: Path,
        content: str,
        language: str,
        file_metadata: Optional[Dict[str, Any]] = None
    ) -> List[CodeChunk]:
        """
        Chunk code using AST parsing with hierarchical structure.

        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            file_metadata: Optional metadata to add to all chunks

        Returns:
            List of CodeChunk objects (file-level + function/class chunks)
        """
        parser = self._get_parser(language)
        if not parser:
            return []

        # Parse the code
        tree = parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node

        # Get chunk node types for this language
        chunk_types = self.CHUNK_NODE_TYPES.get(language, [])
        if not chunk_types:
            logger.warning(f"No chunk types defined for {language}")
            return []

        all_chunks = []

        # STEP 1: Create file-level chunk (NEW)
        file_chunk = None
        if self.create_file_chunks:
            file_chunk = self._extract_file_context(
                root_node, content, file_path, language, file_metadata
            )
            if file_chunk:
                all_chunks.append(file_chunk)

        # STEP 2: Extract function/class chunks
        code_chunks = []
        self._extract_chunks_recursive(
            root_node, content, file_path, language, chunk_types, code_chunks, root_node, file_metadata
        )

        # STEP 3: Link parent-child relationships (NEW)
        if file_chunk and code_chunks:
            file_chunk_id = self._generate_chunk_id(file_chunk)
            file_chunk.metadata["chunk_id"] = file_chunk_id  # NEW: Store chunk_id
            child_ids = []

            for chunk in code_chunks:
                chunk_id = self._generate_chunk_id(chunk)
                chunk.metadata["chunk_id"] = chunk_id  # NEW: Store chunk_id
                # Set parent_chunk_id for each code chunk
                chunk.metadata["parent_chunk_id"] = file_chunk_id
                chunk.metadata["nesting_level"] = 1  # Top-level functions/classes
                child_ids.append(chunk_id)

            # Set child_chunk_ids for file chunk
            file_chunk.metadata["child_chunk_ids"] = child_ids
        else:
            # NEW: Generate chunk_id for chunks without file context
            for chunk in code_chunks:
                chunk_id = self._generate_chunk_id(chunk)
                chunk.metadata["chunk_id"] = chunk_id

        all_chunks.extend(code_chunks)

        # If no chunks found, return empty (will trigger fallback)
        if not all_chunks:
            logger.warning(f"No semantic chunks found in {file_path}")
            return []

        return all_chunks

    def _extract_chunks_recursive(
        self,
        node: Node,
        content: str,
        file_path: Path,
        language: str,
        chunk_types: List[str],
        chunks: List[CodeChunk],
        root_node: Node = None,
        file_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Recursively extract chunks from AST nodes.

        Args:
            node: Current AST node
            content: File content
            file_path: Path to the file
            language: Programming language
            chunk_types: Node types to extract as chunks
            chunks: List to append chunks to
            root_node: Root node of the AST (for extracting file-level imports)
            file_metadata: Optional metadata to add to all chunks
        """
        # Check if this node is a chunk boundary
        if node.type in chunk_types:
            chunk_content = content[node.start_byte : node.end_byte]
            chunk_size = len(chunk_content)

            # Only create chunk if within size limits
            if chunk_size >= self.min_chunk_size:
                # Allow oversized chunks up to 2x max_chunk_size for complete implementations
                if chunk_size > self.max_chunk_size * 2:
                    logger.warning(
                        f"Very large chunk ({chunk_size} chars) in {file_path} "
                        f"at line {node.start_point[0] + 1}. Consider splitting."
                    )
                elif chunk_size > self.max_chunk_size:
                    logger.debug(
                        f"Oversized chunk ({chunk_size} > {self.max_chunk_size}) "
                        f"in {file_path} at line {node.start_point[0] + 1}"
                    )

                # Extract metadata (e.g., function/class name)
                metadata = self._extract_metadata(node, content, language, root_node)

                # Merge file_metadata if provided
                if file_metadata:
                    metadata.update(file_metadata)

                chunk = CodeChunk(
                    content=chunk_content,
                    file_path=str(file_path),
                    start_line=node.start_point[0] + 1,  # 1-indexed
                    end_line=node.end_point[0] + 1,  # 1-indexed
                    chunk_type=node.type,
                    language=language,
                    metadata=metadata,
                )
                chunks.append(chunk)

                # Don't recurse into children if we've created a chunk
                return

        # Recurse into children
        for child in node.children:
            self._extract_chunks_recursive(
                child, content, file_path, language, chunk_types, chunks, root_node, file_metadata
            )

    def _extract_metadata(self, node: Node, content: str, language: str, root_node: Node = None) -> dict:
        """
        Extract metadata from an AST node (e.g., function/class name).

        Args:
            node: AST node
            content: File content
            language: Programming language
            root_node: Root node of the AST (for extracting file-level imports)

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        # Try to find name node (common pattern across languages)
        for child in node.children:
            if "name" in child.type or child.type == "identifier":
                name_text = content[child.start_byte : child.end_byte]
                metadata["name"] = name_text
                break

        # Extract imports (NEW)
        try:
            if root_node:
                imports = self._extract_imports(root_node, content, language)
                metadata["imports"] = imports
        except Exception as e:
            logger.warning(f"Failed to extract imports: {e}")
            metadata["imports"] = []

        # Extract exports (NEW)
        try:
            exports = self._extract_exports(node, content, language)
            metadata["exports"] = exports
        except Exception as e:
            logger.warning(f"Failed to extract exports: {e}")
            metadata["exports"] = []

        # Extract references (NEW)
        try:
            references = self._extract_references(node, content, language)
            metadata["references"] = references
        except Exception as e:
            logger.warning(f"Failed to extract references: {e}")
            metadata["references"] = []

        # Detect context indicators (NEW)
        metadata["has_decorators"] = self._has_decorators(node, content, language)
        metadata["has_error_handling"] = self._has_error_handling(node, content, language)
        metadata["has_type_hints"] = self._has_type_hints(node, content, language)
        metadata["has_docstring"] = self._has_docstring(node, content, language)

        return metadata

    def _extract_imports(self, root_node: Node, content: str, language: str) -> list:
        """
        Extract import statements from AST.

        Args:
            root_node: Root node of the AST
            content: File content
            language: Programming language

        Returns:
            List of import dictionaries with 'statement' and 'line' keys
        """
        imports = []
        import_node_types = self.IMPORT_NODE_TYPES.get(language, [])

        if not import_node_types:
            return imports

        def extract_imports_recursive(node):
            if node.type in import_node_types:
                statement = content[node.start_byte : node.end_byte].strip()
                line = node.start_point[0] + 1
                imports.append({"statement": statement, "line": line})

            for child in node.children:
                extract_imports_recursive(child)

        extract_imports_recursive(root_node)
        return imports

    def _extract_exports(self, node: Node, content: str, language: str) -> list:
        """
        Extract export statements from AST node.

        Args:
            node: AST node
            content: File content
            language: Programming language

        Returns:
            List of export dictionaries with 'statement' and 'line' keys
        """
        exports = []
        export_node_types = self.EXPORT_NODE_TYPES.get(language, [])

        if not export_node_types:
            return exports

        def extract_exports_recursive(n):
            if n.type in export_node_types:
                statement = content[n.start_byte : n.end_byte].strip()
                line = n.start_point[0] + 1
                exports.append({"statement": statement, "line": line})

            for child in n.children:
                extract_exports_recursive(child)

        extract_exports_recursive(node)
        return exports

    def _extract_references(self, node: Node, content: str, language: str) -> list:
        """
        Extract function/class references from AST node.

        Args:
            node: AST node
            content: File content
            language: Programming language

        Returns:
            List of referenced symbol names
        """
        references = []

        # Node types that represent function calls or class instantiations
        call_node_types = {
            "python": ["call"],
            "javascript": ["call_expression"],
            "typescript": ["call_expression"],
            "java": ["method_invocation"],
            "go": ["call_expression"],
            "rust": ["call_expression"],
            "c_sharp": ["invocation_expression"],
        }

        call_types = call_node_types.get(language, [])

        def extract_references_recursive(n):
            if n.type in call_types:
                # Try to extract the function/method name
                for child in n.children:
                    if child.type in ["identifier", "field_expression", "attribute"]:
                        ref_name = content[child.start_byte : child.end_byte].strip()
                        if ref_name and ref_name not in references:
                            references.append(ref_name)
                        break

            for child in n.children:
                extract_references_recursive(child)

        extract_references_recursive(node)
        return references[:20]  # Limit to 20 references

    def _has_decorators(self, node: Node, content: str, language: str) -> bool:
        """Check if node has decorators/annotations."""
        decorator_types = {
            "python": ["decorator"],
            "typescript": ["decorator"],
            "java": ["annotation"],
        }

        dec_types = decorator_types.get(language, [])
        if not dec_types:
            return False

        def has_decorator_recursive(n):
            if n.type in dec_types:
                return True
            return any(has_decorator_recursive(child) for child in n.children)

        return has_decorator_recursive(node)

    def _has_error_handling(self, node: Node, content: str, language: str) -> bool:
        """Check if node contains error handling."""
        error_handling_types = {
            "python": ["try_statement", "except_clause", "raise_statement"],
            "javascript": ["try_statement", "catch_clause", "throw_statement"],
            "typescript": ["try_statement", "catch_clause", "throw_statement"],
            "java": ["try_statement", "catch_clause", "throw_statement"],
            "go": ["defer_statement"],
            "rust": ["match_expression"],
        }

        error_types = error_handling_types.get(language, [])
        if not error_types:
            return False

        def has_error_handling_recursive(n):
            if n.type in error_types:
                return True
            return any(has_error_handling_recursive(child) for child in n.children)

        return has_error_handling_recursive(node)

    def _has_type_hints(self, node: Node, content: str, language: str) -> bool:
        """Check if node has type hints/annotations."""
        type_hint_types = {
            "python": ["type"],
            "typescript": ["type_annotation"],
            "java": ["type_identifier"],
        }

        type_types = type_hint_types.get(language, [])
        if not type_types:
            return False

        def has_type_hint_recursive(n):
            if n.type in type_types:
                return True
            return any(has_type_hint_recursive(child) for child in n.children)

        return has_type_hint_recursive(node)

    def _has_docstring(self, node: Node, content: str, language: str) -> bool:
        """Check if node has documentation."""
        # For Python, check for string literal as first child
        if language == "python":
            for child in node.children:
                if child.type == "block":
                    for block_child in child.children:
                        if block_child.type == "expression_statement":
                            for expr_child in block_child.children:
                                if expr_child.type == "string":
                                    return True
                            break
                    break

        # For JavaScript/TypeScript, check for comment nodes
        if language in ["javascript", "typescript"]:
            # Check previous sibling for comment
            if node.prev_sibling and "comment" in node.prev_sibling.type:
                return True

        return False

    def _extract_file_context(
        self,
        root_node: Node,
        content: str,
        file_path: Path,
        language: str,
        file_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[CodeChunk]:
        """
        Extract file-level context (imports, module docstring).

        Args:
            root_node: Root node of the AST
            content: File content
            file_path: Path to the file
            language: Programming language

        Returns:
            CodeChunk for file-level context or None
        """
        try:
            # Extract all imports
            imports = self._extract_imports(root_node, content, language)
            exports = self._extract_exports(root_node, content, language)

            if not imports and not exports:
                # No file-level context to extract
                return None

            # Calculate line range (from first import to last import/export)
            all_statements = imports + exports
            if not all_statements:
                return None

            start_line = 1
            end_line = max(stmt["line"] for stmt in all_statements)

            # Add some buffer for module docstring (first 20 lines or up to first import)
            if imports:
                first_import_line = min(imp["line"] for imp in imports)
                end_line = max(end_line, first_import_line + 5)

            # Extract content (first end_line lines)
            lines = content.split("\n")
            file_content = "\n".join(lines[:end_line])

            # Create file-level chunk
            metadata = {
                "nesting_level": 0,
                "file_imports": imports,
                "file_exports": exports,
                "imports": imports,  # For consistency
                "exports": exports,  # For consistency
                "has_docstring": self._has_module_docstring(root_node, content, language),
                "chunk_name": file_path.name,
            }

            # Merge file_metadata if provided (from file classification)
            if file_metadata:
                metadata.update(file_metadata)

            return CodeChunk(
                content=file_content,
                file_path=str(file_path),
                start_line=start_line,
                end_line=end_line,
                chunk_type="file_context",
                language=language,
                metadata=metadata,
            )
        except Exception as e:
            logger.warning(f"Failed to extract file context from {file_path}: {e}")
            return None

    def _has_module_docstring(self, root_node: Node, content: str, language: str) -> bool:
        """Check if file has a module-level docstring."""
        if language == "python":
            # Check for string literal as first statement
            for child in root_node.children:
                if child.type == "expression_statement":
                    for expr_child in child.children:
                        if expr_child.type == "string":
                            return True
                    break
        return False

    def _generate_chunk_id(self, chunk: CodeChunk) -> str:
        """
        Generate a unique ID for a chunk.

        Args:
            chunk: CodeChunk object

        Returns:
            SHA256 hash as chunk ID
        """
        # Create a unique identifier from file path, line range, and content hash
        content_hash = hashlib.sha256(chunk.content.encode()).hexdigest()[:16]
        chunk_id = hashlib.sha256(
            f"{chunk.file_path}_{chunk.start_line}_{chunk.end_line}_{content_hash}".encode()
        ).hexdigest()
        return chunk_id

    def _fallback_chunk(
        self,
        file_path: Path,
        content: str,
        language: str,
        file_metadata: Optional[Dict[str, Any]] = None
    ) -> List[CodeChunk]:
        """
        Fallback to character-based chunking when AST parsing fails.

        Args:
            file_path: Path to the file
            content: File content
            language: Programming language (or "unknown")
            file_metadata: Optional metadata to add to all chunks

        Returns:
            List of CodeChunk objects
        """
        chunks = []
        content_length = len(content)
        start = 0

        while start < content_length:
            # Calculate end position
            end = min(start + self.max_chunk_size, content_length)

            # Try to find a good break point (newline) near the end
            if end < content_length:
                # Look back up to overlap_size characters for a newline
                search_start = max(end - self.overlap_size, start)
                newline_pos = content.rfind("\n", search_start, end)

                if newline_pos != -1 and newline_pos > start:
                    end = newline_pos + 1

            chunk_content = content[start:end]

            # Calculate line numbers
            start_line = content[:start].count("\n") + 1
            end_line = content[:end].count("\n") + 1

            # Create metadata and merge file_metadata if provided
            metadata = {}
            if file_metadata:
                metadata.update(file_metadata)

            chunk = CodeChunk(
                content=chunk_content,
                file_path=str(file_path),
                start_line=start_line,
                end_line=end_line,
                chunk_type="fallback",
                language=language,
                metadata=metadata,
            )
            chunks.append(chunk)

            # Move start position (with overlap)
            start = end - self.overlap_size if end < content_length else end

        logger.info(f"Created {len(chunks)} fallback chunks from {file_path}")
        return chunks


