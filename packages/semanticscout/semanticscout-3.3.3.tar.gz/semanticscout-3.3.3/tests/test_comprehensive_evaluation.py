"""
Comprehensive SemanticScout Evaluation Framework

Tests all three indexing pipelines across 20 diverse queries covering:
1. Semantic Search (natural language)
2. Hybrid Retrieval (semantic + symbols)
3. Code Context (dependencies & relationships)
4. Architectural Context (patterns & structure)
5. Best Practices (SOLID, testing, error handling)

Generates detailed comparison report with metrics and recommendations.
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

# Test configuration
MORFEUS_QT_PATH = "C:/git/moRFeus_Qt"
TEST_DATA_DIR = Path("C:/git/Indexer101/.semanticscout-comprehensive-eval")

# Comprehensive test queries organized by category
TEST_QUERIES = {
    "semantic_search": [
        {
            "id": "Q1.1",
            "query": "How does the application communicate with USB HID devices?",
            "expected_files": ["mrf.py", "TxRx.py"],
            "expected_concepts": ["USB", "HID", "device communication", "protocol"],
        },
        {
            "id": "Q1.2",
            "query": "What frequency ranges are supported by the generator?",
            "expected_files": ["mrf.py", "mrfqt.py"],
            "expected_concepts": ["frequency", "range", "validation", "limits"],
        },
        {
            "id": "Q1.3",
            "query": "How is the Qt GUI main window initialized and configured?",
            "expected_files": ["mrfui.py", "mrfuin.py", "mrfqt.py"],
            "expected_concepts": ["QMainWindow", "initialization", "UI setup", "widgets"],
        },
        {
            "id": "Q1.4",
            "query": "What error handling mechanisms are implemented for device communication failures?",
            "expected_files": ["mrf.py", "TxRx.py", "mrftcp.py"],
            "expected_concepts": ["exception", "error handling", "try-catch", "recovery"],
        },
        {
            "id": "Q1.5",
            "query": "How does the application visualize frequency spectrum data?",
            "expected_files": ["mrfplot.py"],
            "expected_concepts": ["plot", "visualization", "spectrum", "chart"],
        },
    ],
    "hybrid_retrieval": [
        {
            "id": "Q2.1",
            "query": "Find all classes that inherit from QWidget or QMainWindow",
            "expected_files": ["mrfui.py", "mrfuin.py", "mrfqt.py"],
            "expected_concepts": ["inheritance", "QWidget", "QMainWindow", "GUI classes"],
        },
        {
            "id": "Q2.2",
            "query": "Show me where the MoRFeus class is defined and how it's used",
            "expected_files": ["mrf.py", "__main__.py", "test_mrf.py"],
            "expected_concepts": ["class definition", "instantiation", "usage"],
        },
        {
            "id": "Q2.3",
            "query": "What methods are available on the frequency generator control interface?",
            "expected_files": ["mrf.py"],
            "expected_concepts": ["methods", "API", "interface", "public methods"],
        },
        {
            "id": "Q2.4",
            "query": "Find all functions that accept frequency parameters",
            "expected_files": ["mrf.py", "mrfqt.py"],
            "expected_concepts": ["function parameters", "frequency", "arguments"],
        },
        {
            "id": "Q2.5",
            "query": "Which modules import the USB communication library?",
            "expected_files": ["__main__.py", "mrfqt.py", "test_mrf.py"],
            "expected_concepts": ["imports", "dependencies", "modules"],
        },
    ],
    "code_context": [
        {
            "id": "Q3.1",
            "query": "What are the dependencies of the main application entry point?",
            "expected_files": ["__main__.py", "mrfqt.py"],
            "expected_concepts": ["dependencies", "imports", "entry point"],
        },
        {
            "id": "Q3.2",
            "query": "Show me the call chain from GUI button click to USB command transmission",
            "expected_files": ["mrfui.py", "mrfqt.py", "mrf.py", "TxRx.py"],
            "expected_concepts": ["event handler", "signal", "slot", "USB transmission"],
        },
        {
            "id": "Q3.3",
            "query": "Which files would be affected if I change the USB protocol implementation?",
            "expected_files": ["mrf.py", "TxRx.py", "mrftcp.py", "test_mrf.py"],
            "expected_concepts": ["impact analysis", "dependencies", "protocol"],
        },
        {
            "id": "Q3.4",
            "query": "What data flows between the GUI layer and the hardware control layer?",
            "expected_files": ["mrfui.py", "mrfqt.py", "mrf.py"],
            "expected_concepts": ["data flow", "layer communication", "interfaces"],
        },
    ],
    "architectural_context": [
        {
            "id": "Q4.1",
            "query": "What design patterns are used in this codebase?",
            "expected_files": ["mrfui.py", "mrfqt.py", "mrf.py"],
            "expected_concepts": ["design patterns", "MVC", "Observer", "architecture"],
        },
        {
            "id": "Q4.2",
            "query": "How is separation of concerns implemented between UI and business logic?",
            "expected_files": ["mrfui.py", "mrfqt.py", "mrf.py"],
            "expected_concepts": ["separation of concerns", "layers", "coupling"],
        },
        {
            "id": "Q4.3",
            "query": "What is the overall architecture of the application?",
            "expected_files": ["__main__.py", "mrfqt.py", "mrf.py", "mrfui.py"],
            "expected_concepts": ["architecture", "components", "structure"],
        },
    ],
    "best_practices": [
        {
            "id": "Q5.1",
            "query": "Does this code follow the Single Responsibility Principle?",
            "expected_files": ["mrf.py", "mrfqt.py", "mrfui.py"],
            "expected_concepts": ["SRP", "responsibility", "cohesion"],
        },
        {
            "id": "Q5.2",
            "query": "What test coverage exists for the USB communication module?",
            "expected_files": ["test_mrf.py"],
            "expected_concepts": ["tests", "coverage", "test cases"],
        },
        {
            "id": "Q5.3",
            "query": "How is dependency injection used in this codebase?",
            "expected_files": ["mrfqt.py", "mrf.py"],
            "expected_concepts": ["dependency injection", "constructor", "interfaces"],
        },
    ],
}

# Test configurations
TEST_CONFIGS = {
    "test1_ollama": {
        "name": "Tree-sitter + Ollama",
        "embedding": {"provider": "ollama", "model": "nomic-embed-text"},
        "lsp_integration": {"enabled": False},
        "features": {
            "enable_ast_processing": True,
            "enable_symbol_table": True,
            "enable_dependency_graph": True,
            "enable_language_detection": True,
            "enable_dependency_analysis": True,
        },
        "language_detection": {"enabled": True, "confidence_threshold": 0.1},
        "dependency_analysis": {
            "enabled": True,
            "strategies": ["rust", "python", "c_sharp", "javascript"],
        },
    },
    "test2_sentence_transformers": {
        "name": "Tree-sitter + Sentence-Transformers",
        "embedding": {"provider": "sentence-transformers", "model": "all-MiniLM-L6-v2"},
        "lsp_integration": {"enabled": False},
        "features": {
            "enable_ast_processing": True,
            "enable_symbol_table": True,
            "enable_dependency_graph": True,
            "enable_language_detection": True,
            "enable_dependency_analysis": True,
        },
        "language_detection": {"enabled": True, "confidence_threshold": 0.1},
        "dependency_analysis": {
            "enabled": True,
            "strategies": ["rust", "python", "c_sharp", "javascript"],
        },
    },
    "test3_lsp": {
        "name": "LSP (jedi) + Sentence-Transformers",
        "embedding": {"provider": "sentence-transformers", "model": "all-MiniLM-L6-v2"},
        "lsp_integration": {"enabled": True},
        "features": {
            "enable_ast_processing": True,
            "enable_symbol_table": True,
            "enable_dependency_graph": True,
            "enable_language_detection": True,
            "enable_dependency_analysis": True,
        },
        "language_detection": {"enabled": True, "confidence_threshold": 0.1},
        "dependency_analysis": {
            "enabled": True,
            "strategies": ["rust", "python", "c_sharp", "javascript"],
        },
    },
}


@dataclass
class QueryResult:
    """Result of a single query execution"""
    query_id: str
    query_text: str
    category: str
    config_name: str
    response_time: float
    result_size: int
    result_text: str
    files_found: List[str]
    relevance_score: float = 0.0  # To be manually assessed
    completeness_score: float = 0.0  # To be manually assessed
    context_quality_score: float = 0.0  # To be manually assessed


@dataclass
class ConfigResults:
    """Results for all queries in a single configuration"""
    config_name: str
    index_time: float
    symbols_count: int
    dependencies_count: int
    query_results: List[QueryResult]


def extract_files_from_result(result_text: str) -> List[str]:
    """Extract file names from search result"""
    files = []
    lines = result_text.split('\n')
    for line in lines:
        if 'File:' in line or 'file_path' in line.lower():
            # Extract filename from various formats
            parts = line.split('/')
            if parts:
                filename = parts[-1].strip()
                if filename and filename not in files:
                    files.append(filename)
    return files


def run_queries_for_config(config_key: str, config: Dict, data_dir: Path) -> ConfigResults:
    """Run all test queries for a single configuration"""
    print("="*80)
    print(f"TESTING: {config['name']}")
    print("="*80)
    print()
    
    # Set config and data directory
    os.environ["SEMANTICSCOUT_CONFIG_JSON"] = json.dumps(config)
    os.environ["SEMANTICSCOUT_DATA_DIR"] = str(data_dir)
    
    # Reload modules
    for module in list(sys.modules.keys()):
        if module.startswith('semanticscout'):
            del sys.modules[module]
    
    # Import
    from semanticscout.mcp_server import (
        index_codebase,
        search_code,
        initialize_components,
        symbol_table_manager,
        dependency_graph_manager,
    )
    
    # Initialize
    print("Initializing components...")
    initialize_components()
    print("[OK] Initialized\n")
    
    # Index
    print(f"Indexing moRFeus_Qt...")
    start_time = time.time()
    index_result = index_codebase(path=MORFEUS_QT_PATH, incremental=False)
    index_time = time.time() - start_time
    
    # Get collection name (auto-generated with provider suffix)
    base_name = "morfeus_qt"
    provider_model = config["embedding"]["model"].replace("-", "_").replace(":", "_")
    collection_name = f"{base_name}_{provider_model}"
    print(f"  Collection: {collection_name}")
    
    # Get stats by parsing the index_result string
    symbols_count = 0
    dependencies_count = 0

    # Extract from result string
    import re
    symbols_match = re.search(r'Symbols extracted:\s*(\d+)', index_result)
    deps_match = re.search(r'Dependencies tracked:\s*(\d+)', index_result)

    if symbols_match:
        symbols_count = int(symbols_match.group(1))
    if deps_match:
        dependencies_count = int(deps_match.group(1))
    
    print(f"[OK] Indexed in {index_time:.2f}s")
    print(f"  Symbols: {symbols_count}")
    print(f"  Dependencies: {dependencies_count}\n")
    
    # Run all queries
    all_query_results = []
    total_queries = sum(len(queries) for queries in TEST_QUERIES.values())
    query_num = 0
    
    for category, queries in TEST_QUERIES.items():
        print(f"\n{'='*80}")
        print(f"Category: {category.upper().replace('_', ' ')}")
        print(f"{'='*80}\n")
        
        for query_info in queries:
            query_num += 1
            query_id = query_info["id"]
            query_text = query_info["query"]
            
            print(f"[{query_num}/{total_queries}] {query_id}: {query_text}")
            
            start_time = time.time()
            try:
                result_text = search_code(
                    query=query_text,
                    collection_name=collection_name,
                    top_k=5,
                    expansion_level="medium"
                )
                response_time = time.time() - start_time
                result_size = len(result_text)
                files_found = extract_files_from_result(result_text)
                
                query_result = QueryResult(
                    query_id=query_id,
                    query_text=query_text,
                    category=category,
                    config_name=config['name'],
                    response_time=response_time,
                    result_size=result_size,
                    result_text=result_text,
                    files_found=files_found,
                )
                
                all_query_results.append(query_result)
                print(f"  [OK] {response_time:.3f}s, {result_size} chars, {len(files_found)} files")

            except Exception as e:
                print(f"  [ERROR] {e}")
                query_result = QueryResult(
                    query_id=query_id,
                    query_text=query_text,
                    category=category,
                    config_name=config['name'],
                    response_time=0.0,
                    result_size=0,
                    result_text=f"ERROR: {str(e)}",
                    files_found=[],
                )
                all_query_results.append(query_result)
    
    return ConfigResults(
        config_name=config['name'],
        index_time=index_time,
        symbols_count=symbols_count,
        dependencies_count=dependencies_count,
        query_results=all_query_results,
    )


if __name__ == "__main__":
    print("="*80)
    print("COMPREHENSIVE SEMANTICSCOUT EVALUATION")
    print("="*80)
    print()
    print(f"Test repository: {MORFEUS_QT_PATH}")
    print(f"Total queries: {sum(len(q) for q in TEST_QUERIES.values())}")
    print(f"Categories: {len(TEST_QUERIES)}")
    print(f"Configurations: {len(TEST_CONFIGS)}")
    print()
    
    # Clean up previous test data
    if TEST_DATA_DIR.exists():
        print(f"Cleaning up: {TEST_DATA_DIR}")
        shutil.rmtree(TEST_DATA_DIR)
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run tests for all configurations
    all_results = {}
    
    for config_key, config in TEST_CONFIGS.items():
        config_data_dir = TEST_DATA_DIR / config_key
        config_data_dir.mkdir(parents=True, exist_ok=True)
        
        results = run_queries_for_config(config_key, config, config_data_dir)
        all_results[config_key] = results
    
    # Save results to JSON for later analysis
    results_file = TEST_DATA_DIR / "evaluation_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            key: asdict(results) for key, results in all_results.items()
        }, f, indent=2)
    
    print(f"\n{'='*80}")
    print("EVALUATION COMPLETE")
    print(f"{'='*80}\n")
    print(f"Results saved to: {results_file}")
    print("\nNext step: Run analysis script to generate comparison report")

