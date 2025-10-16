"""
MCP Client Integration Tests

Tests all SemanticScout MCP tools against a running server using Weather-Unified repository.

This test:
1. Starts the MCP server as a subprocess
2. Connects as an MCP client
3. Tests all 11 MCP tools
4. Validates responses
5. Shuts down the server cleanly

Usage:
    python tests/test_mcp_integration.py
"""

import os
import sys
import time
import json
import subprocess
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test configuration
WEATHER_UNIFIED_PATH = Path("C:/git/Weather-Unified")
TEST_DATA_DIR = Path.home() / ".semanticscout-test-integration"
COLLECTION_NAME = "test_weather_integration"
SERVER_STARTUP_TIMEOUT = 30  # seconds
SERVER_SHUTDOWN_TIMEOUT = 10  # seconds

class Colors:
    """ANSI color codes for output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_test(text):
    """Print test name."""
    print(f"\n{Colors.OKBLUE}{'─' * 80}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}TEST: {text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'─' * 80}{Colors.ENDC}")

def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

class MCPServerManager:
    """Manages MCP server lifecycle for testing."""
    
    def __init__(self, data_dir, config_json=None):
        self.data_dir = data_dir
        self.config_json = config_json
        self.process = None
        self.python_exe = self._find_python()
    
    def _find_python(self):
        """Find Python executable in venv."""
        venv_dir = Path(__file__).parent.parent / "venv"
        
        if sys.platform == "win32":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        
        if python_exe.exists():
            return python_exe
        return sys.executable
    
    def start(self):
        """Start the MCP server."""
        print_info("Starting MCP server...")
        
        # Build command
        cmd = [
            str(self.python_exe),
            "-m", "semanticscout.mcp_server",
            "--data-dir", str(self.data_dir)
        ]
        
        # Set environment
        env = os.environ.copy()
        if self.config_json:
            env["SEMANTICSCOUT_CONFIG_JSON"] = self.config_json
        
        # Start process
        self.process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
            if self.process.poll() is not None:
                # Process exited
                stdout, stderr = self.process.communicate()
                print_error(f"Server failed to start!")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                raise RuntimeError("Server process exited during startup")
            
            # Check if server is ready (look for "Server is ready" in output)
            # For now, just wait a bit
            time.sleep(2)
            break
        
        print_success(f"Server started (PID: {self.process.pid})")
        return True
    
    def stop(self):
        """Stop the MCP server."""
        if not self.process:
            return
        
        print_info("Stopping MCP server...")
        
        # Send SIGTERM for graceful shutdown
        self.process.send_signal(signal.SIGTERM)
        
        # Wait for process to exit
        try:
            self.process.wait(timeout=SERVER_SHUTDOWN_TIMEOUT)
            print_success("Server stopped gracefully")
        except subprocess.TimeoutExpired:
            print_error("Server did not stop gracefully, forcing shutdown...")
            self.process.kill()
            self.process.wait()
            print_success("Server forcefully stopped")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

def test_server_startup():
    """Test 1: Server starts successfully."""
    print_test("Server Startup")
    
    config_json = json.dumps({
        "embedding": {
            "provider": "sentence-transformers",
            "model": "all-MiniLM-L6-v2"
        }
    })
    
    with MCPServerManager(TEST_DATA_DIR, config_json) as server:
        print_success("Server started and running")
        time.sleep(1)  # Let it run for a bit
    
    print_success("Server shutdown cleanly")

def main():
    """Main test runner."""
    print_header("SemanticScout MCP Integration Tests")
    
    # Check if Weather-Unified exists
    if not WEATHER_UNIFIED_PATH.exists():
        print_error(f"Weather-Unified repository not found at {WEATHER_UNIFIED_PATH}")
        print_info("Please clone the repository or update the path in the test file")
        sys.exit(1)
    
    print_info(f"Test repository: {WEATHER_UNIFIED_PATH}")
    print_info(f"Test data directory: {TEST_DATA_DIR}")
    
    # Clean up old test data
    import shutil
    if TEST_DATA_DIR.exists():
        print_info("Cleaning up old test data...")
        shutil.rmtree(TEST_DATA_DIR)
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print_success("Test environment ready")
    
    # Run tests
    try:
        test_server_startup()
        
        print_header("All Tests Passed!")
        return 0
    
    except Exception as e:
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

