"""
GPU utilities for SemanticScout.

This module provides utilities for GPU detection, device management, and optimization
for sentence-transformers embedding generation.
"""

import logging
from typing import Dict, Optional, Tuple, Any
import warnings

logger = logging.getLogger(__name__)

# Try to import torch for GPU detection
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


def detect_gpu_availability() -> bool:
    """
    Detect if GPU/CUDA is available for PyTorch.
    
    Returns:
        True if GPU is available and functional, False otherwise
    """
    if not TORCH_AVAILABLE:
        logger.debug("PyTorch not available, GPU detection skipped")
        return False
    
    try:
        return torch.cuda.is_available()
    except Exception as e:
        logger.warning(f"Error checking GPU availability: {e}")
        return False


def get_gpu_info() -> Dict[str, Any]:
    """
    Get detailed GPU information.
    
    Returns:
        Dictionary containing GPU information
    """
    info = {
        "torch_available": TORCH_AVAILABLE,
        "cuda_available": False,
        "device_count": 0,
        "devices": [],
        "current_device": None,
        "cuda_version": None,
    }
    
    if not TORCH_AVAILABLE:
        return info
    
    try:
        info["cuda_available"] = torch.cuda.is_available()
        
        if info["cuda_available"]:
            info["device_count"] = torch.cuda.device_count()
            info["cuda_version"] = torch.version.cuda
            
            # Get information about each GPU device
            for i in range(info["device_count"]):
                device_props = torch.cuda.get_device_properties(i)
                device_info = {
                    "index": i,
                    "name": device_props.name,
                    "total_memory": device_props.total_memory,
                    "major": device_props.major,
                    "minor": device_props.minor,
                    "multi_processor_count": device_props.multi_processor_count,
                }
                info["devices"].append(device_info)
            
            # Get current device if any
            try:
                info["current_device"] = torch.cuda.current_device()
            except Exception:
                pass
                
    except Exception as e:
        logger.warning(f"Error getting GPU info: {e}")
    
    return info


def get_gpu_memory_info(device_index: Optional[int] = None) -> Dict[str, int]:
    """
    Get GPU memory usage information.
    
    Args:
        device_index: GPU device index (None for current device)
        
    Returns:
        Dictionary with memory information in bytes
    """
    memory_info = {
        "total": 0,
        "allocated": 0,
        "cached": 0,
        "free": 0,
    }
    
    if not TORCH_AVAILABLE or not torch.cuda.is_available():
        return memory_info
    
    try:
        if device_index is not None:
            device = f"cuda:{device_index}"
        else:
            device = torch.cuda.current_device()
        
        memory_info["total"] = torch.cuda.get_device_properties(device).total_memory
        memory_info["allocated"] = torch.cuda.memory_allocated(device)
        memory_info["cached"] = torch.cuda.memory_reserved(device)
        memory_info["free"] = memory_info["total"] - memory_info["allocated"]
        
    except Exception as e:
        logger.warning(f"Error getting GPU memory info: {e}")
    
    return memory_info


def validate_device_string(device: str) -> Tuple[bool, str]:
    """
    Validate a device string and return whether it's valid.
    
    Args:
        device: Device string (e.g., 'cuda', 'cpu', 'cuda:0', 'auto')
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not device:
        return False, "Device string cannot be empty"
    
    device = device.lower().strip()
    
    # Valid device patterns
    if device in ["cpu", "auto"]:
        return True, ""
    
    if device == "cuda":
        if not TORCH_AVAILABLE:
            return False, "PyTorch not available for CUDA device"
        if not torch.cuda.is_available():
            return False, "CUDA not available on this system"
        return True, ""
    
    # Check for specific CUDA device (e.g., cuda:0, cuda:1)
    if device.startswith("cuda:"):
        if not TORCH_AVAILABLE:
            return False, "PyTorch not available for CUDA device"
        if not torch.cuda.is_available():
            return False, "CUDA not available on this system"
        
        try:
            device_index = int(device.split(":")[1])
            device_count = torch.cuda.device_count()
            if device_index >= device_count:
                return False, f"CUDA device {device_index} not available (only {device_count} devices found)"
            return True, ""
        except (ValueError, IndexError):
            return False, f"Invalid CUDA device format: {device}"
    
    return False, f"Unknown device type: {device}"


def detect_optimal_device(preference: str = "auto") -> str:
    """
    Detect the optimal device based on preference and availability.
    
    Args:
        preference: Device preference ('auto', 'cuda', 'cpu', 'cuda:0', etc.)
        
    Returns:
        Optimal device string ('cuda', 'cpu', or specific device)
    """
    preference = preference.lower().strip()
    
    # Validate preference first
    is_valid, error_msg = validate_device_string(preference)
    if not is_valid:
        logger.warning(f"Invalid device preference '{preference}': {error_msg}. Falling back to auto.")
        preference = "auto"
    
    # Handle explicit preferences
    if preference == "cpu":
        logger.info("Using CPU as explicitly requested")
        return "cpu"
    
    if preference.startswith("cuda"):
        if preference == "cuda" or preference.startswith("cuda:"):
            # Preference is for CUDA, check if available
            if TORCH_AVAILABLE and torch.cuda.is_available():
                logger.info(f"Using {preference} as requested")
                return preference
            else:
                logger.warning(f"CUDA requested but not available, falling back to CPU")
                return "cpu"
    
    # Auto detection
    if preference == "auto":
        if TORCH_AVAILABLE and torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            logger.info(f"Auto-detected CUDA with {device_count} device(s), using cuda")
            return "cuda"
        else:
            logger.info("Auto-detected CPU (CUDA not available)")
            return "cpu"
    
    # Fallback
    logger.warning(f"Unknown preference '{preference}', falling back to CPU")
    return "cpu"


def get_optimal_batch_size(device: str, default_gpu: int = 64, default_cpu: int = 16) -> int:
    """
    Get optimal batch size based on device type.
    
    Args:
        device: Device string
        default_gpu: Default batch size for GPU
        default_cpu: Default batch size for CPU
        
    Returns:
        Optimal batch size
    """
    if device and device.lower().startswith("cuda"):
        return default_gpu
    else:
        return default_cpu


def format_memory_size(bytes_size: int) -> str:
    """
    Format memory size in human-readable format.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "2.5 GB")
    """
    if bytes_size == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_size)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def log_gpu_status() -> None:
    """Log current GPU status for debugging."""
    gpu_info = get_gpu_info()
    
    logger.info("=== GPU Status ===")
    logger.info(f"PyTorch available: {gpu_info['torch_available']}")
    logger.info(f"CUDA available: {gpu_info['cuda_available']}")
    
    if gpu_info['cuda_available']:
        logger.info(f"CUDA version: {gpu_info['cuda_version']}")
        logger.info(f"GPU device count: {gpu_info['device_count']}")
        
        for device in gpu_info['devices']:
            memory_str = format_memory_size(device['total_memory'])
            logger.info(f"  GPU {device['index']}: {device['name']} ({memory_str})")
        
        if gpu_info['current_device'] is not None:
            memory_info = get_gpu_memory_info()
            allocated_str = format_memory_size(memory_info['allocated'])
            total_str = format_memory_size(memory_info['total'])
            logger.info(f"Current device: {gpu_info['current_device']} "
                       f"(Memory: {allocated_str}/{total_str})")
    else:
        logger.info("No CUDA devices available")
    
    logger.info("==================")
