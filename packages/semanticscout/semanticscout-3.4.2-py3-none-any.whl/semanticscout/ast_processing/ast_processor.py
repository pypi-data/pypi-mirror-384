"""
Enhanced AST Processor for symbol extraction and dependency tracking.

This module provides comprehensive AST parsing capabilities using tree-sitter
to extract symbols (functions, classes, interfaces, variables) and track
dependencies (imports, exports, references) from TypeScript and JavaScript files.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Set
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

from ..config import get_enhancement_config

logger = logging.getLogger(__name__)


@dataclass
class Symbol:
    """Represents a code symbol (function, class, interface, variable)."""
    name: str
    type: str  # function, class, interface, variable, method, property
    file_path: str
    line_number: int
    column_number: int
    end_line_number: int
    end_column_number: int
    signature: str
    documentation: str = ""
    scope: str = "public"  # public, private, protected
    is_exported: bool = False
    parent_symbol: Optional[str] = None  # For methods/properties
    metadata: Dict = field(default_factory=dict)


@dataclass
class Dependency:
    """Represents an import/export dependency."""
    from_file: str
    to_file: str  # Imported module path
    imported_symbols: List[str]
    import_type: str  # default, named, namespace, dynamic
    line_number: int
    is_type_only: bool = False
    metadata: Dict = field(default_factory=dict)


@dataclass
class SymbolUsage:
    """Represents where a symbol is used (called, referenced, implemented)."""
    from_symbol: str  # Symbol that uses another symbol
    to_symbol: str    # Symbol being used
    usage_type: str   # call, reference, implements, extends, type_annotation
    from_file: str    # File containing the usage
    to_file: str      # File containing the used symbol (may be same as from_file)
    line_number: int  # Line number of the usage
    column_number: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class ParseResult:
    """Result of parsing a file."""
    file_path: str
    symbols: List[Symbol]
    dependencies: List[Dependency]
    symbol_usage: List[SymbolUsage]
    success: bool
    error: Optional[str] = None
    parse_time_ms: float = 0.0
    metadata: Dict = field(default_factory=dict)


class ASTProcessor:
    """
    Enhanced AST processor for extracting symbols and dependencies.

    This processor uses tree-sitter to parse multiple programming languages,
    extracting detailed symbol information and dependency relationships.

    Supported languages:
    - TypeScript/JavaScript
    - Python
    - C
    - C++
    - C#
    - Go
    - Java
    - Kotlin
    - Rust
    - Swift
    - Haskell
    - Zig
    """

    # Symbol node types for each language
    SYMBOL_NODE_TYPES = {
        "typescript": {
            "function": ["function_declaration", "function_signature", "method_definition", "arrow_function", "function_expression"],
            "class": ["class_declaration"],
            "interface": ["interface_declaration"],
            "type": ["type_alias_declaration"],
            "enum": ["enum_declaration"],
            "variable": ["variable_declarator", "lexical_declaration"],
            "method": ["method_definition", "method_signature"],
            "property": ["property_signature", "public_field_definition"],
        },
        "javascript": {
            "function": ["function_declaration", "method_definition"],
            "class": ["class_declaration"],
            "variable": ["variable_declarator", "lexical_declaration"],
            "method": ["method_definition"],
            "property": ["property_definition"],
        },
        "python": {
            "function": ["function_definition"],
            "class": ["class_definition"],
            "method": ["function_definition"],  # Methods are functions inside classes
            "variable": ["assignment"],
        },
        "c_sharp": {
            "function": ["method_declaration", "local_function_statement"],
            "class": ["class_declaration"],
            "interface": ["interface_declaration"],
            "struct": ["struct_declaration"],
            "enum": ["enum_declaration"],
            "method": ["method_declaration"],
            "property": ["property_declaration"],
        },
        "go": {
            "function": ["function_declaration", "method_declaration"],
            "type": ["type_declaration"],
            "interface": ["interface_type"],
            "struct": ["struct_type"],
            "method": ["method_declaration"],
        },
        "java": {
            "function": ["method_declaration", "constructor_declaration"],
            "class": ["class_declaration"],
            "interface": ["interface_declaration"],
            "enum": ["enum_declaration"],
            "method": ["method_declaration"],
            "constructor": ["constructor_declaration"],
            "field": ["field_declaration"],
        },
        "kotlin": {
            "function": ["function_declaration"],
            "class": ["class_declaration"],
            "interface": ["interface_declaration"],
            "object": ["object_declaration"],
            "method": ["function_declaration"],  # Methods are functions in classes
            "property": ["property_declaration"],
        },
        "rust": {
            "function": ["function_item"],
            "struct": ["struct_item"],
            "enum": ["enum_item"],
            "trait": ["trait_item"],
            "impl": ["impl_item"],
            "method": ["function_item"],  # Methods are functions in impl blocks
        },
        "swift": {
            "function": ["function_declaration"],
            "class": ["class_declaration"],
            "struct": ["struct_declaration"],
            "enum": ["enum_declaration"],
            "protocol": ["protocol_declaration"],
            "method": ["function_declaration"],
            "property": ["property_declaration"],
        },
        "haskell": {
            "function": ["function_declaration", "signature"],
            "type": ["type_declaration"],
            "data": ["data_declaration"],
            "class": ["class_declaration"],
        },
        "zig": {
            "function": ["FnProto"],
            "struct": ["ContainerDecl"],
            "enum": ["ContainerDecl"],
            "variable": ["VarDecl"],
        },
        "c": {
            "function": ["function_definition"],
            "struct": ["type_definition"],  # typedef struct
            "variable": ["declaration"],    # global variables
            "typedef": ["type_definition"], # typedef declarations
        },
        "cpp": {
            "function": ["function_definition"],
            "class": ["class_specifier"],
            "struct": ["struct_specifier", "type_definition"],
            "variable": ["declaration"],
            "method": ["function_definition"],  # Methods are functions inside classes
            "namespace": ["namespace_definition"],
            "template": ["template_declaration"],
        },
    }

    # Import/export node types for each language
    IMPORT_NODE_TYPES = {
        "typescript": ["import_statement", "import_clause"],
        "javascript": ["import_statement", "import_clause"],
        "python": ["import_statement", "import_from_statement"],
        "c_sharp": ["using_directive"],
        "go": ["import_declaration"],
        "java": ["import_declaration"],
        "kotlin": ["import_header"],
        "rust": ["use_declaration"],
        "swift": ["import_declaration"],
        "haskell": ["import_declaration"],
        "zig": ["IMPORT"],
        "c": ["preproc_include"],  # #include statements
        "cpp": ["preproc_include"],  # #include statements (same as C)
    }

    EXPORT_NODE_TYPES = {
        "typescript": ["export_statement"],
        "javascript": ["export_statement"],
        "python": [],  # Python doesn't have explicit exports
        "c_sharp": [],  # C# uses access modifiers
        "go": [],  # Go uses capitalization for exports
        "java": [],  # Java uses access modifiers
        "kotlin": [],  # Kotlin uses access modifiers
        "rust": ["visibility_modifier"],  # pub keyword
        "swift": ["modifiers"],  # public, open keywords
        "haskell": ["exports"],
        "zig": ["PUB"],
        "c": [],  # C uses header files for exports
        "cpp": [],  # C++ uses header files for exports
    }

    # Language file extensions
    LANGUAGE_EXTENSIONS = {
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".py": "python",
        ".cs": "c_sharp",
        ".go": "go",
        ".hs": "haskell",
        ".java": "java",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".rs": "rust",
        ".swift": "swift",
        ".zig": "zig",
        ".c": "c",
        ".h": "c",  # C header files
        ".cpp": "cpp",
        ".cxx": "cpp",
        ".cc": "cpp",
        ".hpp": "cpp",  # C++ header files
        ".hxx": "cpp",
        ".hh": "cpp",
    }
    
    def __init__(self, cache_enabled: bool = None):
        """
        Initialize the AST processor.
        
        Args:
            cache_enabled: Enable AST caching. If None, uses config setting.
        """
        self.config = get_enhancement_config()
        
        # Determine cache setting
        if cache_enabled is None:
            cache_enabled = self.config.ast_processing.cache_parsed_trees
        
        self.cache_enabled = cache_enabled
        self._parsers = {}  # Cache parsers by language
        
        # Initialize cache if enabled
        if self.cache_enabled:
            from .ast_cache import ASTCache
            self.cache = ASTCache()
        else:
            self.cache = None
    
    def parse_file(self, file_path: Path, content: Optional[str] = None) -> ParseResult:
        """
        Parse a file and extract symbols and dependencies.
        
        Args:
            file_path: Path to the file to parse
            content: Optional file content (if None, reads from file_path)
            
        Returns:
            ParseResult containing symbols, dependencies, and metadata
        """
        import time
        start_time = time.time()
        
        try:
            # Read content if not provided
            # Use utf-8-sig to automatically strip BOM if present
            # BOM causes byte offset misalignment with tree-sitter
            if content is None:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
            
            # Check file size limit
            max_size_bytes = self.config.ast_processing.max_file_size_mb * 1024 * 1024
            if len(content.encode('utf-8')) > max_size_bytes:
                return ParseResult(
                    file_path=str(file_path),
                    symbols=[],
                    dependencies=[],
                    symbol_usage=[],
                    success=False,
                    error=f"File exceeds size limit ({self.config.ast_processing.max_file_size_mb}MB)"
                )
            
            # Detect language
            language = self._detect_language(file_path)
            if not language:
                return ParseResult(
                    file_path=str(file_path),
                    symbols=[],
                    dependencies=[],
                    symbol_usage=[],
                    success=False,
                    error="Unsupported file type"
                )
            
            # Check cache
            if self.cache:
                cached_result = self.cache.get(file_path, content)
                if cached_result:
                    logger.debug(f"Using cached AST for {file_path}")
                    return cached_result
            
            # Parse the file
            parser = self._get_parser(language)
            if not parser:
                return ParseResult(
                    file_path=str(file_path),
                    symbols=[],
                    dependencies=[],
                    symbol_usage=[],
                    success=False,
                    error=f"Parser not available for {language}"
                )
            
            tree = parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node
            
            # Extract symbols and dependencies
            symbols = self._extract_symbols(root_node, content, str(file_path), language)
            dependencies = self._extract_dependencies(root_node, content, str(file_path), language)

            # Extract symbol usage
            symbol_usage = self._extract_symbol_usage(root_node, content, str(file_path), language, symbols)

            parse_time_ms = (time.time() - start_time) * 1000

            result = ParseResult(
                file_path=str(file_path),
                symbols=symbols,
                dependencies=dependencies,
                symbol_usage=symbol_usage,
                success=True,
                error=None,
                parse_time_ms=parse_time_ms,
                metadata={
                    "language": language,
                    "symbol_count": len(symbols),
                    "dependency_count": len(dependencies),
                    "usage_count": len(symbol_usage),
                }
            )
            
            # Cache the result
            if self.cache:
                self.cache.set(file_path, content, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}", exc_info=True)
            parse_time_ms = (time.time() - start_time) * 1000
            return ParseResult(
                file_path=str(file_path),
                symbols=[],
                dependencies=[],
                symbol_usage=[],
                success=False,
                error=str(e),
                parse_time_ms=parse_time_ms
            )
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        suffix = Path(file_path).suffix.lower()
        return self.LANGUAGE_EXTENSIONS.get(suffix)
    
    def _get_parser(self, language: str):
        """Get or create a tree-sitter parser for the given language."""
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
    
    def _extract_symbols(self, root_node: Node, content: str, file_path: str, language: str) -> List[Symbol]:
        """Extract all symbols from the AST."""
        symbols = []
        
        # Get symbol node types for this language
        symbol_types = self.SYMBOL_NODE_TYPES.get(language, {})
        
        # Extract functions
        for node_type in symbol_types.get("function", []):
            for node in self._find_nodes_by_type(root_node, node_type):
                symbol = self._create_function_symbol(node, content, file_path, language)
                if symbol:
                    symbols.append(symbol)

        # Extract functions from variable declarations (TypeScript/JavaScript)
        if language in ["typescript", "javascript"]:
            symbols.extend(self._extract_functions_from_variables(root_node, content, file_path, language))
        
        # Extract classes
        for node_type in symbol_types.get("class", []):
            for node in self._find_nodes_by_type(root_node, node_type):
                symbol = self._create_class_symbol(node, content, file_path, language)
                if symbol:
                    symbols.append(symbol)
                    # Also extract class members
                    symbols.extend(self._extract_class_members(node, content, file_path, language, symbol.name))
        
        # Extract interfaces (TypeScript only)
        if language == "typescript":
            for node_type in symbol_types.get("interface", []):
                for node in self._find_nodes_by_type(root_node, node_type):
                    symbol = self._create_interface_symbol(node, content, file_path, language)
                    if symbol:
                        symbols.append(symbol)
        
        # Extract type aliases (TypeScript only)
        if language == "typescript":
            for node_type in symbol_types.get("type", []):
                for node in self._find_nodes_by_type(root_node, node_type):
                    symbol = self._create_type_symbol(node, content, file_path, language)
                    if symbol:
                        symbols.append(symbol)

        # Extract enums (TypeScript only)
        if language == "typescript":
            for node_type in symbol_types.get("enum", []):
                for node in self._find_nodes_by_type(root_node, node_type):
                    symbol = self._create_enum_symbol(node, content, file_path, language)
                    if symbol:
                        symbols.append(symbol)

        # Extract C/C++-specific constructs
        if language in ["c", "cpp"]:
            # Extract structs/typedefs
            for node_type in symbol_types.get("struct", []):
                for node in self._find_nodes_by_type(root_node, node_type):
                    symbol = self._create_c_struct_symbol(node, content, file_path, language)
                    if symbol:
                        symbols.append(symbol)

            # Extract global variables
            for node_type in symbol_types.get("variable", []):
                for node in self._find_nodes_by_type(root_node, node_type):
                    symbol = self._create_c_variable_symbol(node, content, file_path, language)
                    if symbol:
                        symbols.append(symbol)

        # Extract C++-specific constructs
        if language == "cpp":
            # Extract namespaces
            for node_type in symbol_types.get("namespace", []):
                for node in self._find_nodes_by_type(root_node, node_type):
                    symbol = self._create_cpp_namespace_symbol(node, content, file_path, language)
                    if symbol:
                        symbols.append(symbol)

            # Extract templates
            for node_type in symbol_types.get("template", []):
                for node in self._find_nodes_by_type(root_node, node_type):
                    symbol = self._create_cpp_template_symbol(node, content, file_path, language)
                    if symbol:
                        symbols.append(symbol)

        # Extract Java-specific constructs
        if language == "java":
            # Extract constructors
            for node_type in symbol_types.get("constructor", []):
                for node in self._find_nodes_by_type(root_node, node_type):
                    symbol = self._create_java_constructor_symbol(node, content, file_path, language)
                    if symbol:
                        symbols.append(symbol)

            # Extract fields
            for node_type in symbol_types.get("field", []):
                for node in self._find_nodes_by_type(root_node, node_type):
                    symbol = self._create_java_field_symbol(node, content, file_path, language)
                    if symbol:
                        symbols.append(symbol)

            # Extract enums
            for node_type in symbol_types.get("enum", []):
                for node in self._find_nodes_by_type(root_node, node_type):
                    symbol = self._create_java_enum_symbol(node, content, file_path, language)
                    if symbol:
                        symbols.append(symbol)

        return symbols

    def _extract_functions_from_variables(self, root_node: Node, content: str, file_path: str, language: str) -> List[Symbol]:
        """Extract functions declared as variables (const func = () => {})."""
        functions = []

        # Find all variable declarators
        for var_declarator in self._find_nodes_by_type(root_node, "variable_declarator"):
            # Check if the variable contains a function
            function_symbol = self._create_function_from_variable(var_declarator, content, file_path, language)
            if function_symbol:
                functions.append(function_symbol)

        return functions

    def _extract_dependencies(self, root_node: Node, content: str, file_path: str, language: str) -> List[Dependency]:
        """Extract import/export dependencies."""
        dependencies = []

        # Get import node types for this language
        import_types = self.IMPORT_NODE_TYPES.get(language, [])

        # Find import statements
        for import_type in import_types:
            for import_node in self._find_nodes_by_type(root_node, import_type):
                dep = self._create_import_dependency(import_node, content, file_path, language)
                if dep:
                    dependencies.append(dep)

        return dependencies

    def _extract_symbol_usage(self, root_node: Node, content: str, file_path: str, language: str, symbols: List[Symbol]) -> List[SymbolUsage]:
        """Extract symbol usage relationships (calls, references, etc.)."""
        usage_list = []

        # Create a set of symbol names for quick lookup
        symbol_names = {symbol.name for symbol in symbols}

        # Extract call expressions
        for call_node in self._find_nodes_by_type(root_node, "call_expression"):
            usage = self._extract_call_usage(call_node, content, file_path, language, symbol_names)
            if usage:
                usage_list.extend(usage)

        # Extract member expressions (method calls)
        for member_node in self._find_nodes_by_type(root_node, "member_expression"):
            usage = self._extract_member_usage(member_node, content, file_path, language, symbol_names)
            if usage:
                usage_list.extend(usage)

        # Extract type annotations (TypeScript)
        if language == "typescript":
            for type_node in self._find_nodes_by_type(root_node, "type_annotation"):
                usage = self._extract_type_usage(type_node, content, file_path, language, symbol_names)
                if usage:
                    usage_list.extend(usage)

        # Extract identifier references
        for identifier_node in self._find_nodes_by_type(root_node, "identifier"):
            usage = self._extract_identifier_usage(identifier_node, content, file_path, language, symbol_names)
            if usage:
                usage_list.append(usage)

        return usage_list

    def _find_nodes_by_type(self, node: Node, node_type: str) -> List[Node]:
        """Recursively find all nodes of a specific type."""
        nodes = []
        
        if node.type == node_type:
            nodes.append(node)
        
        for child in node.children:
            nodes.extend(self._find_nodes_by_type(child, node_type))
        
        return nodes
    
    def _get_node_text(self, node: Optional[Node], content: str) -> str:
        """Get the text content of a node."""
        if node is None:
            return ""
        # Convert to bytes, slice with byte offsets, decode back to string
        # This is necessary because tree-sitter uses byte offsets, not character offsets
        content_bytes = content.encode('utf-8')
        return content_bytes[node.start_byte:node.end_byte].decode('utf-8')

    def _create_function_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol object for a function declaration."""
        try:
            # Get function name - handle different languages
            name_node = node.child_by_field_name('name')
            name = None

            if name_node:
                name = self._get_node_text(name_node, content)
            elif language in ["c", "cpp"]:
                # For C/C++ functions, look for function_declarator -> identifier
                for child in node.children:
                    if child.type == "function_declarator":
                        for grandchild in child.children:
                            if grandchild.type == "identifier":
                                name = self._get_node_text(grandchild, content)
                                break
                        break

            if not name:
                return None

            # Get signature
            signature = self._get_function_signature(node, content)

            # Get documentation
            documentation = self._extract_documentation(node, content, language)

            # Determine scope and export status
            scope, is_exported = self._determine_scope_and_export(node, content)

            return Symbol(
                name=name,
                type="function",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope=scope,
                is_exported=is_exported,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create function symbol: {e}")
            return None

    def _create_class_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol object for a class declaration."""
        try:
            # Get class name
            name_node = node.child_by_field_name('name')
            if not name_node:
                return None

            name = self._get_node_text(name_node, content)
            if not name:
                return None

            # Get class signature (including extends/implements)
            signature = self._get_class_signature(node, content)

            # Get documentation
            documentation = self._extract_documentation(node, content, language)

            # Determine scope and export status
            scope, is_exported = self._determine_scope_and_export(node, content)

            return Symbol(
                name=name,
                type="class",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope=scope,
                is_exported=is_exported,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create class symbol: {e}")
            return None

    def _create_interface_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol object for an interface declaration."""
        try:
            # Get interface name
            name_node = node.child_by_field_name('name')
            if not name_node:
                return None

            name = self._get_node_text(name_node, content)
            if not name:
                return None

            # Get interface signature
            signature = f"interface {name}"

            # Get documentation
            documentation = self._extract_documentation(node, content, language)

            # Determine scope and export status
            scope, is_exported = self._determine_scope_and_export(node, content)

            return Symbol(
                name=name,
                type="interface",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope=scope,
                is_exported=is_exported,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create interface symbol: {e}")
            return None

    def _create_type_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol object for a type alias declaration."""
        try:
            # Get type name
            name_node = node.child_by_field_name('name')
            if not name_node:
                return None

            name = self._get_node_text(name_node, content)
            if not name:
                return None

            # Get type signature
            signature = f"type {name}"

            # Get documentation
            documentation = self._extract_documentation(node, content, language)

            # Determine scope and export status
            scope, is_exported = self._determine_scope_and_export(node, content)

            return Symbol(
                name=name,
                type="type",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope=scope,
                is_exported=is_exported,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create type symbol: {e}")
            return None

    def _create_function_from_variable(self, var_node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol object for a function declared as a variable (const func = () => {})."""
        try:
            # Get variable name
            name_node = var_node.child_by_field_name('name')
            if not name_node:
                return None

            name = self._get_node_text(name_node, content)
            if not name:
                return None

            # Check if the variable value is a function (arrow_function or function_expression)
            value_node = var_node.child_by_field_name('value')
            if not value_node:
                return None

            # Check if it's an arrow function or function expression
            if value_node.type not in ["arrow_function", "function_expression"]:
                return None

            # Get function signature from the arrow function or function expression
            signature = self._get_function_signature_from_variable(var_node, value_node, content, name)

            # Get documentation
            documentation = self._extract_documentation(var_node, content, language)

            # Determine scope and export status from the parent lexical_declaration
            scope, is_exported = self._determine_scope_and_export_from_variable(var_node, content)

            return Symbol(
                name=name,
                type="function",
                file_path=file_path,
                line_number=var_node.start_point[0] + 1,
                column_number=var_node.start_point[1],
                end_line_number=value_node.end_point[0] + 1,
                end_column_number=value_node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope=scope,
                is_exported=is_exported,
                metadata={"node_type": "function_variable", "function_type": value_node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create function from variable: {e}")
            return None

    def _create_enum_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol object for an enum declaration."""
        try:
            # Get enum name
            name_node = node.child_by_field_name('name')
            if not name_node:
                return None

            name = self._get_node_text(name_node, content)
            if not name:
                return None

            # Get enum signature
            signature = f"enum {name}"

            # Get documentation
            documentation = self._extract_documentation(node, content, language)

            # Determine scope and export status
            scope, is_exported = self._determine_scope_and_export(node, content)

            return Symbol(
                name=name,
                type="enum",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope=scope,
                is_exported=is_exported,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create enum symbol: {e}")
            return None

    def _extract_class_members(self, class_node: Node, content: str, file_path: str, language: str, class_name: str) -> List[Symbol]:
        """Extract methods and properties from a class."""
        members = []

        # Find class body
        body_node = class_node.child_by_field_name('body')
        if not body_node:
            return members

        # Extract methods
        for method_node in self._find_nodes_by_type(body_node, "method_definition"):
            symbol = self._create_method_symbol(method_node, content, file_path, language, class_name)
            if symbol:
                members.append(symbol)

        return members

    def _create_method_symbol(self, node: Node, content: str, file_path: str, language: str, parent_class: str) -> Optional[Symbol]:
        """Create a Symbol object for a method."""
        try:
            # Get method name
            name_node = node.child_by_field_name('name')
            if not name_node:
                return None

            name = self._get_node_text(name_node, content)
            if not name:
                return None

            # Get signature
            signature = self._get_function_signature(node, content)

            # Get documentation
            documentation = self._extract_documentation(node, content, language)

            # Determine scope
            scope = self._determine_method_scope(node, content)

            return Symbol(
                name=name,
                type="method",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope=scope,
                is_exported=False,  # Methods are not directly exported
                parent_symbol=parent_class,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create method symbol: {e}")
            return None

    def _create_c_struct_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol object for a C struct/typedef declaration."""
        try:
            # For type_definition nodes, look for the type identifier
            name = None

            # Look for type_identifier (typedef name)
            for child in node.children:
                if child.type == "type_identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return None

            # Get struct signature
            signature = self._get_node_text(node, content).split('\n')[0].strip()
            if len(signature) > 200:
                signature = signature[:197] + "..."

            # Get documentation (look for comments before the struct)
            documentation = self._extract_documentation(node, content, language)

            return Symbol(
                name=name,
                type="struct",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope="public",  # C structs are typically public
                is_exported=True,  # Structs in headers are exported
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create C struct symbol: {e}")
            return None

    def _create_c_variable_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol object for a C global variable declaration."""
        try:
            # For declaration nodes, look for the identifier
            name = None

            # Look for init_declarator or identifier
            for child in node.children:
                if child.type == "init_declarator":
                    # Look for identifier within init_declarator
                    for grandchild in child.children:
                        if grandchild.type == "identifier":
                            name = self._get_node_text(grandchild, content)
                            break
                    break
                elif child.type == "identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return None

            # Get variable signature (type + name)
            signature = self._get_node_text(node, content).strip()
            if len(signature) > 200:
                signature = signature[:197] + "..."

            # Check if it's static (private scope)
            scope = "public"
            for child in node.children:
                if child.type == "storage_class_specifier" and "static" in self._get_node_text(child, content):
                    scope = "private"
                    break

            return Symbol(
                name=name,
                type="variable",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation="",
                scope=scope,
                is_exported=(scope == "public"),
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create C variable symbol: {e}")
            return None

    def _create_cpp_namespace_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol object for a C++ namespace declaration."""
        try:
            # For namespace_definition nodes, look for the namespace identifier
            name = None

            for child in node.children:
                if child.type == "namespace_identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return None

            # Get namespace signature
            signature = self._get_node_text(node, content).split('\n')[0].strip()
            if len(signature) > 200:
                signature = signature[:197] + "..."

            return Symbol(
                name=name,
                type="namespace",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation="",
                scope="public",
                is_exported=True,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create C++ namespace symbol: {e}")
            return None

    def _create_cpp_template_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol object for a C++ template declaration."""
        try:
            # For template_declaration nodes, look for the template name
            name = None

            # Templates can contain functions, classes, etc.
            # Look for the main declaration inside the template
            for child in node.children:
                if child.type in ["function_definition", "class_specifier"]:
                    # Extract name from the templated declaration
                    if child.type == "function_definition":
                        for grandchild in child.children:
                            if grandchild.type == "function_declarator":
                                for ggchild in grandchild.children:
                                    if ggchild.type == "identifier":
                                        name = self._get_node_text(ggchild, content)
                                        break
                                break
                    elif child.type == "class_specifier":
                        for grandchild in child.children:
                            if grandchild.type == "type_identifier":
                                name = self._get_node_text(grandchild, content)
                                break
                    break

            if not name:
                return None

            # Get template signature
            signature = self._get_node_text(node, content).split('\n')[0].strip()
            if len(signature) > 200:
                signature = signature[:197] + "..."

            return Symbol(
                name=name,
                type="template",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation="",
                scope="public",
                is_exported=True,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create C++ template symbol: {e}")
            return None

    def _get_function_signature(self, node: Node, content: str) -> str:
        """Extract function signature."""
        try:
            # Get the full function declaration text (first line)
            full_text = self._get_node_text(node, content)
            lines = full_text.split('\n')

            # Find the line with the opening brace or arrow
            signature_lines = []
            for line in lines:
                signature_lines.append(line)
                if '{' in line or '=>' in line:
                    break

            signature = ' '.join(signature_lines).strip()

            # Limit signature length
            if len(signature) > 200:
                signature = signature[:197] + "..."

            return signature
        except Exception:
            return ""

    def _get_class_signature(self, node: Node, content: str) -> str:
        """Extract class signature including extends/implements."""
        try:
            # Get class name
            name_node = node.child_by_field_name('name')
            if not name_node:
                return ""

            name = self._get_node_text(name_node, content)
            signature = f"class {name}"

            # Check for extends
            heritage_node = node.child_by_field_name('heritage')
            if heritage_node:
                heritage_text = self._get_node_text(heritage_node, content)
                signature += f" {heritage_text}"

            return signature
        except Exception:
            return ""

    def _extract_documentation(self, node: Node, content: str, language: str) -> str:
        """Extract JSDoc or comment documentation."""
        try:
            # Look for previous sibling comment
            if node.prev_sibling and 'comment' in node.prev_sibling.type:
                doc_text = self._get_node_text(node.prev_sibling, content)
                # Clean up JSDoc formatting
                doc_text = doc_text.replace('/**', '').replace('*/', '').replace('*', '').strip()
                return doc_text

            return ""
        except Exception:
            return ""

    def _determine_scope_and_export(self, node: Node, content: str) -> tuple[str, bool]:
        """Determine if a symbol is public/private and exported."""
        scope = "public"
        is_exported = False

        # Check parent nodes for export keyword
        current = node.parent
        while current:
            if current.type == "export_statement":
                is_exported = True
                break
            current = current.parent

        # Check for private/protected modifiers (TypeScript)
        for child in node.children:
            if child.type in ["public", "private", "protected"]:
                scope = child.type
                break

        return scope, is_exported

    def _determine_method_scope(self, node: Node, content: str) -> str:
        """Determine method scope (public/private/protected)."""
        # Check for access modifiers
        for child in node.children:
            if child.type in ["public", "private", "protected"]:
                return child.type

        # Check if method name starts with underscore (convention for private)
        name_node = node.child_by_field_name('name')
        if name_node:
            name = self._get_node_text(name_node, content)
            if name.startswith('_'):
                return "private"

        return "public"

    def _get_function_signature_from_variable(self, var_node: Node, func_node: Node, content: str, name: str) -> str:
        """Extract function signature from a variable declaration containing a function."""
        try:
            # Start with the variable name
            signature_parts = []

            # Check if it's exported by looking at parent lexical_declaration
            parent = var_node.parent
            if parent and parent.parent and parent.parent.type == "export_statement":
                signature_parts.append("export")

            # Add const/let/var
            if parent:
                for child in parent.children:
                    if child.type in ["const", "let", "var"]:
                        signature_parts.append(child.type)
                        break

            # Add function name
            signature_parts.append(name)
            signature_parts.append("=")

            # Check for async
            if func_node.type == "arrow_function":
                for child in func_node.children:
                    if child.type == "async":
                        signature_parts.append("async")
                        break

            # Get parameters
            params_node = func_node.child_by_field_name('parameters') or func_node.child_by_field_name('parameter')
            if params_node:
                params_text = self._get_node_text(params_node, content)
                signature_parts.append(params_text)

            # Get return type annotation if present
            type_annotation = None
            for child in func_node.children:
                if child.type == "type_annotation":
                    type_annotation = self._get_node_text(child, content)
                    break

            if type_annotation:
                signature_parts.append(type_annotation)

            # Add arrow for arrow functions
            if func_node.type == "arrow_function":
                signature_parts.append("=>")

            signature = " ".join(signature_parts)

            # Limit signature length
            if len(signature) > 200:
                signature = signature[:197] + "..."

            return signature
        except Exception:
            return f"{name} = function"

    def _determine_scope_and_export_from_variable(self, var_node: Node, content: str) -> tuple[str, bool]:
        """Determine scope and export status from a variable declaration."""
        scope = "public"
        is_exported = False

        # Check if the variable is in an export statement
        parent = var_node.parent  # lexical_declaration
        if parent and parent.parent and parent.parent.type == "export_statement":
            is_exported = True

        return scope, is_exported

    def _extract_call_usage(self, call_node: Node, content: str, file_path: str, language: str, symbol_names: set) -> List[SymbolUsage]:
        """Extract function call usage from a call_expression node."""
        usage_list = []

        try:
            # Get the function being called
            function_node = call_node.child_by_field_name('function')
            if not function_node:
                return usage_list

            # Handle different types of function calls
            called_symbol = None

            if function_node.type == "identifier":
                # Direct function call: functionName()
                called_symbol = self._get_node_text(function_node, content)
            elif function_node.type == "member_expression":
                # Method call: object.method()
                property_node = function_node.child_by_field_name('property')
                if property_node:
                    called_symbol = self._get_node_text(property_node, content)

            if called_symbol and called_symbol in symbol_names:
                # Find the containing function/symbol that makes this call
                containing_symbol = self._find_containing_symbol(call_node, content)

                usage = SymbolUsage(
                    from_symbol=containing_symbol or "global",
                    to_symbol=called_symbol,
                    usage_type="call",
                    from_file=file_path,
                    to_file=file_path,  # Assume same file for now
                    line_number=call_node.start_point[0] + 1,
                    column_number=call_node.start_point[1],
                    metadata={"node_type": "call_expression"}
                )
                usage_list.append(usage)

        except Exception as e:
            logger.debug(f"Failed to extract call usage: {e}")

        return usage_list

    def _extract_member_usage(self, member_node: Node, content: str, file_path: str, language: str, symbol_names: set) -> List[SymbolUsage]:
        """Extract member access usage from a member_expression node."""
        usage_list = []

        try:
            # Get the property being accessed
            property_node = member_node.child_by_field_name('property')
            if not property_node:
                return usage_list

            accessed_symbol = self._get_node_text(property_node, content)

            if accessed_symbol and accessed_symbol in symbol_names:
                # Find the containing function/symbol that accesses this member
                containing_symbol = self._find_containing_symbol(member_node, content)

                usage = SymbolUsage(
                    from_symbol=containing_symbol or "global",
                    to_symbol=accessed_symbol,
                    usage_type="reference",
                    from_file=file_path,
                    to_file=file_path,  # Assume same file for now
                    line_number=member_node.start_point[0] + 1,
                    column_number=member_node.start_point[1],
                    metadata={"node_type": "member_expression"}
                )
                usage_list.append(usage)

        except Exception as e:
            logger.debug(f"Failed to extract member usage: {e}")

        return usage_list

    def _extract_type_usage(self, type_node: Node, content: str, file_path: str, language: str, symbol_names: set) -> List[SymbolUsage]:
        """Extract type annotation usage from a type_annotation node."""
        usage_list = []

        try:
            # Find type identifiers within the type annotation
            for type_id_node in self._find_nodes_by_type(type_node, "type_identifier"):
                type_name = self._get_node_text(type_id_node, content)

                if type_name and type_name in symbol_names:
                    containing_symbol = self._find_containing_symbol(type_node, content)

                    usage = SymbolUsage(
                        from_symbol=containing_symbol or "global",
                        to_symbol=type_name,
                        usage_type="type_annotation",
                        from_file=file_path,
                        to_file=file_path,  # Assume same file for now
                        line_number=type_id_node.start_point[0] + 1,
                        column_number=type_id_node.start_point[1],
                        metadata={"node_type": "type_annotation"}
                    )
                    usage_list.append(usage)

        except Exception as e:
            logger.debug(f"Failed to extract type usage: {e}")

        return usage_list

    def _extract_identifier_usage(self, identifier_node: Node, content: str, file_path: str, language: str, symbol_names: set) -> Optional[SymbolUsage]:
        """Extract identifier reference usage."""
        try:
            identifier_name = self._get_node_text(identifier_node, content)

            if not identifier_name or identifier_name not in symbol_names:
                return None

            # Skip if this identifier is part of a declaration (not a usage)
            if self._is_declaration_context(identifier_node):
                return None

            # Skip if this is already handled by call or member expressions
            parent = identifier_node.parent
            if parent and parent.type in ["call_expression", "member_expression"]:
                return None

            containing_symbol = self._find_containing_symbol(identifier_node, content)

            return SymbolUsage(
                from_symbol=containing_symbol or "global",
                to_symbol=identifier_name,
                usage_type="reference",
                from_file=file_path,
                to_file=file_path,  # Assume same file for now
                line_number=identifier_node.start_point[0] + 1,
                column_number=identifier_node.start_point[1],
                metadata={"node_type": "identifier"}
            )

        except Exception as e:
            logger.debug(f"Failed to extract identifier usage: {e}")
            return None

    def _find_containing_symbol(self, node: Node, content: str) -> Optional[str]:
        """Find the symbol (function, method, class) that contains this node."""
        current = node.parent

        while current:
            # Check for function declarations
            if current.type in ["function_declaration", "method_definition", "arrow_function"]:
                name_node = current.child_by_field_name('name')
                if name_node:
                    return self._get_node_text(name_node, content)

            # Check for variable declarators with functions
            elif current.type == "variable_declarator":
                name_node = current.child_by_field_name('name')
                value_node = current.child_by_field_name('value')
                if name_node and value_node and value_node.type in ["arrow_function", "function_expression"]:
                    return self._get_node_text(name_node, content)

            # Check for class declarations
            elif current.type == "class_declaration":
                name_node = current.child_by_field_name('name')
                if name_node:
                    return self._get_node_text(name_node, content)

            current = current.parent

        return None

    def _is_declaration_context(self, identifier_node: Node) -> bool:
        """Check if an identifier is in a declaration context (not a usage)."""
        parent = identifier_node.parent

        if not parent:
            return False

        # Check if it's the name in a declaration
        if parent.type in ["function_declaration", "class_declaration", "interface_declaration",
                          "type_alias_declaration", "variable_declarator", "enum_declaration"]:
            name_field = parent.child_by_field_name('name')
            if name_field == identifier_node:
                return True

        # Check if it's a parameter name
        if parent.type in ["formal_parameter", "required_parameter", "optional_parameter"]:
            return True

        return False

    def _create_import_dependency(self, node: Node, content: str, file_path: str, language: str) -> Optional[Dependency]:
        """Create a Dependency object for an import statement."""
        try:
            # Handle C# using directives
            if language == "c_sharp" and node.type == "using_directive":
                logger.debug(f"Processing C# using directive in {file_path}")
                result = self._create_csharp_using_dependency(node, content, file_path)
                if result:
                    logger.debug(f"Created C# dependency: {result.to_file}")
                return result

            # Handle Rust use declarations
            if language == "rust" and node.type == "use_declaration":
                logger.debug(f"Processing Rust use declaration in {file_path}")
                result = self._create_rust_use_dependency(node, content, file_path)
                if result:
                    logger.debug(f"Created Rust dependency: {result.to_file}")
                return result

            # Handle Python imports
            if language == "python":
                return self._create_python_import_dependency(node, content, file_path)

            # Handle C/C++ includes
            if language in ["c", "cpp"] and node.type == "preproc_include":
                logger.debug(f"Processing {language.upper()} include in {file_path}")
                result = self._create_c_include_dependency(node, content, file_path)
                if result:
                    logger.debug(f"Created {language.upper()} dependency: {result.to_file}")
                return result

            # Handle Java imports
            if language == "java" and node.type == "import_declaration":
                logger.debug(f"Processing Java import in {file_path}")
                result = self._create_java_import_dependency(node, content, file_path)
                if result:
                    logger.debug(f"Created Java dependency: {result.to_file}")
                return result

            # Handle JavaScript/TypeScript imports
            # Get the source (imported module path)
            source_node = node.child_by_field_name('source')
            if not source_node:
                return None

            source_text = self._get_node_text(source_node, content)
            # Remove quotes
            to_file = source_text.strip('"').strip("'")

            # Extract imported symbols
            imported_symbols = []
            import_type = "default"
            is_type_only = False

            # Check for type-only import by looking at the full import statement
            full_import_text = self._get_node_text(node, content)
            if full_import_text.strip().startswith('import type '):
                is_type_only = True

            # Check for import clause
            for child in node.children:
                if child.type == "import_clause":
                    # Also check clause text for type keyword
                    clause_text = self._get_node_text(child, content)
                    if clause_text.strip().startswith('type '):
                        is_type_only = True

                    # Extract named imports
                    for named_imports in self._find_nodes_by_type(child, "named_imports"):
                        for import_spec in self._find_nodes_by_type(named_imports, "import_specifier"):
                            name_node = import_spec.child_by_field_name('name')
                            if name_node:
                                imported_symbols.append(self._get_node_text(name_node, content))
                        import_type = "named"

                    # Check for namespace import
                    for namespace_import in self._find_nodes_by_type(child, "namespace_import"):
                        name_node = namespace_import.child_by_field_name('name')
                        if name_node:
                            imported_symbols.append(self._get_node_text(name_node, content))
                        import_type = "namespace"

                    # Check for default import
                    if child.child_by_field_name('name'):
                        name_node = child.child_by_field_name('name')
                        imported_symbols.append(self._get_node_text(name_node, content))
                        import_type = "default"

            return Dependency(
                from_file=file_path,
                to_file=to_file,
                imported_symbols=imported_symbols,
                import_type=import_type,
                line_number=node.start_point[0] + 1,
                is_type_only=is_type_only,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create import dependency: {e}")
            return None

    def _create_csharp_using_dependency(self, node: Node, content: str, file_path: str) -> Optional[Dependency]:
        """Create a Dependency object for a C# using directive."""
        try:
            # C# using directive structure:
            # using_directive
            #   - using (keyword)
            #   - identifier or qualified_name (namespace)
            #   - ; (semicolon)

            # Find the namespace node (identifier or qualified_name)
            namespace_node = None
            for child in node.children:
                if child.type in ["identifier", "qualified_name", "name"]:
                    namespace_node = child
                    break

            if not namespace_node:
                return None

            # Get the namespace text
            namespace = self._get_node_text(namespace_node, content)

            # Skip system/external namespaces - only track project namespaces
            # Common external namespace prefixes
            external_prefixes = [
                "System", "Microsoft", "Newtonsoft", "NUnit", "Xunit", "Moq",
                "MongoDB", "EntityFramework", "AutoMapper", "Serilog", "FluentValidation",
                "MediatR", "Dapper", "StackExchange", "Npgsql", "MySql", "Oracle",
                "Amazon", "Azure", "Google", "RestSharp", "Polly", "Hangfire"
            ]
            if any(namespace.startswith(prefix) for prefix in external_prefixes):
                logger.debug(f"Skipping external namespace: {namespace}")
                return None

            # Also skip if namespace doesn't contain a dot (likely external single-word namespace)
            # Project namespaces typically have structure like: ProjectName.Module.SubModule
            if '.' not in namespace:
                logger.debug(f"Skipping single-word namespace: {namespace}")
                return None

            logger.debug(f"Keeping project namespace: {namespace}")

            # For C#, store the namespace as metadata but use a placeholder for to_file
            # The actual file mapping will be resolved later using the symbol table
            # We mark this as a namespace dependency that needs resolution
            return Dependency(
                from_file=file_path,
                to_file=f"namespace:{namespace}",  # Mark as namespace for later resolution
                imported_symbols=[namespace],
                import_type="namespace",
                line_number=node.start_point[0] + 1,
                is_type_only=False,
                metadata={
                    "node_type": node.type,
                    "language": "c_sharp",
                    "namespace": namespace,
                    "needs_resolution": True
                }
            )
        except Exception as e:
            logger.warning(f"Failed to create C# using dependency: {e}")
            return None

    def _create_python_import_dependency(self, node: Node, content: str, file_path: str) -> Optional[Dependency]:
        """Create a Dependency object for a Python import statement."""
        try:
            imported_symbols = []
            to_file = ""
            import_type = "default"

            # Handle "import module" statements
            if node.type == "import_statement":
                # import_statement
                #   - import (keyword)
                #   - dotted_name or aliased_import
                for child in node.children:
                    if child.type == "dotted_name":
                        to_file = self._get_node_text(child, content)
                        imported_symbols.append(to_file)
                        import_type = "namespace"
                        break  # Take first dotted_name as the module
                    elif child.type == "aliased_import":
                        # aliased_import: name as alias
                        name_node = child.child_by_field_name('name')
                        if name_node:
                            to_file = self._get_node_text(name_node, content)
                            imported_symbols.append(to_file)
                            import_type = "namespace"
                            break

            # Handle "from module import symbol" statements
            elif node.type == "import_from_statement":
                # import_from_statement
                #   - from (keyword)
                #   - dotted_name (module)
                #   - import (keyword)
                #   - dotted_name or wildcard or aliased_import or import_list

                # Find the module name (first dotted_name after 'from')
                found_from = False
                for child in node.children:
                    if child.type == "from":
                        found_from = True
                    elif found_from and child.type == "dotted_name" and not to_file:
                        to_file = self._get_node_text(child, content)
                        break

                # Find what's being imported (after 'import' keyword)
                found_import = False
                for child in node.children:
                    if child.type == "import":
                        found_import = True
                    elif found_import:
                        if child.type == "wildcard":
                            imported_symbols.append("*")
                            import_type = "wildcard"
                        elif child.type == "dotted_name":
                            imported_symbols.append(self._get_node_text(child, content))
                            import_type = "named"
                        elif child.type == "aliased_import":
                            name_node = child.child_by_field_name('name')
                            if name_node:
                                imported_symbols.append(self._get_node_text(name_node, content))
                                import_type = "named"
                        elif child.type == "import_list":
                            # Multiple imports: from module import (a, b, c)
                            for import_child in child.children:
                                if import_child.type == "dotted_name":
                                    imported_symbols.append(self._get_node_text(import_child, content))
                                elif import_child.type == "aliased_import":
                                    name_node = import_child.child_by_field_name('name')
                                    if name_node:
                                        imported_symbols.append(self._get_node_text(name_node, content))
                            import_type = "named"

            if not to_file:
                return None

            return Dependency(
                from_file=file_path,
                to_file=to_file,
                imported_symbols=imported_symbols,
                import_type=import_type,
                line_number=node.start_point[0] + 1,
                is_type_only=False,
                metadata={"node_type": node.type, "language": "python"}
            )
        except Exception as e:
            logger.warning(f"Failed to create Python import dependency: {e}")
            return None

    def _create_rust_use_dependency(self, node: Node, content: str, file_path: str) -> Optional[Dependency]:
        """Create a Dependency object for a Rust use declaration."""
        try:
            # Rust use declaration structure:
            # use_declaration
            #   - use (keyword)
            #   - use_clause (the actual import path)
            #   - ; (semicolon)

            # Find the use_clause node
            use_clause = None
            for child in node.children:
                if child.type == "use_clause":
                    use_clause = child
                    break

            if not use_clause:
                return None

            # Extract the module path and imported symbols
            module_path, imported_symbols, import_type = self._parse_rust_use_clause(use_clause, content)

            if not module_path:
                return None

            # For Rust, we need to distinguish between:
            # 1. External crate imports (e.g., use serde::Serialize)
            # 2. Local module imports (e.g., use crate::config::Config)
            # 3. Standard library imports (e.g., use std::collections::HashMap)

            # Mark external crates and std library for different handling
            is_external = self._is_external_rust_crate(module_path)
            is_std = module_path.startswith("std::")

            # Store metadata about the import type
            metadata = {
                "node_type": node.type,
                "language": "rust",
                "is_external_crate": is_external,
                "is_std_library": is_std,
                "needs_resolution": not (is_external or is_std)  # Only local modules need resolution
            }

            return Dependency(
                from_file=file_path,
                to_file=f"rust_module:{module_path}",  # Mark as Rust module for later resolution
                imported_symbols=imported_symbols,
                import_type=import_type,
                line_number=node.start_point[0] + 1,
                is_type_only=False,
                metadata=metadata
            )
        except Exception as e:
            logger.warning(f"Failed to create Rust use dependency: {e}")
            return None

    def _parse_rust_use_clause(self, use_clause: Node, content: str) -> tuple[str, list[str], str]:
        """
        Parse a Rust use clause to extract module path, imported symbols, and import type.

        Returns:
            Tuple of (module_path, imported_symbols, import_type)
        """
        try:
            # Handle different use clause patterns:
            # 1. Simple path: use std::collections::HashMap
            # 2. Glob import: use std::collections::*
            # 3. List import: use std::collections::{HashMap, HashSet}
            # 4. Aliased import: use std::collections::HashMap as Map
            # 5. Self import: use std::collections::{self, HashMap}

            module_path = ""
            imported_symbols = []
            import_type = "simple"

            # Traverse the use clause to build the path
            path_parts = []
            self._extract_rust_path_parts(use_clause, content, path_parts)

            if not path_parts:
                return "", [], "simple"

            # Check for different import patterns
            last_part = path_parts[-1]

            if last_part == "*":
                # Glob import: use module::*
                module_path = "::".join(path_parts[:-1])
                imported_symbols = ["*"]
                import_type = "glob"
            elif "{" in last_part and "}" in last_part:
                # List import: use module::{item1, item2}
                module_path = "::".join(path_parts[:-1])
                import_list = last_part.strip("{}")
                imported_symbols = [item.strip() for item in import_list.split(",") if item.strip()]
                import_type = "list"
            elif " as " in last_part:
                # Aliased import: use module::Item as Alias
                module_path = "::".join(path_parts[:-1])
                parts = last_part.split(" as ")
                if len(parts) == 2:
                    imported_symbols = [parts[1].strip()]  # Use the alias
                    import_type = "aliased"
            else:
                # Simple import: use module::Item
                if len(path_parts) > 1:
                    module_path = "::".join(path_parts[:-1])
                    imported_symbols = [path_parts[-1]]
                else:
                    module_path = path_parts[0]
                    imported_symbols = [path_parts[0]]
                import_type = "simple"

            return module_path, imported_symbols, import_type

        except Exception as e:
            logger.warning(f"Failed to parse Rust use clause: {e}")
            return "", [], "simple"

    def _extract_rust_path_parts(self, node: Node, content: str, path_parts: list) -> None:
        """Recursively extract path parts from a Rust use clause."""
        try:
            if node.type == "identifier":
                path_parts.append(self._get_node_text(node, content))
            elif node.type == "scoped_identifier":
                # Handle scoped identifiers like crate::module
                for child in node.children:
                    if child.type in ["identifier", "scoped_identifier"]:
                        self._extract_rust_path_parts(child, content, path_parts)
            elif node.type == "use_list":
                # Handle use lists like {item1, item2}
                list_content = self._get_node_text(node, content)
                path_parts.append(list_content)
            elif node.type == "use_as_clause":
                # Handle aliased imports
                clause_content = self._get_node_text(node, content)
                path_parts.append(clause_content)
            elif node.type == "use_wildcard":
                # Handle glob imports
                path_parts.append("*")
            else:
                # Recursively process children
                for child in node.children:
                    if child.type not in ["use", "::", ";"]:  # Skip keywords and separators
                        self._extract_rust_path_parts(child, content, path_parts)
        except Exception as e:
            logger.debug(f"Error extracting Rust path parts: {e}")

    def _is_external_rust_crate(self, module_path: str) -> bool:
        """
        Determine if a Rust module path refers to an external crate.

        External crates are those that:
        1. Don't start with 'crate::', 'self::', or 'super::'
        2. Don't start with 'std::'
        3. Are not relative paths
        """
        if not module_path:
            return False

        # Local module indicators
        local_prefixes = ["crate::", "self::", "super::"]
        if any(module_path.startswith(prefix) for prefix in local_prefixes):
            return False

        # Standard library
        if module_path.startswith("std::"):
            return False

        # If it doesn't have any of the above prefixes, it's likely an external crate
        # unless it's a single identifier that could be a local module
        if "::" not in module_path:
            # Single identifier could be either external crate or local module
            # We'll assume it's external for now, but this could be refined
            return True

        # Multi-part path without local prefixes is likely external
        return True

    def _create_c_include_dependency(self, node: Node, content: str, file_path: str) -> Optional[Dependency]:
        """Create a Dependency object for a C #include statement."""
        try:
            # C include structure:
            # preproc_include
            #   - #include (keyword)
            #   - system_lib_string (<stdio.h>) OR string_literal ("main.h")

            include_path = ""
            import_type = "system"  # Default to system include

            # Look for the include path
            for child in node.children:
                if child.type == "system_lib_string":
                    # System include like <stdio.h>
                    include_path = self._get_node_text(child, content)
                    # Remove < and > brackets
                    include_path = include_path.strip('<>')
                    import_type = "system"
                    break
                elif child.type == "string_literal":
                    # Local include like "main.h"
                    include_path = self._get_node_text(child, content)
                    # Remove quotes
                    include_path = include_path.strip('"')
                    import_type = "local"
                    break

            if not include_path:
                return None

            # For local includes, try to resolve the path relative to current file
            to_file = include_path
            if import_type == "local":
                # For local includes, we'll store the relative path
                # The dependency graph can resolve this later
                to_file = include_path
            else:
                # For system includes, mark them as system dependencies
                to_file = f"system:{include_path}"

            return Dependency(
                from_file=file_path,
                to_file=to_file,
                imported_symbols=[include_path],  # Store the include name as symbol
                import_type=import_type,
                line_number=node.start_point[0] + 1,
                is_type_only=False,
                metadata={
                    "node_type": node.type,
                    "language": "c",
                    "include_path": include_path,
                    "is_system": (import_type == "system")
                }
            )
        except Exception as e:
            logger.warning(f"Failed to create C include dependency: {e}")
            return None

    def _create_java_constructor_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol for a Java constructor."""
        try:
            # Get constructor name (should match class name)
            name = None
            for child in node.children:
                if child.type == "identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return None

            # Get constructor signature
            signature = self._get_java_method_signature(node, content)

            # Get documentation
            documentation = self._extract_documentation(node, content, language)

            # Determine scope and export status
            scope, is_exported = self._determine_java_scope_and_export(node, content)

            return Symbol(
                name=name,
                type="constructor",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope=scope,
                is_exported=is_exported,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create Java constructor symbol: {e}")
            return None

    def _create_java_field_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol for a Java field."""
        try:
            # Get field name from variable_declarator
            name = None
            for child in node.children:
                if child.type == "variable_declarator":
                    for grandchild in child.children:
                        if grandchild.type == "identifier":
                            name = self._get_node_text(grandchild, content)
                            break
                    break

            if not name:
                return None

            # Get field signature (type + name)
            signature = self._get_node_text(node, content).strip()
            if len(signature) > 200:
                signature = signature[:197] + "..."

            # Get documentation
            documentation = self._extract_documentation(node, content, language)

            # Determine scope and export status
            scope, is_exported = self._determine_java_scope_and_export(node, content)

            return Symbol(
                name=name,
                type="field",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope=scope,
                is_exported=is_exported,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create Java field symbol: {e}")
            return None

    def _create_java_enum_symbol(self, node: Node, content: str, file_path: str, language: str) -> Optional[Symbol]:
        """Create a Symbol for a Java enum."""
        try:
            # Get enum name
            name = None
            for child in node.children:
                if child.type == "identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return None

            # Get enum signature
            signature = self._get_node_text(node, content).strip()
            if len(signature) > 200:
                signature = signature[:197] + "..."

            # Get documentation
            documentation = self._extract_documentation(node, content, language)

            # Determine scope and export status
            scope, is_exported = self._determine_java_scope_and_export(node, content)

            return Symbol(
                name=name,
                type="enum",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                signature=signature,
                documentation=documentation,
                scope=scope,
                is_exported=is_exported,
                metadata={"node_type": node.type}
            )
        except Exception as e:
            logger.warning(f"Failed to create Java enum symbol: {e}")
            return None

    def _get_java_method_signature(self, node: Node, content: str) -> str:
        """Get Java method signature including modifiers, return type, name, and parameters."""
        try:
            signature_parts = []

            # Get modifiers (public, private, static, etc.)
            for child in node.children:
                if child.type == "modifiers":
                    modifiers = self._get_node_text(child, content).strip()
                    if modifiers:
                        signature_parts.append(modifiers)
                    break

            # For constructors, no return type
            if node.type == "constructor_declaration":
                # Get constructor name
                for child in node.children:
                    if child.type == "identifier":
                        name = self._get_node_text(child, content)
                        signature_parts.append(name)
                        break
            else:
                # For methods, get return type and name
                return_type = None
                method_name = None

                for child in node.children:
                    if child.type in ["void_type", "type_identifier", "generic_type", "array_type"]:
                        return_type = self._get_node_text(child, content)
                    elif child.type == "identifier":
                        method_name = self._get_node_text(child, content)

                if return_type:
                    signature_parts.append(return_type)
                if method_name:
                    signature_parts.append(method_name)

            # Get parameters
            for child in node.children:
                if child.type == "formal_parameters":
                    params = self._get_node_text(child, content)
                    signature_parts.append(params)
                    break

            return " ".join(signature_parts)
        except Exception as e:
            logger.warning(f"Failed to get Java method signature: {e}")
            return self._get_node_text(node, content)[:100]

    def _determine_java_scope_and_export(self, node: Node, content: str) -> tuple[str, bool]:
        """Determine scope and export status for Java symbols."""
        try:
            # Check for modifiers
            for child in node.children:
                if child.type == "modifiers":
                    modifiers_text = self._get_node_text(child, content).lower()

                    if "private" in modifiers_text:
                        return "private", False
                    elif "protected" in modifiers_text:
                        return "protected", True
                    elif "public" in modifiers_text:
                        return "public", True
                    else:
                        # Package-private (default in Java)
                        return "package", True

            # No explicit modifier means package-private
            return "package", True
        except Exception as e:
            logger.warning(f"Failed to determine Java scope: {e}")
            return "public", True

    def _create_java_import_dependency(self, node: Node, content: str, file_path: str) -> Optional[Dependency]:
        """Create a Dependency object for a Java import statement."""
        try:
            # Java import structure: import java.util.List;
            # The scoped_identifier contains the full import path
            import_path = None

            for child in node.children:
                if child.type == "scoped_identifier":
                    import_path = self._get_node_text(child, content)
                    break

            if not import_path:
                return None

            # Extract the class name (last part of the import)
            parts = import_path.split('.')
            class_name = parts[-1] if parts else import_path

            # Determine import type
            import_type = "external"
            if import_path.startswith("java."):
                import_type = "standard_library"
            elif import_path.startswith("javax."):
                import_type = "standard_library"
            elif import_path.startswith("com.") or import_path.startswith("org."):
                import_type = "external"
            else:
                import_type = "local"

            return Dependency(
                from_file=file_path,
                to_file=import_path,
                imported_symbols=[class_name],
                import_type=import_type,
                line_number=node.start_point[0] + 1,
                is_type_only=False,
                metadata={
                    "full_import_path": import_path,
                    "package": ".".join(parts[:-1]) if len(parts) > 1 else "",
                    "is_wildcard": False
                }
            )
        except Exception as e:
            logger.warning(f"Failed to create Java import dependency: {e}")
            return None
