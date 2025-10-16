"""
Parallel processing utilities for improved performance.

This module provides utilities for parallel file processing during indexing.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Optional, TypeVar, Iterable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class ParallelResult:
    """Result from parallel processing."""
    success_count: int
    failure_count: int
    results: List[Any]
    errors: List[Exception]


def process_in_parallel(
    items: Iterable[T],
    process_func: Callable[[T], R],
    max_workers: Optional[int] = None,
    description: str = "Processing items"
) -> ParallelResult:
    """
    Process items in parallel using a thread pool.
    
    Args:
        items: Items to process
        process_func: Function to apply to each item
        max_workers: Maximum number of worker threads (None = CPU count)
        description: Description for logging
        
    Returns:
        ParallelResult with success/failure counts and results
    """
    results = []
    errors = []
    success_count = 0
    failure_count = 0
    
    items_list = list(items)
    total = len(items_list)
    
    logger.info(f"{description}: Processing {total} items with {max_workers or 'auto'} workers")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {
            executor.submit(process_func, item): item
            for item in items_list
        }
        
        # Process completed tasks
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                results.append(result)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to process item: {e}")
                errors.append(e)
                failure_count += 1
    
    logger.info(
        f"{description}: Completed {success_count} successful, "
        f"{failure_count} failed out of {total} total"
    )
    
    return ParallelResult(
        success_count=success_count,
        failure_count=failure_count,
        results=results,
        errors=errors
    )


def batch_process_in_parallel(
    items: List[T],
    process_func: Callable[[List[T]], R],
    batch_size: int,
    max_workers: Optional[int] = None,
    description: str = "Processing batches"
) -> ParallelResult:
    """
    Process items in parallel batches.
    
    Args:
        items: Items to process
        process_func: Function to apply to each batch
        batch_size: Number of items per batch
        max_workers: Maximum number of worker threads
        description: Description for logging
        
    Returns:
        ParallelResult with success/failure counts and results
    """
    # Create batches
    batches = [
        items[i:i + batch_size]
        for i in range(0, len(items), batch_size)
    ]
    
    logger.info(
        f"{description}: Processing {len(items)} items in "
        f"{len(batches)} batches of {batch_size}"
    )
    
    # Process batches in parallel
    return process_in_parallel(
        batches,
        process_func,
        max_workers=max_workers,
        description=f"{description} (batched)"
    )

