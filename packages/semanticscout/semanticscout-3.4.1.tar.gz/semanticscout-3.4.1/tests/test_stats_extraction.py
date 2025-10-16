"""Quick test to verify stats extraction from index_result"""
import json
import os
import sys
import re

# Set config
os.environ["SEMANTICSCOUT_CONFIG_JSON"] = json.dumps({
    "name": "Test",
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
})
os.environ["SEMANTICSCOUT_DATA_DIR"] = "C:/git/Indexer101/.test-stats"

# Import
sys.path.insert(0, "C:/git/Indexer101/src")
from semanticscout.mcp_server import index_codebase, initialize_components

# Initialize
print("Initializing...")
initialize_components()

# Index
print("Indexing...")
result = index_codebase(path="C:/git/moRFeus_Qt", incremental=False)

# Extract stats
print("\n" + "="*80)
print("RESULT STRING:")
print("="*80)
# Write to file to avoid Unicode issues
with open("C:/git/Indexer101/.test-stats/result.txt", "w", encoding="utf-8") as f:
    f.write(result)
print("(Result written to .test-stats/result.txt)")
print("="*80)

# Parse stats
symbols_match = re.search(r'Symbols extracted:\s*(\d+)', result)
deps_match = re.search(r'Dependencies tracked:\s*(\d+)', result)

print("\nEXTRACTED STATS:")
print(f"Symbols: {symbols_match.group(1) if symbols_match else 'NOT FOUND'}")
print(f"Dependencies: {deps_match.group(1) if deps_match else 'NOT FOUND'}")

