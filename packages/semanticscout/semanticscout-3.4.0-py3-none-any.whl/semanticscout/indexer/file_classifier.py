"""
File classification module for detecting test files vs production code.

This module provides multi-strategy test file detection using:
1. Directory path patterns (e.g., /tests/, /test/, /__tests__/)
2. File name patterns (e.g., .test., .spec., Test.cs, _test.py)
3. AST-based detection (test decorators/attributes like @Test, [TestMethod])
"""

import re
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FileClassifier:
    """
    Classifies files as test code or production code using multiple detection strategies.
    
    Strategies:
    1. Path-based: Checks if file is in test directory
    2. Name-based: Checks if filename matches test patterns
    3. AST-based: Checks for test decorators/attributes in code
    """
    
    # Directory patterns that indicate test code
    TEST_DIR_PATTERNS = [
        r'[/\\]tests?[/\\]',           # /test/ or /tests/
        r'[/\\]__tests__[/\\]',        # /__tests__/ (JavaScript)
        r'[/\\]spec[/\\]',             # /spec/ (Ruby, JavaScript)
        r'[/\\]\.pytest_cache[/\\]',   # /.pytest_cache/ (Python)
        r'[/\\]test_.*[/\\]',          # /test_*/ (Python)
        r'[/\\].*\.tests?[/\\]',       # /*.test/ or /*.tests/ (C#)
        r'[/\\]testing[/\\]',          # /testing/
        r'[/\\]__pycache__[/\\]',      # /__pycache__/ (Python)
    ]
    
    # File name patterns that indicate test code
    TEST_FILE_PATTERNS = [
        r'\.test\.',                    # .test. (JavaScript/TypeScript)
        r'\.spec\.',                    # .spec. (JavaScript/TypeScript/Angular)
        r'Tests?\.(cs|py|js|ts|java|go|rb|php)',  # Test.cs, Tests.py, etc.
        r'_test\.(py|go)',              # _test.py, _test.go
        r'test_.*\.py',                 # test_*.py (Python)
        r'.*Test\.(java|kt)',           # *Test.java, *Test.kt (Java/Kotlin)
        r'.*Tests\.(cs|vb)',            # *Tests.cs, *Tests.vb (C#/VB.NET)
        r'.*Spec\.(js|ts|rb)',          # *Spec.js, *Spec.ts, *Spec.rb
        r'.*\.test\.(js|ts|jsx|tsx)',   # *.test.js, *.test.tsx
        r'.*\.spec\.(js|ts|jsx|tsx)',   # *.spec.js, *.spec.tsx
    ]
    
    # AST-based test indicators (decorators, attributes, imports)
    TEST_AST_PATTERNS = [
        # Python test decorators
        r'@pytest\.',
        r'@unittest\.',
        r'@test',
        r'from\s+pytest\s+import',
        r'from\s+unittest\s+import',
        r'import\s+pytest',
        r'import\s+unittest',
        
        # C# test attributes
        r'\[Test\]',
        r'\[TestMethod\]',
        r'\[Fact\]',
        r'\[Theory\]',
        r'\[TestCase',
        r'using\s+Xunit',
        r'using\s+NUnit',
        r'using\s+Microsoft\.VisualStudio\.TestTools',
        
        # Java test annotations
        r'@Test',
        r'@RunWith',
        r'@Before',
        r'@After',
        r'import\s+org\.junit',
        r'import\s+org\.testng',
        
        # JavaScript/TypeScript test frameworks
        r'describe\(',
        r'it\(',
        r'test\(',
        r'expect\(',
        r'from\s+[\'"]jest[\'"]',
        r'from\s+[\'"]mocha[\'"]',
        r'from\s+[\'"]@testing-library',
    ]
    
    # Penalty factor for test files (reduces similarity score by 70%)
    TEST_PENALTY = 0.3
    PRODUCTION_PENALTY = 1.0

    # DI configuration file name patterns (NEW)
    DI_CONFIG_FILE_PATTERNS = [
        r'Startup\.cs$',           # ASP.NET Core Startup.cs
        r'Program\.cs$',           # ASP.NET Core Program.cs
        r'Startup\.vb$',           # VB.NET Startup.vb
        r'main\.py$',              # Python main.py
        r'app\.py$',               # Flask/FastAPI app.py
        r'[Aa]pp[Mm]odule\.ts$',   # Angular AppModule.ts
        r'[Aa]pp[Mm]odule\.js$',   # NestJS app.module.js
        r'[Mm]ain\.ts$',           # NestJS main.ts
        r'[Cc]onfig\.py$',         # Python config.py
        r'[Ss]ettings\.py$',       # Django settings.py
    ]

    # DI configuration content patterns (NEW)
    DI_CONFIG_CONTENT_PATTERNS = [
        # ASP.NET Core DI patterns
        r'\.AddScoped<',
        r'\.AddSingleton<',
        r'\.AddTransient<',
        r'services\.Add',
        r'ConfigureServices',
        r'IServiceCollection',

        # Python DI patterns
        r'@injectable',
        r'container\.register',
        r'dependency_injector',
        r'@inject',

        # NestJS/Angular DI patterns
        r'@Module\(',
        r'@Injectable\(',
        r'providers:\s*\[',

        # Spring Boot DI patterns
        r'@Configuration',
        r'@Bean',
        r'@Component',
    ]

    # Boost factor for DI configuration files (increases similarity score by 2x)
    DI_CONFIG_BOOST = 2.0

    @classmethod
    def is_test_file(cls, file_path: str) -> bool:
        """
        Check if a file is a test file based on path and name patterns.
        
        Args:
            file_path: Path to the file (relative or absolute)
            
        Returns:
            True if file is detected as test code, False otherwise
        """
        # Normalize path separators
        normalized_path = file_path.replace('\\', '/')
        
        # Check directory patterns
        for pattern in cls.TEST_DIR_PATTERNS:
            if re.search(pattern, normalized_path, re.IGNORECASE):
                logger.debug(f"File {file_path} matched test directory pattern: {pattern}")
                return True
        
        # Check file name patterns
        file_name = Path(file_path).name
        for pattern in cls.TEST_FILE_PATTERNS:
            if re.search(pattern, file_name, re.IGNORECASE):
                logger.debug(f"File {file_path} matched test file pattern: {pattern}")
                return True
        
        return False
    
    @classmethod
    def is_test_file_by_ast(cls, file_content: Optional[str]) -> bool:
        """
        Check if a file is a test file based on AST patterns (decorators, imports).
        
        Args:
            file_content: Content of the file to analyze
            
        Returns:
            True if file contains test-related patterns, False otherwise
        """
        if not file_content:
            return False
        
        # Count matches to avoid false positives from single occurrences
        match_count = 0
        for pattern in cls.TEST_AST_PATTERNS:
            if re.search(pattern, file_content, re.MULTILINE):
                match_count += 1
                if match_count >= 2:  # Require at least 2 matches for confidence
                    logger.debug(f"File content matched {match_count} test AST patterns")
                    return True
        
        return False

    @classmethod
    def is_di_configuration_file(cls, file_path: str, file_content: Optional[str] = None) -> bool:
        """
        Check if a file is a DI configuration file (Startup.cs, Program.cs, etc.).

        Uses two strategies:
        1. File name patterns (Startup.cs, Program.cs, main.py, etc.)
        2. Content patterns (AddScoped, AddSingleton, ConfigureServices, etc.)

        Args:
            file_path: Path to the file
            file_content: Optional file content for pattern matching

        Returns:
            True if file is a DI configuration file, False otherwise
        """
        # Strategy 1: File name-based detection
        file_name = Path(file_path).name
        for pattern in cls.DI_CONFIG_FILE_PATTERNS:
            if re.search(pattern, file_name, re.IGNORECASE):
                logger.debug(f"File {file_name} matched DI config file pattern: {pattern}")
                return True

        # Strategy 2: Content-based detection (require multiple matches to avoid false positives)
        if file_content:
            match_count = 0
            for pattern in cls.DI_CONFIG_CONTENT_PATTERNS:
                if re.search(pattern, file_content, re.MULTILINE):
                    match_count += 1
                    if match_count >= 3:  # Require at least 3 DI patterns for confidence
                        logger.debug(f"File content matched {match_count} DI config patterns")
                        return True

        return False

    @classmethod
    def classify_file(
        cls,
        file_path: str,
        file_content: Optional[str] = None
    ) -> Tuple[str, float, str]:
        """
        Classify a file and return file type, penalty factor, and category.

        Uses multiple strategies:
        1. DI configuration detection (Startup.cs, Program.cs, etc.)
        2. Test file detection (path, name, AST patterns)
        3. Default to production code

        Args:
            file_path: Path to the file
            file_content: Optional file content for pattern matching

        Returns:
            Tuple of (file_type, penalty_factor, file_category) where:
            - file_type is 'test', 'production', or 'di_configuration'
            - penalty_factor is TEST_PENALTY (0.3) for test, PRODUCTION_PENALTY (1.0) for production, DI_CONFIG_BOOST (2.0) for DI config
            - file_category is 'test', 'production', or 'di_configuration'

        Examples:
            >>> FileClassifier.classify_file('Startup.cs')
            ('production', 2.0, 'di_configuration')

            >>> FileClassifier.classify_file('tests/test_api.py')
            ('test', 0.3, 'test')

            >>> FileClassifier.classify_file('src/api/service.py')
            ('production', 1.0, 'production')
        """
        # BUG FIX 251: Test file detection MUST have higher priority than DI configuration
        # Priority 1: Check for test files (path/name patterns)
        if cls.is_test_file(file_path):
            logger.info(f"Classified {file_path} as TEST (path/name pattern)")
            return ('test', cls.TEST_PENALTY, 'test')

        # Priority 2: AST-based test detection (if content provided)
        if file_content and cls.is_test_file_by_ast(file_content):
            logger.info(f"Classified {file_path} as TEST (AST pattern)")
            return ('test', cls.TEST_PENALTY, 'test')

        # Priority 3: Check for DI configuration files
        if cls.is_di_configuration_file(file_path, file_content):
            logger.info(f"Classified {file_path} as DI_CONFIGURATION")
            return ('production', cls.DI_CONFIG_BOOST, 'di_configuration')

        # Default to production code
        logger.debug(f"Classified {file_path} as PRODUCTION")
        return ('production', cls.PRODUCTION_PENALTY, 'production')
    
    @classmethod
    def get_test_penalty(cls) -> float:
        """Get the penalty factor applied to test files."""
        return cls.TEST_PENALTY
    
    @classmethod
    def get_production_penalty(cls) -> float:
        """Get the penalty factor applied to production files (no penalty)."""
        return cls.PRODUCTION_PENALTY

