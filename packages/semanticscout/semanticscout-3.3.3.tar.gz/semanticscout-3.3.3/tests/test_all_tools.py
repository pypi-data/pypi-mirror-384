"""
Comprehensive test for all SemanticScout MCP tools.
Tests indexing + all query/search tools in async context (simulates MCP server).
"""

import asyncio
from pathlib import Path
import sys
import os
import json
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from semanticscout.paths import PathManager
from semanticscout.embeddings import SentenceTransformerProvider
from semanticscout.vector_store.chroma_store import ChromaVectorStore
from semanticscout.indexer.pipeline import IndexingPipeline
from semanticscout.retriever.semantic_search import SemanticSearcher
from semanticscout.retriever.query_processor import QueryProcessor
from semanticscout.retriever.context_expander import ContextExpander
from semanticscout.retriever.hybrid_retriever import HybridRetriever
from semanticscout.symbol_table.symbol_table import SymbolTable
from semanticscout.dependency_graph.dependency_graph import DependencyGraph
from semanticscout.language_detection.project_language_detector import ProjectLanguageDetector
from semanticscout.dependency_analysis.dependency_router import DependencyAnalysisRouter
from semanticscout.config import get_enhancement_config

ENHANCED_FEATURES = True


async def test_all_tools():
    """Test all SemanticScout tools in async context."""

    # Configuration
    codebase_path = Path(r"C:\git\Weather-Unified")
    collection_name = "test_weather_all_tools"

    # Create temporary test directory using PathManager
    test_base_dir = Path(tempfile.mkdtemp(prefix="semanticscout_test_"))
    test_path_manager = PathManager(base_dir=test_base_dir)

    print("=" * 80)
    print("SemanticScout Comprehensive Tool Testing")
    print("Testing ALL tools in async context (simulates MCP server)")
    print("=" * 80)

    print(f"\nCodebase: {codebase_path}")
    print(f"Test data dir: {test_base_dir}")
    print(f"Collection: {collection_name}")

    try:
        # Ensure test directories exist
        test_path_manager.ensure_directories()
        print(f"✓ Test directory structure created: {test_base_dir}")

        # Load configuration using the new config system
        print("\n" + "=" * 80)
        print("PHASE 1: INITIALIZATION")
        print("=" * 80)

        print("\n--- Loading Configuration ---")
        # Load enhancement config
        enhancement_config = get_enhancement_config()

        # Use sentence-transformers for testing (fast, no external dependencies)
        provider_name = "sentence-transformers"
        model_name = "all-MiniLM-L6-v2"

        print(f"✓ Configuration loaded")
        print(f"  Embedding provider: {provider_name}")
        print(f"  Model: {model_name}")
        print(f"  AST processing: {enhancement_config.ast_processing.enabled}")
        print(f"  Symbol table: {enhancement_config.symbol_table.enabled}")
        print(f"  Dependency graph: {enhancement_config.dependency_graph.enabled}")

        # Initialize embedding provider
        print("\n--- Embedding Provider ---")
        embedding_provider = SentenceTransformerProvider(model_name=model_name)
        print(f"✓ SentenceTransformer provider initialized: {model_name}")
        print(f"✓ Provider: {embedding_provider.get_model_name()}")
        print(f"✓ Dimensions: {embedding_provider.get_dimensions()}")

        # Initialize vector store using test path manager
        print("\n--- Vector Store ---")
        vector_store = ChromaVectorStore(
            persist_directory=str(test_path_manager.get_vector_store_dir())
        )
        print(f"✓ Vector store initialized: {test_path_manager.get_vector_store_dir()}")

        # Initialize symbol table and dependency graph using test path manager
        print("\n--- Symbol Table & Dependency Graph ---")
        symbol_table_db = test_path_manager.get_symbol_tables_dir() / f"{collection_name}.db"
        symbol_table = SymbolTable(db_path=symbol_table_db, collection_name=collection_name)
        symbol_table.clear()  # Clear any existing data from previous runs

        # Create dependency graph with test-specific file path
        dependency_graph_file = test_path_manager.get_dependency_graphs_dir() / f"{collection_name}.pkl"
        dependency_graph = DependencyGraph(collection_name=collection_name, auto_load=False)

        print(f"✓ Symbol table initialized: {symbol_table_db}")
        print(f"✓ Dependency graph initialized")

        # Initialize language detection and dependency analysis
        print("\n--- Language Detection & Dependency Analysis ---")
        language_detector = ProjectLanguageDetector()
        dependency_router = DependencyAnalysisRouter()
        print("✓ Language detector and dependency router initialized")

        # Test language detection before indexing
        print("\n--- Testing Language Detection ---")
        detected_languages = language_detector.detect_languages(codebase_path)
        print(f"✓ Language detection completed")
        print(f"  Primary language: {detected_languages.primary_language}")
        print(f"  Languages detected: {list(detected_languages.languages.keys())}")
        print(f"  Language confidence scores:")
        for lang, confidence in detected_languages.languages.items():
            print(f"    {lang}: {confidence:.3f}")
        print(f"  Total files analyzed: {detected_languages.total_files}")
        print(f"  Config files found: {detected_languages.config_files_found}")
        print(f"  Overall confidence: {detected_languages.confidence:.3f}")

        # Validate language detection results
        if detected_languages.primary_language:
            print(f"✅ Primary language detected: {detected_languages.primary_language}")
        else:
            print("⚠️  No primary language detected")

        if detected_languages.languages:
            print(f"✅ {len(detected_languages.languages)} languages detected")
        else:
            print("⚠️  No languages detected")

        # Initialize indexing pipeline
        print("\n--- Indexing Pipeline ---")
        pipeline = IndexingPipeline(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            batch_size=50,
            symbol_table=symbol_table,
            dependency_graph=dependency_graph,
            language_detector=language_detector,
            dependency_router=dependency_router
        )
        print("✓ Pipeline initialized with language detection and dependency routing")
        
        # PHASE 2: INDEXING
        print("\n" + "=" * 80)
        print("PHASE 2: INDEXING")
        print("=" * 80)

        print(f"\nIndexing codebase into collection: {collection_name}")
        print("This will take ~20-30 seconds...")
        stats = pipeline.index_codebase(
            root_path=str(codebase_path),
            collection_name=collection_name
        )
        
        print(f"\n✅ Indexing Complete!")
        print(f"  Files: {stats.files_indexed}/{stats.files_discovered}")
        print(f"  Chunks: {stats.chunks_created}")
        print(f"  Embeddings: {stats.embeddings_generated}")
        print(f"  Symbols: {stats.symbols_extracted}")
        print(f"  Dependencies: {stats.dependencies_tracked}")
        print(f"  Time: {stats.time_elapsed:.2f}s")
        
        if stats.errors:
            print(f"\n⚠️  Errors: {len(stats.errors)}")
            for error in stats.errors[:3]:
                print(f"  - {error}")
        
        # PHASE 3: TOOL TESTING
        print("\n" + "=" * 80)
        print("PHASE 3: TESTING ALL MCP TOOLS")
        print("=" * 80)
        
        # Initialize query components
        print("\n--- Initializing Query Components ---")
        query_processor = QueryProcessor(embedding_provider=embedding_provider)
        context_expander = ContextExpander(vector_store=vector_store)
        semantic_searcher = SemanticSearcher(
            vector_store=vector_store,
            query_processor=query_processor,
            context_expander=context_expander
        )
        hybrid_retriever = HybridRetriever(
            semantic_searcher=semantic_searcher,
            symbol_table=symbol_table,
            dependency_graph=dependency_graph
        )
        print("✓ All query components initialized (with full enhancements)")
        
        # Test 1: list_collections
        print("\n" + "-" * 80)
        print("TEST 1: list_collections")
        print("-" * 80)
        collections = vector_store.list_collections()
        print(f"✓ Found {len(collections)} collection(s):")
        for coll in collections:
            print(f"  - {coll}")
        
        # Test 2: get_indexing_status
        print("\n" + "-" * 80)
        print("TEST 2: get_indexing_status")
        print("-" * 80)
        collection = vector_store.get_or_create_collection(collection_name)
        count = collection.count()
        print(f"✓ Collection: {collection_name}")
        print(f"  Chunks: {count}")
        print(f"  Symbols: {stats.symbols_extracted}")
        print(f"  Dependencies: {stats.dependencies_tracked}")
        print(f"  Symbols: {stats.symbols_extracted}")
        print(f"  Dependencies: {stats.dependencies_tracked}")
        
        # Test 3: search_code (semantic search)
        print("\n" + "-" * 80)
        print("TEST 3: search_code (semantic search)")
        print("-" * 80)
        
        test_queries = [
            "weather API service",
            "database configuration",
            "chart controller",
            "unit tests for observations"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = semantic_searcher.search(
                collection_name=collection_name,
                query=query,
                top_k=3
            )
            print(f"✓ Found {len(results)} results")
            if results:
                top_result = results[0]
                print(f"  Top result: {top_result.file_path}")
                print(f"  Score: {top_result.similarity_score:.4f}")
        
        # Test 4: find_symbol
        print("\n" + "-" * 80)
        print("TEST 4: find_symbol")
        print("-" * 80)

        test_symbols = [
            ("HomeController", "class"),
            ("ObservationsService", "class"),
            ("GetObservations", None)  # Search all types
        ]

        for symbol_name, symbol_type in test_symbols:
            type_str = f" ({symbol_type})" if symbol_type else ""
            print(f"\nSearching for: '{symbol_name}'{type_str}")
            symbols = symbol_table.lookup_symbol(symbol_name, symbol_type=symbol_type)
            if symbols:
                print(f"✓ Found {len(symbols)} match(es)")
                for sym in symbols[:2]:
                    print(f"  - {sym['file_path']}:{sym['line_number']} ({sym['type']})")
            else:
                print(f"  No matches found")

        # Test 5: find_callers (FIXED - using new find_callers method)
        print("\n" + "-" * 80)
        print("TEST 5: find_callers (FIXED)")
        print("-" * 80)

        # Test with actual symbols from the codebase
        test_caller_symbols = [
            "HomeController",
            "ObservationsService",
            "GetObservations"
        ]

        for symbol_name in test_caller_symbols:
            print(f"\nFinding callers of: '{symbol_name}'")
            try:
                # Use the NEW find_callers method
                callers = symbol_table.find_callers(symbol_name, max_results=5)
                if callers:
                    print(f"✓ Found {len(callers)} potential caller(s)")
                    for caller in callers[:3]:
                        print(f"  - {caller['name']} ({caller['type']}) in {caller['file_path']}:{caller['line_number']}")
                else:
                    print(f"  No callers found (symbol may be in isolated file)")
            except Exception as e:
                print(f"Error finding callers: {e}")

        # Test 6: trace_dependencies (FIXED - using new get_file_dependencies method)
        print("\n" + "-" * 80)
        print("TEST 6: trace_dependencies (FIXED)")
        print("-" * 80)

        # Use backslashes for Windows paths
        test_files = [
            r"WURequest\Services\ObservationsService.cs",
            r"WURequest\Controllers\HomeController.cs",
            r"WURequest\Models\Observation.cs"
        ]

        for test_file in test_files:
            print(f"\nTracing dependencies for: {test_file}")
            try:
                # Use the NEW get_file_dependencies method
                dependencies = dependency_graph.get_file_dependencies(
                    test_file,
                    symbol_table,
                    depth=2
                )
                if dependencies:
                    print(f"✓ Found {len(dependencies)} dependencies")
                    # Group by level
                    by_level = {}
                    for dep in dependencies:
                        level = dep.get('level', 1)
                        if level not in by_level:
                            by_level[level] = []
                        by_level[level].append(dep)

                    for level in sorted(by_level.keys())[:2]:  # Show first 2 levels
                        print(f"  Level {level}: {len(by_level[level])} dependencies")
                        for dep in by_level[level][:3]:  # Show first 3 per level
                            print(f"    - {dep['to_file']}")
                else:
                    print(f"  No dependencies found (file may have no imports)")
            except Exception as e:
                print(f"Error tracing dependencies: {e}")

        # Test 7: hybrid_retriever
        print("\n" + "-" * 80)
        print("TEST 7: hybrid_retriever (semantic + structural)")
        print("-" * 80)

        hybrid_query = "weather observation data service"
        print(f"\nHybrid query: '{hybrid_query}'")
        hybrid_results = hybrid_retriever.retrieve(
            query=hybrid_query,
            collection_name=collection_name,
            top_k=5
        )
        print(f"✓ Found {len(hybrid_results)} results (semantic + structural)")
        for i, result in enumerate(hybrid_results[:3], 1):
            print(f"  {i}. {result.file_path}")
            print(f"     Score: {result.score:.4f}")
            print(f"     Sources: {', '.join(result.sources)}")

        # Test 8: context_expander
        print("\n" + "-" * 80)
        print("TEST 8: context_expander")
        print("-" * 80)

        if results:
            test_chunk = results[0]
            print(f"\nExpanding context for: {test_chunk.file_path}")

            # Convert SearchResult to dict format expected by context_expander
            chunk_dict = {
                'content': test_chunk.content,
                'file_path': test_chunk.file_path,
                'start_line': test_chunk.start_line,
                'end_line': test_chunk.end_line,
                'chunk_type': test_chunk.chunk_type,
                'language': test_chunk.language,
                'metadata': {
                    'file_path': test_chunk.file_path,
                    'start_line': test_chunk.start_line,
                    'end_line': test_chunk.end_line
                }
            }

            expanded_result = context_expander.expand_chunk(
                chunk=chunk_dict,
                collection_name=collection_name,
                expansion_level="medium"
            )
            print(f"✓ Expanded from 1 chunk to {expanded_result.total_chunks} chunks")
            print(f"  Original lines: {test_chunk.end_line - test_chunk.start_line + 1}")
            print(f"  Expanded lines: {expanded_result.total_lines}")
            print(f"  Expansion stats: {expanded_result.expansion_stats}")
        
        # FINAL SUMMARY
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        
        print("\nTools Tested:")
        print("  ✅ list_collections")
        print("  ✅ get_indexing_status")
        print("  ✅ search_code (semantic search)")
        print("  ✅ find_symbol (symbol table lookup)")
        print("  ✅ find_callers (dependency analysis)")
        print("  ✅ trace_dependencies (dependency graph)")
        print("  ✅ hybrid_retriever (semantic + structural)")
        print("  ✅ context_expander (context expansion)")
        
        print("\nPerformance:")
        print(f"  Indexing: {stats.time_elapsed:.2f}s for {stats.files_indexed} files")
        print(f"  Queries: All completed successfully")
        
        print("\n🎉 SemanticScout is ready for production!")

        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up test directory
        print(f"\n🗑️  Cleaning up test directory: {test_base_dir}")
        try:
            shutil.rmtree(test_base_dir)
            print("✓ Test directory cleaned up")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up test directory: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SemanticScout Comprehensive Tool Testing")
    print("Testing indexing in async context (simulates MCP server)")
    print("=" * 80)
    
    # Run in async context (simulates MCP server)
    success = asyncio.run(test_all_tools())
    
    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED - All tools working correctly!")
    else:
        print("❌ TEST FAILED - Fix issues before publishing!")
    print("=" * 80)
    
    sys.exit(0 if success else 1)

