#!/usr/bin/env python3
"""
Personal Password Manager - Performance Monitor
================================================

This module provides comprehensive performance monitoring and profiling
capabilities for the password manager system.

Key Features:
- Operation timing and profiling
- Cache hit rate monitoring
- Database query performance tracking
- Memory usage monitoring
- Performance metrics aggregation
- Automated performance reporting

Author: Personal Password Manager
Version: 2.2.0
"""

import functools
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class OperationMetrics:
    """Metrics for a single operation"""

    operation_name: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds"""
        return self.duration_ms / 1000.0


class PerformanceMonitor:
    """
    Performance monitoring and profiling system

    Tracks operation timing, cache performance, and system metrics
    to identify bottlenecks and optimize performance.
    """

    def __init__(self, max_history: int = 1000, enable_detailed_tracking: bool = True):
        """
        Initialize performance monitor

        Args:
            max_history: Maximum number of operations to keep in history
            enable_detailed_tracking: Enable detailed per-operation tracking
        """
        self.max_history = max_history
        self.enable_detailed_tracking = enable_detailed_tracking

        # Thread safety
        self._lock = threading.RLock()

        # Operation metrics
        self._operation_history: deque = deque(maxlen=max_history)
        self._operation_stats: Dict[str, Dict[str, Any]] = defaultdict(self._default_stats)

        # Current operations (for nested timing)
        self._current_operations: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

        logger.info(f"Performance monitor initialized (max_history={max_history})")

    def _default_stats(self) -> Dict[str, Any]:
        """Get default statistics structure"""
        return {
            "count": 0,
            "total_time_ms": 0.0,
            "min_time_ms": float("in"),
            "max_time_ms": 0.0,
            "avg_time_ms": 0.0,
            "success_count": 0,
            "failure_count": 0,
            "last_execution": None,
        }

    def start_operation(
        self, operation_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Start timing an operation

        Args:
            operation_name: Name of the operation
            metadata: Additional metadata to track

        Returns:
            int: Operation ID for use with end_operation
        """
        with self._lock:
            thread_id = threading.get_ident()
            operation_id = id((thread_id, time.time()))

            operation = {
                "id": operation_id,
                "name": operation_name,
                "start_time": time.time(),
                "metadata": metadata or {},
            }

            self._current_operations[thread_id].append(operation)

            return operation_id

    def end_operation(
        self, operation_id: int, success: bool = True, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[OperationMetrics]:
        """
        End timing an operation

        Args:
            operation_id: Operation ID from start_operation
            success: Whether the operation succeeded
            metadata: Additional metadata to add

        Returns:
            OperationMetrics: Metrics for the completed operation
        """
        with self._lock:
            thread_id = threading.get_ident()
            operations = self._current_operations[thread_id]

            # Find and remove the operation
            operation = None
            for i, op in enumerate(operations):
                if op["id"] == operation_id:
                    operation = operations.pop(i)
                    break

            if not operation:
                logger.warning(f"Operation {operation_id} not found in current operations")
                return None

            # Calculate metrics
            end_time = time.time()
            duration_ms = (end_time - operation["start_time"]) * 1000

            # Merge metadata
            full_metadata = operation["metadata"].copy()
            if metadata:
                full_metadata.update(metadata)

            metrics = OperationMetrics(
                operation_name=operation["name"],
                start_time=operation["start_time"],
                end_time=end_time,
                duration_ms=duration_ms,
                success=success,
                metadata=full_metadata,
            )

            # Record metrics
            self._record_metrics(metrics)

            return metrics

    def _record_metrics(self, metrics: OperationMetrics) -> None:
        """
        Record operation metrics

        Args:
            metrics: Operation metrics to record
        """
        with self._lock:
            # Add to history
            if self.enable_detailed_tracking:
                self._operation_history.append(metrics)

            # Update statistics
            stats = self._operation_stats[metrics.operation_name]
            stats["count"] += 1
            stats["total_time_ms"] += metrics.duration_ms
            stats["min_time_ms"] = min(stats["min_time_ms"], metrics.duration_ms)
            stats["max_time_ms"] = max(stats["max_time_ms"], metrics.duration_ms)
            stats["avg_time_ms"] = stats["total_time_ms"] / stats["count"]
            stats["last_execution"] = datetime.now()

            if metrics.success:
                stats["success_count"] += 1
            else:
                stats["failure_count"] += 1

    def get_operation_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for operations

        Args:
            operation_name: Specific operation name, or None for all

        Returns:
            Dict with operation statistics
        """
        with self._lock:
            if operation_name:
                return self._operation_stats.get(operation_name, self._default_stats()).copy()
            else:
                return {name: stats.copy() for name, stats in self._operation_stats.items()}

    def get_recent_operations(
        self, count: int = 100, operation_name: Optional[str] = None
    ) -> List[OperationMetrics]:
        """
        Get recent operations

        Args:
            count: Number of operations to return
            operation_name: Filter by operation name

        Returns:
            List of recent operation metrics
        """
        with self._lock:
            operations = list(self._operation_history)

            if operation_name:
                operations = [op for op in operations if op.operation_name == operation_name]

            return operations[-count:]

    def get_slow_operations(
        self, threshold_ms: float = 100, count: int = 10
    ) -> List[OperationMetrics]:
        """
        Get slowest operations above threshold

        Args:
            threshold_ms: Minimum duration in milliseconds
            count: Number of operations to return

        Returns:
            List of slow operations, sorted by duration
        """
        with self._lock:
            slow_ops = [op for op in self._operation_history if op.duration_ms >= threshold_ms]
            slow_ops.sort(key=lambda op: op.duration_ms, reverse=True)
            return slow_ops[:count]

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary

        Returns:
            Dict with performance summary
        """
        with self._lock:
            total_operations = sum(stats["count"] for stats in self._operation_stats.values())
            total_time_ms = sum(stats["total_time_ms"] for stats in self._operation_stats.values())

            # Find slowest operations
            slowest_ops = []
            for name, stats in self._operation_stats.items():
                if stats["count"] > 0:
                    slowest_ops.append(
                        {
                            "operation": name,
                            "avg_time_ms": stats["avg_time_ms"],
                            "max_time_ms": stats["max_time_ms"],
                            "count": stats["count"],
                        }
                    )
            slowest_ops.sort(key=lambda x: x["avg_time_ms"], reverse=True)

            # Calculate failure rate
            total_failures = sum(stats["failure_count"] for stats in self._operation_stats.values())
            failure_rate = (total_failures / total_operations * 100) if total_operations > 0 else 0

            return {
                "total_operations": total_operations,
                "total_time_ms": total_time_ms,
                "avg_time_ms": total_time_ms / total_operations if total_operations > 0 else 0,
                "failure_rate": failure_rate,
                "operations_tracked": len(self._operation_stats),
                "history_size": len(self._operation_history),
                "slowest_operations": slowest_ops[:10],
            }

    def reset_metrics(self) -> None:
        """Reset all performance metrics"""
        with self._lock:
            self._operation_history.clear()
            self._operation_stats.clear()
            logger.info("Performance metrics reset")

    def monitor(self, operation_name: Optional[str] = None):
        """
        Decorator to monitor function performance

        Args:
            operation_name: Name for the operation (defaults to function name)

        Example:
            @monitor.monitor("search_passwords")
            def search_passwords(...):
                ...
        """

        def decorator(func: Callable) -> Callable:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Start monitoring
                op_id = self.start_operation(op_name)

                success = True
                result = None
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    raise
                finally:
                    # End monitoring
                    self.end_operation(op_id, success=success)

            return wrapper

        return decorator


class PerformanceTracker:
    """
    Context manager for tracking operation performance

    Usage:
        with PerformanceTracker(monitor, "database_query") as tracker:
            # Perform operation
            tracker.add_metadata({"rows": 100})
    """

    def __init__(
        self,
        monitor: PerformanceMonitor,
        operation_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize performance tracker

        Args:
            monitor: Performance monitor instance
            operation_name: Name of the operation
            metadata: Initial metadata
        """
        self.monitor = monitor
        self.operation_name = operation_name
        self.metadata = metadata or {}
        self.operation_id = None
        self.success = True

    def __enter__(self):
        """Start tracking"""
        self.operation_id = self.monitor.start_operation(
            self.operation_name, metadata=self.metadata
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End tracking"""
        if exc_type is not None:
            self.success = False

        if self.operation_id is not None:
            self.monitor.end_operation(
                self.operation_id, success=self.success, metadata=self.metadata
            )

        return False  # Don't suppress exceptions

    def add_metadata(self, metadata: Dict[str, Any]) -> None:
        """Add metadata to the current operation"""
        self.metadata.update(metadata)

    def mark_failed(self) -> None:
        """Mark the operation as failed"""
        self.success = False


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def monitor_performance(operation_name: Optional[str] = None):
    """
    Decorator to monitor function performance using global monitor

    Args:
        operation_name: Name for the operation (defaults to function name)
    """
    return get_performance_monitor().monitor(operation_name)


if __name__ == "__main__":
    print("Performance Monitor Module")
    print("=" * 50)
    print("✓ Module loaded successfully")
    print("\nFeatures:")
    print("  - Operation timing and profiling")
    print("  - Performance metrics aggregation")
    print("  - Slow operation detection")
    print("  - Decorator and context manager support")
