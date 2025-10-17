#!/usr/bin/env python3
"""
Timing utilities for performance monitoring across all modules.
"""

import time
import logging
from functools import wraps
from typing import Any, Callable
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class TimingLogger:
    """Centralized timing logger for performance tracking."""
    
    def __init__(self):
        self.timings = {}
        self.start_times = {}
    
    def start(self, operation: str):
        """Start timing an operation."""
        self.start_times[operation] = time.time()
        logger.debug(f"TIMING START: {operation}")
    
    def end(self, operation: str) -> float:
        """End timing an operation and return elapsed time."""
        if operation not in self.start_times:
            logger.warning(f"TIMING WARNING: No start time for {operation}")
            return 0.0
        
        elapsed = time.time() - self.start_times[operation]
        del self.start_times[operation]
        
        # Store timing
        if operation not in self.timings:
            self.timings[operation] = []
        self.timings[operation].append(elapsed)
        
        # Log with appropriate level based on duration
        if elapsed > 10:
            logger.warning(f"TIMING SLOW: {operation} took {elapsed:.2f}s (>10s)")
        elif elapsed > 5:
            logger.debug(f"TIMING MODERATE: {operation} took {elapsed:.2f}s (5-10s)")
        else:
            logger.debug(f"TIMING COMPLETE: {operation} took {elapsed:.2f}s")
        
        return elapsed
    
    def get_summary(self) -> dict:
        """Get summary of all timings."""
        summary = {}
        for operation, times in self.timings.items():
            summary[operation] = {
                "count": len(times),
                "total": sum(times),
                "average": sum(times) / len(times) if times else 0,
                "min": min(times) if times else 0,
                "max": max(times) if times else 0
            }
        return summary
    
    def log_summary(self):
        """Log a formatted summary of all timings."""
        summary = self.get_summary()
        logger.debug("=" * 60)
        logger.debug("TIMING SUMMARY")
        logger.debug("=" * 60)
        
        # Sort by total time descending
        sorted_ops = sorted(summary.items(), key=lambda x: x[1]["total"], reverse=True)
        
        for operation, stats in sorted_ops:
            logger.debug(
                f"{operation}: "
                f"Total={stats['total']:.2f}s, "
                f"Avg={stats['average']:.2f}s, "
                f"Count={stats['count']}, "
                f"Min={stats['min']:.2f}s, "
                f"Max={stats['max']:.2f}s"
            )
        logger.debug("=" * 60)

# Global timing logger instance
timing_logger = TimingLogger()

@contextmanager
def time_operation(operation_name: str):
    """Context manager for timing operations.
    
    Usage:
        with time_operation("Module 1: Database Query"):
            # Your code here
            results = query_database()
    """
    timing_logger.start(operation_name)
    try:
        yield
    finally:
        timing_logger.end(operation_name)

def timed_function(operation_name: str = None):
    """Decorator for timing function execution.
    
    Usage:
        @timed_function("Process Data")
        def process_data(data):
            # Your code here
            return processed_data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            with time_operation(op_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def log_module_performance(module_name: str, stage: str, start_time: float):
    """Log performance for a specific module stage."""
    elapsed = time.time() - start_time
    logger.debug(f"PERFORMANCE: {module_name} - {stage}: {elapsed:.3f}s")
    return elapsed