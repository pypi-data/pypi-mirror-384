"""
Comprehensive test of all SemanticScout MCP tools on moRFeus_Qt repository.

Similar to test_all_tools.py (Weather Unified), but for the moRFeus_Qt C# codebase.

Tests:
1. Index codebase (full indexing)
2. Search code (semantic search)
3. Find symbol (symbol lookup)
4. Find callers (call graph)
5. Trace dependencies (dependency analysis)
6. Get indexing status (metadata)
"""

import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from semanticscout.embeddings import SentenceTransformerProvider
from semanticscout.vector_store.chroma_store import ChromaVectorStore
from semanticscout.symbol_table.symbol_table import SymbolTable
from semanticscout.dependency_graph.dependency_graph import DependencyGraph
from semanticscout.indexer.pipeline import IndexingPipeline
from semanticscout.retriever.semantic_search import SemanticSearcher
from semanticscout.retriever.query_processor import QueryProcessor
from semanticscout.language_detection.project_language_detector import ProjectLanguageDetector
from semanticscout.dependency_analysis.dependency_router import DependencyAnalysisRouter

# Configuration
MORFEUS_QT_PATH = Path("C:/git/moRFeus_Qt")
COLLECTION_NAME = "morfeus_qt_test"
DATA_DIR = Path.home() / ".semanticscout-test-morfeus"


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def test_language_detection():
    """Test 0: Language detection on moRFeus_Qt Python project."""
    print_section("TEST 0: Language Detection")

    if not MORFEUS_QT_PATH.exists():
        print(f"❌ moRFeus_Qt repository not found at {MORFEUS_QT_PATH}")
        print("   Please clone the repository or update the path.")
        return False

    print(f"Testing language detection on: {MORFEUS_QT_PATH}")

    # Initialize language detector
    language_detector = ProjectLanguageDetector()

    print("\nRunning language detection...")
    detected_languages = language_detector.detect_languages(MORFEUS_QT_PATH)

    print(f"\nLanguage Detection Results:")
    print(f"  Primary language: {detected_languages.primary_language}")
    print(f"  Total files analyzed: {detected_languages.total_files}")
    print(f"  Config files found: {detected_languages.config_files_found}")
    print(f"  Overall confidence: {detected_languages.confidence:.3f}")

    print(f"\nLanguage confidence breakdown:")
    for lang, confidence in sorted(detected_languages.languages.items(), key=lambda x: x[1], reverse=True):
        print(f"    {lang}: {confidence:.3f}")

    # Test dependency router with detected languages
    print(f"\nTesting dependency analysis routing:")
    dependency_router = DependencyAnalysisRouter()
    strategies = dependency_router.get_registered_strategies()
    print(f"  Available strategies: {strategies}")

    # Validate results for Python project (moRFeus_Qt is actually a Python project)
    success = True

    # Check if Python is detected (should be primary or at least present)
    if detected_languages.primary_language != "python" and "python" not in detected_languages.languages:
        print(f"❌ Python not detected in moRFeus_Qt project")
        success = False

    # Check for reasonable file count
    if detected_languages.total_files < 5:
        print(f"❌ Too few files detected: {detected_languages.total_files}")
        success = False

    # Check for Python config files
    python_config_files = [f for f in detected_languages.config_files_found if f.endswith(('.py', 'setup.py', 'requirements.txt', 'pyproject.toml'))]
    if not python_config_files:
        print(f"⚠️  No Python config files detected (expected setup.py, requirements.txt, etc.)")
        # This is a warning, not a failure

    # Check overall confidence
    if detected_languages.confidence < 0.2:
        print(f"❌ Overall confidence too low: {detected_languages.confidence}")
        success = False

    if success:
        print(f"✅ Language detection successful")
        if detected_languages.primary_language == "python":
            print(f"✅ Python correctly identified as primary language")
        elif "python" in detected_languages.languages:
            print(f"✅ Python detected with confidence: {detected_languages.languages['python']:.3f}")
        print(f"✅ Analyzed {detected_languages.total_files} files with {detected_languages.confidence:.3f} confidence")
    else:
        print(f"❌ Language detection failed validation")

    return success


def test_index_codebase():
    """Test 1: Index the moRFeus_Qt codebase."""
    print_section("TEST 1: Index moRFeus_Qt Codebase")
    
    if not MORFEUS_QT_PATH.exists():
        print(f"❌ moRFeus_Qt repository not found at {MORFEUS_QT_PATH}")
        print("   Please clone the repository or update the path.")
        return None, None, None, None
    
    print(f"Codebase: {MORFEUS_QT_PATH}")
    print(f"Data dir: {DATA_DIR}")
    print(f"Collection: {COLLECTION_NAME}")

    # Clean up old data directory
    import shutil
    if DATA_DIR.exists():
        print(f"\n🗑️  Cleaning up old data directory...")
        shutil.rmtree(DATA_DIR)

    # Create fresh data directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Fresh data directory ready: {DATA_DIR}")

    # Parse configuration from SEMANTICSCOUT_CONFIG_JSON (same as MCP client)
    print("\nLoading configuration...")
    config_json = '{"embedding":{"provider":"sentence-transformers","model":"all-MiniLM-L6-v2"},"features":{"enable_ast_processing":true,"enable_symbol_table":true,"enable_dependency_graph":true},"performance":{"max_file_size_mb":10,"max_files_per_batch":50,"enable_parallel_processing":true}}'
    config_data = json.loads(config_json)

    embedding_config = config_data.get("embedding", {})
    provider_name = embedding_config.get("provider", "sentence-transformers")
    model_name = embedding_config.get("model", "all-MiniLM-L6-v2")

    print(f"✓ Configuration loaded from JSON")
    print(f"  Embedding provider: {provider_name}")
    print(f"  Model: {model_name}")

    # Create components based on config
    print("\nInitializing embedding provider...")
    if provider_name == "sentence-transformers":
        embedding_provider = SentenceTransformerProvider(model_name=model_name)
        print(f"✓ SentenceTransformer provider initialized: {model_name}")
    else:
        raise ValueError(f"Unsupported embedding provider for tests: {provider_name}")

    print(f"✓ Provider: {embedding_provider.get_model_name()}")
    print(f"✓ Dimensions: {embedding_provider.get_dimensions()}")

    vector_store = ChromaVectorStore(persist_directory=str(DATA_DIR / "chroma"))
    print(f"✓ Vector store initialized: {DATA_DIR / 'chroma'}")

    # Use test data directory for database files
    symbol_table_db = DATA_DIR / "symbol_tables" / f"{COLLECTION_NAME}.db"
    symbol_table_db.parent.mkdir(parents=True, exist_ok=True)

    symbol_table = SymbolTable(db_path=symbol_table_db, collection_name=COLLECTION_NAME)
    symbol_table.clear()  # Clear any existing data from previous runs
    dependency_graph = DependencyGraph(collection_name=COLLECTION_NAME, auto_load=False)
    print(f"✓ Symbol table initialized: {symbol_table_db}")
    print(f"✓ Dependency graph initialized")

    # Initialize language detection and dependency analysis
    language_detector = ProjectLanguageDetector()
    dependency_router = DependencyAnalysisRouter()
    print("✓ Language detector and dependency router initialized")

    # Create indexing pipeline
    pipeline = IndexingPipeline(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        symbol_table=symbol_table,
        dependency_graph=dependency_graph,
        language_detector=language_detector,
        dependency_router=dependency_router
    )
    
    # Index codebase
    print("\n⏳ Indexing codebase (this may take a few minutes)...")
    start_time = time.time()

    result = pipeline.index_codebase(
        root_path=str(MORFEUS_QT_PATH),
        collection_name=COLLECTION_NAME,
    )

    elapsed = time.time() - start_time

    print(f"\n✅ Indexing complete in {elapsed:.2f}s")
    print(f"   Files indexed: {result.files_indexed}")
    print(f"   Chunks created: {result.chunks_created}")
    print(f"   Symbols extracted: {result.symbols_extracted}")
    print(f"   Dependencies tracked: {result.dependencies_tracked}")
    
    return embedding_provider, vector_store, symbol_table, dependency_graph


def test_search_code(vector_store, embedding_provider):
    """Test 2: Semantic code search."""
    print_section("TEST 2: Semantic Code Search")
    
    if not vector_store or not embedding_provider:
        print("⏭️  Skipping (indexing failed)")
        return
    
    # Create semantic search
    query_processor = QueryProcessor(embedding_provider=embedding_provider)
    search = SemanticSearcher(
        vector_store=vector_store,
        query_processor=query_processor,
    )
    
    # Test queries
    queries = [
        "USB device communication",
        "frequency control",
        "GUI initialization",
        "error handling",
        "serial port communication",
    ]
    
    print("\n🔎 Running search queries...")
    for query in queries:
        results = search.search(
            query=query,
            collection_name=COLLECTION_NAME,
            top_k=3,
        )
        
        print(f"\n  Query: '{query}'")
        print(f"  Results: {len(results)}")

        for i, result in enumerate(results[:2], 1):  # Show top 2
            print(f"    {i}. {result.file_path} "
                  f"(score: {result.similarity_score:.3f})")
            # Show snippet
            snippet = result.content[:100].replace('\n', ' ')
            print(f"       {snippet}...")


def test_find_symbol(symbol_table):
    """Test 3: Symbol lookup (FIXED - using lookup_symbol method)."""
    print_section("TEST 3: Symbol Lookup (FIXED)")

    if not symbol_table:
        print("⏭️  Skipping (indexing failed)")
        return

    # Test symbol searches with actual Python symbols from moRFeus_Qt
    test_symbols = [
        ("MoRFeus", "class"),  # Main device class
        ("MainWindow", "class"),  # Qt main window
        ("Worker", "class"),  # Thread worker class
        ("find", "function"),  # Device finder function
        ("__init__", None),  # Search all types
    ]

    print("\n📚 Searching for symbols...")
    for symbol_name, symbol_type in test_symbols:
        type_str = f" ({symbol_type})" if symbol_type else ""
        print(f"\n  Symbol: '{symbol_name}'{type_str}")

        # Use the FIXED lookup_symbol method
        results = symbol_table.lookup_symbol(
            name=symbol_name,
            symbol_type=symbol_type
        )

        print(f"  Found: {len(results)} matches")

        for result in results[:2]:  # Show top 2
            print(f"    - {result.get('name', 'unknown')} "
                  f"({result.get('type', 'unknown')}) "
                  f"in {result.get('file_path', 'unknown')}:{result.get('line_number', '?')}")


def test_find_callers(symbol_table):
    """Test 4: Find callers (FIXED - using new find_callers method)."""
    print_section("TEST 4: Find Callers (FIXED)")

    if not symbol_table:
        print("⏭️  Skipping (indexing failed)")
        return

    # Test with actual Python symbols from moRFeus_Qt
    test_caller_symbols = [
        "MoRFeus",  # Main device class
        "MainWindow",  # Qt main window
        "Worker",  # Thread worker
        "find"  # Device finder function
    ]

    print("\n🔗 Finding callers for symbols...")
    for symbol_name in test_caller_symbols:
        print(f"\n  Symbol: '{symbol_name}'")

        try:
            # Use the NEW find_callers method
            callers = symbol_table.find_callers(symbol_name, max_results=5)
            if callers:
                print(f"  ✓ Found {len(callers)} potential caller(s)")
                for caller in callers[:3]:
                    print(f"    - {caller['name']} ({caller['type']}) "
                          f"in {caller['file_path']}:{caller['line_number']}")
            else:
                print(f"    No callers found (symbol may be in isolated file)")
        except Exception as e:
            print(f"    Error: {e}")


def test_trace_dependencies(dependency_graph, symbol_table):
    """Test 5: Trace file dependencies (FIXED - using new get_file_dependencies method)."""
    print_section("TEST 5: Trace Dependencies (FIXED)")

    if not dependency_graph or not symbol_table:
        print("⏭️  Skipping (indexing failed)")
        return

    # Get dependency graph stats
    stats = dependency_graph.get_statistics()

    print("\n🕸️  Dependency Graph Statistics:")
    print(f"   Total nodes: {stats.get('total_nodes', 0)}")
    print(f"   Total edges: {stats.get('total_edges', 0)}")
    print(f"   File nodes: {stats.get('file_nodes', 0)}")

    # Test tracing dependencies for actual Python files in moRFeus_Qt
    test_files = [
        "moRFeusQt\\mrf.py",  # Main device module (4 dependencies)
        "moRFeusQt\\mrfqt.py",  # Qt GUI module (8 dependencies)
        "moRFeusQt\\TxRx.py"  # Thread worker module (5 dependencies)
    ]

    print("\n🔍 Tracing file dependencies...")
    for test_file in test_files:
        print(f"\n  File: {test_file}")

        try:
            # Use the NEW get_file_dependencies method
            dependencies = dependency_graph.get_file_dependencies(
                test_file,
                symbol_table,
                depth=2
            )
            if dependencies:
                print(f"  ✓ Found {len(dependencies)} dependencies")
                # Group by level
                by_level = {}
                for dep in dependencies:
                    level = dep.get('level', 1)
                    if level not in by_level:
                        by_level[level] = []
                    by_level[level].append(dep)

                for level in sorted(by_level.keys())[:2]:  # Show first 2 levels
                    print(f"    Level {level}: {len(by_level[level])} dependencies")
                    for dep in by_level[level][:3]:  # Show first 3 per level
                        print(f"      - {dep['to_file']}")
            else:
                print(f"    No dependencies found (file may have no imports)")
        except Exception as e:
            print(f"    Error: {e}")

    print(f"   Symbol nodes: {stats.get('symbol_nodes', 0)}")
    print(f"   File dependencies: {stats.get('file_dependencies', 0)}")
    print(f"   Symbol dependencies: {stats.get('symbol_dependencies', 0)}")


def test_get_indexing_status(vector_store, symbol_table):
    """Test 6: Get indexing status and metadata."""
    print_section("TEST 6: Indexing Status")
    
    if not vector_store or not symbol_table:
        print("⏭️  Skipping (indexing failed)")
        return
    
    print("\n📊 Collection Status:")
    
    # Vector store stats
    try:
        collection = vector_store.client.get_collection(name=COLLECTION_NAME)
        count = collection.count()
        print(f"   Vector store chunks: {count}")
    except Exception as e:
        print(f"   Vector store: Error - {e}")
    
    # Symbol table stats
    try:
        cursor = symbol_table.conn.execute(
            "SELECT COUNT(*) FROM symbols WHERE collection_name = ?",
            (COLLECTION_NAME,)
        )
        symbol_count = cursor.fetchone()[0]
        print(f"   Symbol table entries: {symbol_count}")
    except Exception as e:
        print(f"   Symbol table: Error - {e}")
    
    # File metadata
    try:
        cursor = symbol_table.conn.execute(
            "SELECT COUNT(*) FROM file_metadata WHERE collection_name = ?",
            (COLLECTION_NAME,)
        )
        file_count = cursor.fetchone()[0]
        print(f"   Indexed files: {file_count}")
    except Exception as e:
        print(f"   File metadata: Error - {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  SemanticScout MCP Tools - moRFeus_Qt Comprehensive Test")
    print("=" * 80)

    # Test 0: Language detection
    language_success = test_language_detection()
    if not language_success:
        print("\n⚠️  Language detection failed - continuing with other tests")

    # Test 1: Index codebase
    embedding_provider, vector_store, symbol_table, dependency_graph = test_index_codebase()

    if not vector_store:
        print("\n❌ Indexing failed - cannot continue with other tests")
        return

    # Test 2: Search code
    test_search_code(vector_store, embedding_provider)

    # Test 3: Find symbol
    test_find_symbol(symbol_table)

    # Test 4: Find callers
    test_find_callers(symbol_table)

    # Test 5: Trace dependencies (FIXED - now requires symbol_table)
    test_trace_dependencies(dependency_graph, symbol_table)

    # Test 6: Get indexing status
    test_get_indexing_status(vector_store, symbol_table)

    print("\n" + "=" * 80)
    if language_success:
        print("  ✅ All tests complete (including language detection)!")
    else:
        print("  ⚠️  All tests complete (language detection had issues)!")
    print("=" * 80)


if __name__ == "__main__":
    main()

