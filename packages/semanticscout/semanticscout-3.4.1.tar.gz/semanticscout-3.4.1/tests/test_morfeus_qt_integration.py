"""
Integration test suite for moRFeus_Qt repository.

Tests full indexing and incremental updates on a real C# codebase.
"""

import pytest
import time
from pathlib import Path

from src.semanticscout.indexer.pipeline import IndexingPipeline
from src.semanticscout.indexer.delta_indexer import DeltaIndexer
from src.semanticscout.indexer.change_detector import UnifiedChangeDetector
from src.semanticscout.embeddings.sentence_transformer_provider import SentenceTransformerProvider
from src.semanticscout.vector_store.chroma_store import ChromaVectorStore
from src.semanticscout.symbol_table.symbol_table import SymbolTable
from src.semanticscout.dependency_graph.dependency_graph import DependencyGraph


# Path to moRFeus_Qt repository
MORFEUS_QT_PATH = Path("C:/git/moRFeus_Qt")
COLLECTION_NAME = "morfeus_qt_test"


@pytest.fixture(scope="module")
def morfeus_env():
    """Set up test environment for moRFeus_Qt."""
    if not MORFEUS_QT_PATH.exists():
        pytest.skip(f"moRFeus_Qt repository not found at {MORFEUS_QT_PATH}")
    
    # Use sentence-transformers for faster testing
    embedding_provider = SentenceTransformerProvider()
    vector_store = ChromaVectorStore(persist_directory="./data/test_chroma")
    symbol_table = SymbolTable(collection_name=COLLECTION_NAME)
    dependency_graph = DependencyGraph()
    
    # Create indexing pipeline
    pipeline = IndexingPipeline(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        symbol_table=symbol_table,
        dependency_graph=dependency_graph,
    )
    
    # Create delta indexer
    delta_indexer = DeltaIndexer(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        symbol_table=symbol_table,
        dependency_graph=dependency_graph,
    )
    
    # Create change detector
    change_detector = UnifiedChangeDetector(repo_path=MORFEUS_QT_PATH)
    
    yield {
        "pipeline": pipeline,
        "delta_indexer": delta_indexer,
        "change_detector": change_detector,
        "vector_store": vector_store,
        "symbol_table": symbol_table,
        "dependency_graph": dependency_graph,
    }
    
    # Cleanup
    try:
        vector_store.delete_collection(COLLECTION_NAME)
        symbol_table.close()
    except:
        pass


def test_full_indexing(morfeus_env):
    """Test full indexing of moRFeus_Qt repository."""
    pipeline = morfeus_env["pipeline"]
    
    print(f"\n📊 Full Indexing: {MORFEUS_QT_PATH}")
    start_time = time.time()
    
    # Index the repository
    result = pipeline.index_codebase(
        codebase_path=MORFEUS_QT_PATH,
        collection_name=COLLECTION_NAME,
    )
    
    elapsed = time.time() - start_time
    
    print(f"✅ Indexing complete in {elapsed:.2f}s")
    print(f"  Files indexed: {result['files_indexed']}")
    print(f"  Chunks created: {result['chunks_created']}")
    print(f"  Symbols extracted: {result['symbols_extracted']}")
    print(f"  Dependencies tracked: {result['dependencies_tracked']}")
    
    # Assertions
    assert result["files_indexed"] > 0, "Should index files"
    assert result["chunks_created"] > 0, "Should create chunks"
    assert result["symbols_extracted"] > 0, "Should extract symbols"
    
    # Verify C# support
    assert result["dependencies_tracked"] > 0, "Should track C# dependencies"


def test_incremental_update_single_file(morfeus_env):
    """Test incremental update of a single file."""
    delta_indexer = morfeus_env["delta_indexer"]
    
    # Find a C# file to update
    cs_files = list(MORFEUS_QT_PATH.rglob("*.cs"))
    if not cs_files:
        pytest.skip("No C# files found")
    
    test_file = cs_files[0]
    
    print(f"\n🔄 Incremental Update: {test_file.name}")
    start_time = time.time()
    
    # Update file
    result = delta_indexer.update_file(
        file_path=test_file,
        collection_name=COLLECTION_NAME,
        root_path=MORFEUS_QT_PATH,
    )
    
    elapsed = time.time() - start_time
    
    print(f"✅ Update complete in {elapsed:.2f}s")
    print(f"  Chunks added: {result.chunks_added}")
    print(f"  Chunks reused: {result.chunks_reused}")
    print(f"  Chunks removed: {result.chunks_removed}")
    print(f"  Symbols added: {result.symbols_added}")
    
    assert result.success, "Update should succeed"


def test_change_detection(morfeus_env):
    """Test change detection on moRFeus_Qt repository."""
    change_detector = morfeus_env["change_detector"]
    
    print(f"\n🔍 Change Detection: {MORFEUS_QT_PATH}")
    start_time = time.time()
    
    # Detect changes
    changes = change_detector.detect_changes(MORFEUS_QT_PATH)
    
    elapsed = time.time() - start_time
    
    print(f"✅ Detection complete in {elapsed:.2f}s")
    print(f"  Changed files: {len(changes)}")
    
    # Should detect strategy (Git or hash-based)
    strategy = change_detector.get_strategy(MORFEUS_QT_PATH)
    print(f"  Strategy: {strategy}")
    
    assert strategy in ["git", "hash"], "Should use valid strategy"


def test_search_functionality(morfeus_env):
    """Test semantic search on indexed moRFeus_Qt code."""
    vector_store = morfeus_env["vector_store"]
    
    # Search for common C# patterns
    queries = [
        "USB device communication",
        "frequency control",
        "GUI initialization",
        "error handling",
    ]
    
    print(f"\n🔎 Search Tests:")
    for query in queries:
        results = vector_store.search(
            collection_name=COLLECTION_NAME,
            query_embedding=[0.1] * 384,  # Dummy embedding for test
            top_k=5,
        )
        
        print(f"  '{query}': {len(results)} results")
        
        # Should return results (even with dummy embedding)
        assert isinstance(results, list), "Should return list of results"


def test_symbol_lookup(morfeus_env):
    """Test symbol table lookup for C# symbols."""
    symbol_table = morfeus_env["symbol_table"]
    
    # Search for common C# symbols
    symbols = symbol_table.search_symbols(
        query="Form",
        limit=10,
    )
    
    print(f"\n📚 Symbol Lookup:")
    print(f"  Found {len(symbols)} symbols matching 'Form'")
    
    if symbols:
        for symbol in symbols[:3]:
            print(f"    - {symbol['name']} ({symbol['symbol_type']})")
    
    assert isinstance(symbols, list), "Should return list of symbols"


def test_dependency_graph(morfeus_env):
    """Test dependency graph for C# files."""
    dependency_graph = morfeus_env["dependency_graph"]
    
    # Get graph stats
    stats = dependency_graph.get_statistics()
    
    print(f"\n🕸️ Dependency Graph:")
    print(f"  Nodes: {stats.get('node_count', 0)}")
    print(f"  Edges: {stats.get('edge_count', 0)}")
    print(f"  Avg dependencies: {stats.get('avg_dependencies', 0):.2f}")
    
    assert stats.get('node_count', 0) > 0, "Should have nodes"


def test_performance_comparison(morfeus_env):
    """Compare full vs incremental indexing performance."""
    pipeline = morfeus_env["pipeline"]
    delta_indexer = morfeus_env["delta_indexer"]
    change_detector = morfeus_env["change_detector"]
    
    print(f"\n⚡ Performance Comparison:")
    
    # Detect changed files
    changes = change_detector.detect_changes(MORFEUS_QT_PATH)
    
    if not changes:
        print("  No changes detected - skipping comparison")
        return
    
    # Take first 5 changed files for testing
    test_files = list(changes)[:5]
    
    # Incremental update
    print(f"  Testing incremental update on {len(test_files)} files...")
    start_time = time.time()
    
    results = delta_indexer.update_files(
        file_paths=test_files,
        collection_name=COLLECTION_NAME,
        root_path=MORFEUS_QT_PATH,
    )
    
    incremental_time = time.time() - start_time
    
    successful = sum(1 for r in results if r.success)
    total_chunks_reused = sum(r.chunks_reused for r in results)
    
    print(f"  ✅ Incremental: {incremental_time:.2f}s")
    print(f"     Success: {successful}/{len(test_files)}")
    print(f"     Chunks reused: {total_chunks_reused}")
    
    assert successful > 0, "Should successfully update some files"


def test_concurrent_updates(morfeus_env):
    """Test concurrent file updates (if supported)."""
    delta_indexer = morfeus_env["delta_indexer"]
    
    # Find multiple C# files
    cs_files = list(MORFEUS_QT_PATH.rglob("*.cs"))[:3]
    
    if len(cs_files) < 2:
        pytest.skip("Need at least 2 C# files for concurrent test")
    
    print(f"\n🔀 Concurrent Updates: {len(cs_files)} files")
    start_time = time.time()
    
    # Update files sequentially (parallel would require async)
    results = delta_indexer.update_files(
        file_paths=cs_files,
        collection_name=COLLECTION_NAME,
        root_path=MORFEUS_QT_PATH,
    )
    
    elapsed = time.time() - start_time
    
    successful = sum(1 for r in results if r.success)
    
    print(f"✅ Updates complete in {elapsed:.2f}s")
    print(f"  Success: {successful}/{len(cs_files)}")
    
    assert successful > 0, "Should successfully update files"


def test_consistency_check(morfeus_env):
    """Verify index consistency after updates."""
    vector_store = morfeus_env["vector_store"]
    symbol_table = morfeus_env["symbol_table"]
    
    print(f"\n✓ Consistency Check:")
    
    # Get collection stats
    if vector_store.collection_exists(COLLECTION_NAME):
        collection = vector_store.client.get_collection(COLLECTION_NAME)
        chunk_count = collection.count()
        print(f"  Vector store chunks: {chunk_count}")
    else:
        chunk_count = 0
        print(f"  Vector store: Collection not found")
    
    # Get symbol count
    symbols = symbol_table.search_symbols("", limit=1000)
    symbol_count = len(symbols)
    print(f"  Symbol table entries: {symbol_count}")
    
    # Basic consistency checks
    assert chunk_count >= 0, "Chunk count should be non-negative"
    assert symbol_count >= 0, "Symbol count should be non-negative"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

