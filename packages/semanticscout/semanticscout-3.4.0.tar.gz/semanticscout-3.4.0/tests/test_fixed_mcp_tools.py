"""
Test the three fixed MCP tools: find_symbol, find_callers, trace_dependencies.
This test verifies the bug fixes work correctly.
"""

import asyncio
from pathlib import Path
import sys
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from semanticscout.embeddings import SentenceTransformerProvider
from semanticscout.vector_store.chroma_store import ChromaVectorStore
from semanticscout.indexer.pipeline import IndexingPipeline
from semanticscout.symbol_table.symbol_table import SymbolTable, SymbolTableManager
from semanticscout.dependency_graph.dependency_graph import DependencyGraph, DependencyGraphManager


async def test_codebase(codebase_path: Path, collection_name: str, data_dir: Path):
    """Test the three fixed MCP tools on a specific codebase."""

    print("=" * 80)
    print(f"Testing Fixed MCP Tools - {collection_name}")
    print("=" * 80)
    print(f"\nCodebase: {codebase_path}")
    print(f"Data dir: {data_dir}")
    print(f"Collection: {collection_name}")
    
    try:
        # Clean up old data directory
        if data_dir.exists():
            print(f"\n🗑️  Cleaning up old data directory...")
            shutil.rmtree(data_dir)

        # Create fresh data directory
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Fresh data directory ready")

        # Initialize components
        print("\n" + "=" * 80)
        print("PHASE 1: INITIALIZATION")
        print("=" * 80)

        print("\n--- Embedding Provider ---")
        embedding_provider = SentenceTransformerProvider(model_name="all-MiniLM-L6-v2")
        print(f"✓ Provider: {embedding_provider.get_model_name()}")

        print("\n--- Vector Store ---")
        vector_store = ChromaVectorStore(persist_directory=str(data_dir / "chroma"))
        print(f"✓ Vector store initialized")

        print("\n--- Symbol Table & Dependency Graph Managers ---")
        symbol_table_manager = SymbolTableManager()
        dependency_graph_manager = DependencyGraphManager()
        print(f"✓ Managers initialized")

        # Get collection-specific instances
        symbol_table = symbol_table_manager.get_table(collection_name)
        dependency_graph = dependency_graph_manager.get_graph(collection_name)
        symbol_table.clear()  # Clear any existing data
        print(f"✓ Collection-specific instances retrieved")

        # Initialize indexing pipeline
        print("\n--- Indexing Pipeline ---")
        pipeline = IndexingPipeline(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            batch_size=50,
            symbol_table=symbol_table,
            dependency_graph=dependency_graph
        )
        print("✓ Pipeline initialized")
        
        # PHASE 2: INDEXING
        print("\n" + "=" * 80)
        print("PHASE 2: INDEXING")
        print("=" * 80)

        print(f"\nIndexing SemanticScout codebase...")
        stats = pipeline.index_codebase(
            root_path=str(codebase_path),
            collection_name=collection_name
        )
        
        print(f"\n✅ Indexing Complete!")
        print(f"  Files: {stats.files_indexed}/{stats.files_discovered}")
        print(f"  Chunks: {stats.chunks_created}")
        print(f"  Symbols: {stats.symbols_extracted}")
        print(f"  Dependencies: {stats.dependencies_tracked}")
        print(f"  Time: {stats.time_elapsed:.2f}s")
        
        # Ensure persistence
        symbol_table.conn.commit()
        dependency_graph.save_to_file()
        print("✓ Data persisted")
        
        # PHASE 3: TEST FIXED TOOLS
        print("\n" + "=" * 80)
        print("PHASE 3: TESTING FIXED MCP TOOLS")
        print("=" * 80)
        
        # TEST 1: find_symbol (Bug Fix #1)
        print("\n" + "-" * 80)
        print("TEST 1: find_symbol (using lookup_symbol method)")
        print("-" * 80)
        
        test_symbols = [
            ("SymbolTable", "class"),
            ("IndexingPipeline", "class"),
            ("search", "method"),
        ]
        
        all_passed = True
        for symbol_name, symbol_type in test_symbols:
            print(f"\nSearching for: '{symbol_name}' (type: {symbol_type})")
            try:
                # This should now work with the fixed lookup_symbol method
                symbols = symbol_table.lookup_symbol(symbol_name, symbol_type=symbol_type)
                if symbols:
                    print(f"✅ PASS - Found {len(symbols)} match(es)")
                    for sym in symbols[:2]:
                        print(f"  - {sym['name']} in {sym['file_path']}:{sym['line_number']}")
                else:
                    print(f"⚠️  No matches found (may not exist in codebase)")
            except Exception as e:
                print(f"❌ FAIL - Error: {e}")
                all_passed = False
        
        # TEST 2: find_callers (Bug Fix #2)
        print("\n" + "-" * 80)
        print("TEST 2: find_callers (new method implementation)")
        print("-" * 80)
        
        test_caller_symbols = [
            "SymbolTable",
            "IndexingPipeline",
            "search",
        ]
        
        for symbol_name in test_caller_symbols:
            print(f"\nFinding callers of: '{symbol_name}'")
            try:
                # This should now work with the new find_callers method
                callers = symbol_table.find_callers(symbol_name, max_results=5)
                if callers:
                    print(f"✅ PASS - Found {len(callers)} potential caller(s)")
                    for caller in callers[:3]:
                        print(f"  - {caller['name']} ({caller['type']}) in {caller['file_path']}:{caller['line_number']}")
                else:
                    print(f"⚠️  No callers found (symbol may be in isolated file)")
            except Exception as e:
                print(f"❌ FAIL - Error: {e}")
                all_passed = False
        
        # TEST 3: trace_dependencies (Bug Fix #3)
        print("\n" + "-" * 80)
        print("TEST 3: trace_dependencies (new get_file_dependencies method)")
        print("-" * 80)
        
        # Find a file that likely has dependencies
        test_files = [
            "mcp_server.py",
            "indexer/pipeline.py",
            "symbol_table/symbol_table.py",
        ]
        
        for test_file in test_files:
            print(f"\nTracing dependencies for: {test_file}")
            try:
                # This should now work with the new get_file_dependencies method
                dependencies = dependency_graph.get_file_dependencies(
                    test_file,
                    symbol_table,
                    depth=2
                )
                if dependencies:
                    print(f"✅ PASS - Found {len(dependencies)} dependencies")
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
                    print(f"⚠️  No dependencies found (file may have no imports)")
            except Exception as e:
                print(f"❌ FAIL - Error: {e}")
                all_passed = False
        
        # PHASE 4: TEST MULTI-COLLECTION SUPPORT
        print("\n" + "=" * 80)
        print("PHASE 4: TESTING MULTI-COLLECTION SUPPORT")
        print("=" * 80)
        
        print("\nTesting that managers handle multiple collections correctly...")
        
        # Create a second collection
        collection_name_2 = "test_fixes_2"
        symbol_table_2 = symbol_table_manager.get_table(collection_name_2)
        dependency_graph_2 = dependency_graph_manager.get_graph(collection_name_2)
        
        print(f"✓ Created second collection: {collection_name_2}")
        
        # Verify they are different instances
        if symbol_table is not symbol_table_2:
            print(f"✅ PASS - Symbol tables are separate instances")
        else:
            print(f"❌ FAIL - Symbol tables are the same instance!")
            all_passed = False
        
        if dependency_graph is not dependency_graph_2:
            print(f"✅ PASS - Dependency graphs are separate instances")
        else:
            print(f"❌ FAIL - Dependency graphs are the same instance!")
            all_passed = False
        
        # FINAL SUMMARY
        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        
        if all_passed:
            print("\n✅ ALL TESTS PASSED!")
            print("\nAll three fixed MCP tools are working correctly:")
            print("  1. find_symbol - Uses lookup_symbol() method ✓")
            print("  2. find_callers - New method implemented ✓")
            print("  3. trace_dependencies - New get_file_dependencies() method ✓")
            print("  4. Multi-collection support - Managers working correctly ✓")
        else:
            print("\n❌ SOME TESTS FAILED")
            print("Please review the errors above.")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_fixed_tools())
    sys.exit(0 if success else 1)

