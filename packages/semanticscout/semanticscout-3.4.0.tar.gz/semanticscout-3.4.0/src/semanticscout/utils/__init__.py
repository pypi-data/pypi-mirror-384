"""
Utility modules for SemanticScout.
"""

from .model_compatibility import (
    EmbeddingModelCompatibilityChecker,
    CompatibilityResult,
    CompatibilityStatus,
)

from .gpu_utils import (
    detect_gpu_availability,
    get_gpu_info,
    get_gpu_memory_info,
    validate_device_string,
    detect_optimal_device,
    get_optimal_batch_size,
    format_memory_size,
    log_gpu_status,
)

__all__ = [
    "EmbeddingModelCompatibilityChecker",
    "CompatibilityResult",
    "CompatibilityStatus",
    "detect_gpu_availability",
    "get_gpu_info",
    "get_gpu_memory_info",
    "validate_device_string",
    "detect_optimal_device",
    "get_optimal_batch_size",
    "format_memory_size",
    "log_gpu_status",
]

