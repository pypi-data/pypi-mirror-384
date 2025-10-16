"""
File encoding detection and handling utilities.

Provides robust file reading with automatic encoding detection and binary file filtering.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import chardet

logger = logging.getLogger(__name__)

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    # Executables and libraries
    '.exe', '.dll', '.so', '.dylib', '.a', '.lib', '.o', '.obj',
    # Archives
    '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar', '.xz',
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
    # Audio/Video
    '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac', '.ogg',
    # Documents (binary formats)
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # Databases
    '.db', '.sqlite', '.sqlite3',
    # Other binary
    '.pyc', '.pyo', '.class', '.jar', '.war',
}


def is_binary_file(file_path: Path) -> bool:
    """
    Check if a file is binary based on extension and content.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if file is binary, False otherwise
    """
    # Check extension first (fast)
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    
    # Check for null bytes in first 8KB (more thorough)
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(8192)
            if b'\x00' in chunk:
                return True
    except Exception as e:
        logger.warning(f"Could not check if {file_path} is binary: {e}")
        return True  # Assume binary if we can't read it
    
    return False


def detect_encoding(file_path: Path, sample_size: int = 65536) -> Optional[str]:
    """
    Detect the encoding of a file using chardet.
    
    Args:
        file_path: Path to the file
        sample_size: Number of bytes to sample for detection (default: 64KB)
        
    Returns:
        Detected encoding name, or None if detection failed
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(sample_size)
        
        if not raw_data:
            return 'utf-8'  # Empty file, default to UTF-8
        
        result = chardet.detect(raw_data)
        encoding = result.get('encoding')
        confidence = result.get('confidence', 0.0)
        
        # Only trust high-confidence detections
        if encoding and confidence > 0.7:
            logger.debug(f"Detected encoding {encoding} with confidence {confidence:.2f} for {file_path}")
            return encoding
        
        logger.debug(f"Low confidence ({confidence:.2f}) encoding detection for {file_path}, will try fallbacks")
        return None
        
    except Exception as e:
        logger.warning(f"Encoding detection failed for {file_path}: {e}")
        return None


def read_file_with_encoding_detection(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Read a file with automatic encoding detection and fallback strategies.
    
    Strategy:
    1. Try UTF-8 with BOM handling (utf-8-sig)
    2. Detect encoding with chardet
    3. Try detected encoding
    4. Fallback to Latin-1 (never fails, but may produce garbage)
    5. If all else fails, return None
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Tuple of (file_content, encoding_used) or (None, None) if file should be skipped
    """
    # Check if binary file first
    if is_binary_file(file_path):
        logger.debug(f"Skipping binary file: {file_path}")
        return None, None
    
    # Strategy 1: Try UTF-8 with BOM handling
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        logger.debug(f"Successfully read {file_path} with UTF-8")
        return content, 'utf-8-sig'
    except UnicodeDecodeError:
        logger.debug(f"UTF-8 decoding failed for {file_path}, trying detection")
    except Exception as e:
        logger.warning(f"Error reading {file_path} with UTF-8: {e}")
        return None, None
    
    # Strategy 2: Detect encoding
    detected_encoding = detect_encoding(file_path)
    
    if detected_encoding:
        try:
            with open(file_path, 'r', encoding=detected_encoding) as f:
                content = f.read()
            logger.debug(f"Successfully read {file_path} with detected encoding {detected_encoding}")
            return content, detected_encoding
        except (UnicodeDecodeError, LookupError) as e:
            logger.debug(f"Detected encoding {detected_encoding} failed for {file_path}: {e}")
    
    # Strategy 3: Fallback to Latin-1 (ISO-8859-1)
    # Latin-1 never fails because it maps all byte values to Unicode
    try:
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
        logger.warning(f"Using Latin-1 fallback for {file_path} - content may be incorrect")
        return content, 'latin-1'
    except Exception as e:
        logger.error(f"Even Latin-1 fallback failed for {file_path}: {e}")
        return None, None


def safe_read_file(file_path: Path) -> Optional[str]:
    """
    Safely read a file with encoding detection, returning None if file should be skipped.
    
    This is a convenience wrapper around read_file_with_encoding_detection that only
    returns the content (not the encoding used).
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File content as string, or None if file should be skipped
    """
    content, _ = read_file_with_encoding_detection(file_path)
    return content

