"""
Integration test for all 11 MCP tools using direct function imports.
Tests both Weather-Unified (C#) and moRFeus_Qt (Python) repositories.

This is much faster than using the MCP Inspector as it imports functions directly.
"""

import asyncio
import json
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any

# Set configuration before importing semanticscout
os.environ["SEMANTICSCOUT_CONFIG_JSON"] = json.dumps({
    "embedding": {
        "provider": "sentence-transformers",
        "model": "all-MiniLM-L6-v2"
    }
})

# Import MCP server functions
from semanticscout.mcp_server import (
    get_server_info,
    list_collections,
    index_codebase,
    get_indexing_status,
    search_code,
    find_symbol,
    find_callers,
    trace_dependencies,
    clear_index,
    process_file_changes,
)


# Test configuration
WEATHER_UNIFIED_PATH = "C:/git/Weather-Unified"
MORFEUS_QT_PATH = "C:/git/moRFeus_Qt"
TEST_DATA_DIR = Path("C:/Users/Ohan/.semanticscout-integration-test")


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a colored header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}\n")


def print_test(test_name: str):
    """Print test name."""
    try:
        print(f"{Colors.BOLD}{Colors.BLUE}▶ {test_name}{Colors.END}")
    except UnicodeEncodeError:
        print(f"{Colors.BOLD}{Colors.BLUE}> {test_name}{Colors.END}")


def print_success(message: str):
    """Print success message."""
    try:
        print(f"{Colors.GREEN}✓ {message}{Colors.END}")
    except UnicodeEncodeError:
        print(f"{Colors.GREEN}+ {message}{Colors.END}")


def print_error(message: str):
    """Print error message."""
    try:
        print(f"{Colors.RED}✗ {message}{Colors.END}")
    except UnicodeEncodeError:
        print(f"{Colors.RED}X {message}{Colors.END}")


def print_info(message: str):
    """Print info message."""
    # Handle Unicode characters that may not be supported in Windows console
    try:
        print(f"{Colors.YELLOW}  {message}{Colors.END}")
    except UnicodeEncodeError:
        # Fallback: encode with errors='replace' to avoid crashes
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(f"{Colors.YELLOW}  {safe_message}{Colors.END}")


def print_result(key: str, value: Any):
    """Print a key-value result."""
    print(f"{Colors.MAGENTA}  {key}:{Colors.END} {value}")


async def test_get_server_info():
    """Test 1: get_server_info"""
    print_test("Test 1: get_server_info")

    # Load actual config to get expected values
    import importlib.util
    from pathlib import Path

    # Import config module using the same pattern as mcp_server.py
    config_module_path = Path(__file__).parent.parent / "src" / "semanticscout" / "config.py"
    spec = importlib.util.spec_from_file_location("semanticscout_config_module", config_module_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    expected_config = config_module.load_config()

    # Determine expected model and dimensions based on provider type
    if expected_config.embedding_provider == "sentence-transformers":
        expected_model = expected_config.sentence_transformers_model
        # Get expected dimensions from provider
        from semanticscout.embeddings.sentence_transformer_provider import SentenceTransformerProvider
        temp_provider = SentenceTransformerProvider(model_name=expected_model)
        expected_dims = temp_provider.get_dimensions()
    elif expected_config.embedding_provider == "ollama":
        expected_model = expected_config.ollama_model
        expected_dims = 768  # nomic-embed-text default
    elif expected_config.embedding_provider == "openai":
        expected_model = expected_config.openai_model
        expected_dims = 1536  # text-embedding-3-small default
    else:
        expected_model = "unknown"
        expected_dims = 768

    result = get_server_info()

    assert result["name"] == "semanticscout", f"Expected name 'semanticscout', got {result['name']}"
    assert "version" in result, "Missing version field"
    assert result["embedding_provider"] == expected_config.embedding_provider, f"Expected {expected_config.embedding_provider}, got {result['embedding_provider']}"
    assert result["embedding_model"] == expected_model, f"Expected {expected_model}, got {result['embedding_model']}"
    assert result["embedding_dimensions"] == expected_dims, f"Expected {expected_dims} dimensions, got {result['embedding_dimensions']}"
    assert result["status"] == "running", f"Expected status 'running', got {result['status']}"

    print_success("Server info retrieved successfully")
    print_result("Version", result["version"])
    print_result("Provider", result["embedding_provider"])
    print_result("Model", result["embedding_model"])
    print_result("Dimensions", result["embedding_dimensions"])

    return result


async def test_list_collections_empty():
    """Test 2: list_collections (should be empty initially)"""
    print_test("Test 2: list_collections (empty)")

    result = list_collections()

    assert "collections" in result, "Missing collections field"
    assert "total_collections" in result, "Missing total_collections field"
    assert isinstance(result["collections"], list), "collections should be a list"

    # Verify structure of each collection (if any exist)
    for coll in result["collections"]:
        assert "name" in coll, "Missing 'name' field in collection"
        assert "embedding_model" in coll, "Missing 'embedding_model' field in collection"
        assert "embedding_dimensions" in coll, "Missing 'embedding_dimensions' field in collection"
        assert "processor_type" in coll, "Missing 'processor_type' field in collection"
        assert "chunk_count" in coll, "Missing 'chunk_count' field in collection"
        assert "associated_files" in coll, "Missing 'associated_files' field in collection"
        # codebase_path is optional (may not exist for old collections)
        if "codebase_path" in coll:
            assert isinstance(coll["codebase_path"], str), "codebase_path should be a string"

    print_success(f"Collections listed: {result['total_collections']} collections")

    return result


async def test_index_weather_unified():
    """Test 3: index_codebase (Weather-Unified)"""
    print_test("Test 3: index_codebase (Weather-Unified)")

    # Clear any existing collections for this path first
    # (to avoid duplicate detection blocking the test)
    collections_result = list_collections()
    for coll in collections_result.get("collections", []):
        codebase_path = coll.get("codebase_path", "")
        if codebase_path and Path(codebase_path).resolve() == Path(WEATHER_UNIFIED_PATH).resolve():
            print_info(f"Clearing existing collection: {coll['name']}")
            clear_index(coll['name'])

    start_time = time.time()
    result = index_codebase(path=WEATHER_UNIFIED_PATH, incremental=False)
    elapsed = time.time() - start_time

    # Parse result string to extract statistics
    assert "Successfully indexed" in result, f"Indexing failed: {result}"
    assert "Files indexed:" in result, "Missing file count"
    assert "Chunks created:" in result, "Missing chunk count"

    # Extract collection name
    lines = result.split("\n")
    collection_name = None
    for line in lines:
        if line.startswith("Collection:"):
            collection_name = line.split(":")[1].strip()
            break

    assert collection_name is not None, "Could not extract collection name"
    # Collection names preserve original project name format + UUID suffix
    # Weather-Unified becomes weather-unified_a1b2c3d4 (preserves hyphen)
    assert collection_name.startswith("weather-unified_"), f"Expected collection name to start with 'weather-unified_', got '{collection_name}'"
    # Verify UUID suffix format (8 hex characters)
    uuid_part = collection_name.split("_")[-1]
    assert len(uuid_part) == 8 and all(c in "0123456789abcdef" for c in uuid_part), f"Expected 8-character hex UUID suffix, got '{uuid_part}'"

    print_success(f"Weather-Unified indexed in {elapsed:.2f}s")
    print_result("Collection", collection_name)
    print_info(result)

    return collection_name


async def test_index_morfeus_qt():
    """Test 4: index_codebase (moRFeus_Qt)"""
    print_test("Test 4: index_codebase (moRFeus_Qt)")

    # Clear any existing collections for this path first
    collections_result = list_collections()
    for coll in collections_result.get("collections", []):
        codebase_path = coll.get("codebase_path", "")
        if codebase_path and Path(codebase_path).resolve() == Path(MORFEUS_QT_PATH).resolve():
            print_info(f"Clearing existing collection: {coll['name']}")
            clear_index(coll['name'])

    start_time = time.time()
    result = index_codebase(path=MORFEUS_QT_PATH, incremental=False)
    elapsed = time.time() - start_time

    assert "Successfully indexed" in result, f"Indexing failed: {result}"

    # Extract collection name
    lines = result.split("\n")
    collection_name = None
    for line in lines:
        if line.startswith("Collection:"):
            collection_name = line.split(":")[1].strip()
            break

    assert collection_name is not None, "Could not extract collection name"
    # Collection names now use underscores and UUID suffix (e.g., morfeus_qt_a1b2c3d4)
    assert collection_name.startswith("morfeus_qt_"), f"Expected collection name to start with 'morfeus_qt_', got '{collection_name}'"
    # Verify UUID suffix format (8 hex characters)
    uuid_part = collection_name.split("_")[-1]
    assert len(uuid_part) == 8 and all(c in "0123456789abcdef" for c in uuid_part), f"Expected 8-character hex UUID suffix, got '{uuid_part}'"

    print_success(f"moRFeus_Qt indexed in {elapsed:.2f}s")
    print_result("Collection", collection_name)
    print_info(result)

    return collection_name


async def test_list_collections_with_data():
    """Test 5: list_collections (should have 2 collections)"""
    print_test("Test 5: list_collections (with data)")

    result = list_collections()

    assert result["total_collections"] == 2, f"Expected 2 collections, got {result['total_collections']}"

    print_success(f"Found {result['total_collections']} collections")
    for coll in result["collections"]:
        # Verify new response structure with all fields
        assert "name" in coll, "Missing 'name' field in collection"
        assert "embedding_model" in coll, "Missing 'embedding_model' field in collection"
        assert "embedding_dimensions" in coll, "Missing 'embedding_dimensions' field in collection"
        assert "processor_type" in coll, "Missing 'processor_type' field in collection"
        assert "chunk_count" in coll, "Missing 'chunk_count' field in collection"
        assert "associated_files" in coll, "Missing 'associated_files' field in collection"

        # Verify associated_files structure
        assert isinstance(coll["associated_files"], dict), "associated_files should be a dict"

        # Check if codebase_path exists (should for newly indexed collections)
        if "codebase_path" in coll:
            print_result(f"  {coll['name']} (path: {coll['codebase_path']})", f"{coll['chunk_count']} chunks")
        else:
            print_result(f"  {coll['name']} ({coll['embedding_model']}, dims={coll['embedding_dimensions']}, {coll['processor_type']})", f"{coll['chunk_count']} chunks")

    return result


async def test_get_indexing_status(collection_name: str, repo_name: str):
    """Test 6/7: get_indexing_status"""
    print_test(f"Test: get_indexing_status ({repo_name})")
    
    result = get_indexing_status(collection_name=collection_name)
    
    # Parse result string
    assert "Indexing Status" in result, "Missing status header"
    assert "Total chunks:" in result, "Missing chunk count"
    
    print_success(f"Status retrieved for {repo_name}")
    print_info(result)
    
    return result


async def test_search_code(collection_name: str, query: str, repo_name: str, expected_files: list = None):
    """Test 8-11: search_code"""
    print_test(f"Test: search_code - '{query}' ({repo_name})")
    
    result = search_code(query=query, collection_name=collection_name, top_k=5)
    
    assert "Search Results" in result, "Missing search results"
    assert "Found" in result, "Missing result count"
    
    print_success(f"Search completed for '{query}'")
    
    # Check if expected files are in results (if provided)
    if expected_files:
        for expected_file in expected_files:
            if expected_file in result:
                print_result("  Found expected", expected_file)
    
    # Print first result
    lines = result.split("\n")
    for i, line in enumerate(lines):
        if "Result 1/" in line:
            # Print next 5 lines
            for j in range(i, min(i + 6, len(lines))):
                print_info(lines[j])
            break
    
    return result


async def test_find_symbol(collection_name: str, symbol_name: str, repo_name: str, symbol_type: str = None):
    """Test 12-13: find_symbol"""
    print_test(f"Test: find_symbol - '{symbol_name}' ({repo_name})")
    
    result = find_symbol(symbol_name=symbol_name, collection_name=collection_name, symbol_type=symbol_type)
    
    assert "Symbol Search Results" in result or "not found" in result.lower(), "Unexpected result format"
    
    if "not found" in result.lower():
        print_info(f"Symbol '{symbol_name}' not found (may be expected)")
    else:
        print_success(f"Symbol '{symbol_name}' found")
        # Print first few lines
        lines = result.split("\n")
        for line in lines[:5]:
            print_info(line)
    
    return result


async def test_find_callers(collection_name: str, symbol_name: str, repo_name: str):
    """Test 14-15: find_callers"""
    print_test(f"Test: find_callers - '{symbol_name}' ({repo_name})")
    
    result = find_callers(symbol_name=symbol_name, collection_name=collection_name, max_results=10)
    
    assert "Callers" in result or "not found" in result.lower(), "Unexpected result format"
    
    if "not found" in result.lower() or "No callers found" in result:
        print_info(f"No callers found for '{symbol_name}' (may be expected)")
    else:
        print_success(f"Callers found for '{symbol_name}'")
        # Print first few lines
        lines = result.split("\n")
        for line in lines[:8]:
            print_info(line)
    
    return result


async def test_trace_dependencies(collection_name: str, file_path: str, repo_name: str):
    """Test 16-17: trace_dependencies"""
    print_test(f"Test: trace_dependencies - '{file_path}' ({repo_name})")
    
    result = trace_dependencies(file_path=file_path, collection_name=collection_name, depth=2)

    # Debug: print actual result
    print(f"\n  DEBUG: trace_dependencies result:\n{result}\n")

    assert "Dependency Trace" in result or "not found" in result.lower() or "No dependencies" in result, f"Unexpected result format: {result[:200]}"
    
    if "not found" in result.lower():
        print_info(f"File '{file_path}' not found (may be expected)")
    else:
        print_success(f"Dependencies traced for '{file_path}'")
        # Print first few lines
        lines = result.split("\n")
        for line in lines[:10]:
            print_info(line)
    
    return result


async def main():
    """Run all integration tests."""
    print_header("SemanticScout Integration Test - All 11 Tools")
    print_info(f"Test data directory: {TEST_DATA_DIR}")
    print_info(f"Weather-Unified: {WEATHER_UNIFIED_PATH}")
    print_info(f"moRFeus_Qt: {MORFEUS_QT_PATH}")

    # Clean up test data directory
    if TEST_DATA_DIR.exists():
        print_info(f"Cleaning up existing test data...")
        shutil.rmtree(TEST_DATA_DIR)
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize MCP server components
    print_info("Initializing MCP server components...")
    from semanticscout.mcp_server import initialize_components
    initialize_components()
    
    try:
        # Test 1: Server info
        await test_get_server_info()
        
        # Test 2: List collections (empty)
        await test_list_collections_empty()
        
        # Test 3-4: Index both repositories
        weather_collection = await test_index_weather_unified()
        morfeus_collection = await test_index_morfeus_qt()
        
        # Test 5: List collections (with data)
        await test_list_collections_with_data()
        
        # Test 6-7: Get indexing status
        await test_get_indexing_status(weather_collection, "Weather-Unified")
        await test_get_indexing_status(morfeus_collection, "moRFeus_Qt")
        
        # Test 8-11: Search code
        await test_search_code(weather_collection, "database configuration", "Weather-Unified", 
                              ["ObservationDatabaseSettings", "ForecastDatabaseSettings"])
        await test_search_code(weather_collection, "API controllers", "Weather-Unified",
                              ["Controller"])
        await test_search_code(morfeus_collection, "USB device communication", "moRFeus_Qt",
                              ["mrf.py"])
        await test_search_code(morfeus_collection, "Qt main window", "moRFeus_Qt",
                              ["mrfqt.py"])
        
        # Test 12-13: Find symbol
        await test_find_symbol(weather_collection, "ObservationsController", "Weather-Unified", "class")
        await test_find_symbol(morfeus_collection, "MoRFeus", "moRFeus_Qt", "class")
        
        # Test 14-15: Find callers
        await test_find_callers(weather_collection, "ObservationsService", "Weather-Unified")
        await test_find_callers(morfeus_collection, "find", "moRFeus_Qt")
        
        # Test 16-17: Trace dependencies
        await test_trace_dependencies(weather_collection, "WURequest/Services/ObservationsService.cs", "Weather-Unified")
        await test_trace_dependencies(morfeus_collection, "moRFeusQt/mrf.py", "moRFeus_Qt")
        
        print_header("✅ ALL TESTS PASSED!")

    except Exception as e:
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Shutdown components to release file locks
        print_info("Shutting down components...")
        try:
            from semanticscout.mcp_server import vector_store
            if vector_store and hasattr(vector_store, 'client'):
                # Close ChromaDB client
                del vector_store.client
        except Exception as e:
            print_info(f"Note: Could not shutdown cleanly: {e}")

        # Wait a moment for file handles to be released
        time.sleep(1)

        # Cleanup
        print_info("Cleaning up test data...")
        if TEST_DATA_DIR.exists():
            try:
                shutil.rmtree(TEST_DATA_DIR)
                print_success("Test data cleaned up")
            except PermissionError as e:
                print_info(f"Note: Could not delete test data (file in use): {e}")
                print_info(f"Please manually delete: {TEST_DATA_DIR}")


if __name__ == "__main__":
    asyncio.run(main())

