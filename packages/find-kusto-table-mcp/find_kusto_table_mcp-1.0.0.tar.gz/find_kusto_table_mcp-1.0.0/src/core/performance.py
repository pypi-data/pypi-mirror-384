"""
Performance monitoring and metrics for the Kusto MCP server.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque

from .logging_config import get_logger, log_performance

logger = get_logger("performance")


@dataclass
class OperationMetrics:
    """Metrics for a specific operation"""
    name: str
    total_calls: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    error_count: int = 0
    recent_durations: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def avg_duration_ms(self) -> float:
        """Average duration in milliseconds"""
        return self.total_duration_ms / self.total_calls if self.total_calls > 0 else 0.0
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        return ((self.total_calls - self.error_count) / self.total_calls * 100) if self.total_calls > 0 else 0.0
    
    def add_measurement(self, duration_ms: float, success: bool = True):
        """Add a new measurement"""
        self.total_calls += 1
        self.total_duration_ms += duration_ms
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)
        self.recent_durations.append(duration_ms)
        
        if not success:
            self.error_count += 1
    
    def get_percentile(self, percentile: float) -> float:
        """Get percentile from recent measurements"""
        if not self.recent_durations:
            return 0.0
        
        sorted_durations = sorted(self.recent_durations)
        index = int(len(sorted_durations) * percentile / 100)
        return sorted_durations[min(index, len(sorted_durations) - 1)]


class PerformanceMonitor:
    """Global performance monitoring"""
    
    def __init__(self):
        self.metrics: Dict[str, OperationMetrics] = defaultdict(lambda: OperationMetrics(""))
        self.start_time = datetime.now()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    @contextmanager
    def measure_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager to measure operation performance"""
        start_time = time.perf_counter()
        success = True
        error = None
        
        try:
            yield
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Update metrics
            if operation_name not in self.metrics:
                self.metrics[operation_name] = OperationMetrics(operation_name)
            
            self.metrics[operation_name].add_measurement(duration_ms, success)
            
            # Log performance
            log_metadata = metadata or {}
            if error:
                log_metadata['error'] = error
            
            log_performance(operation_name, duration_ms, log_metadata)
            
            # Log slow operations
            if duration_ms > 1000:  # Over 1 second
                logger.warning(f"Slow operation: {operation_name} took {duration_ms:.2f}ms")
    
    def record_cache_hit(self, cache_type: str):
        """Record a cache hit"""
        self.cache_stats['hits'] += 1
        logger.debug(f"Cache hit: {cache_type}")
    
    def record_cache_miss(self, cache_type: str):
        """Record a cache miss"""
        self.cache_stats['misses'] += 1
        logger.debug(f"Cache miss: {cache_type}")
    
    def record_cache_eviction(self, cache_type: str):
        """Record a cache eviction"""
        self.cache_stats['evictions'] += 1
        logger.debug(f"Cache eviction: {cache_type}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        uptime = datetime.now() - self.start_time
        
        # Calculate cache hit rate
        total_cache_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        cache_hit_rate = (self.cache_stats['hits'] / total_cache_requests * 100) if total_cache_requests > 0 else 0.0
        
        # Get top operations by call count
        top_operations = sorted(
            [(name, metrics) for name, metrics in self.metrics.items()],
            key=lambda x: x[1].total_calls,
            reverse=True
        )[:10]
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'total_operations': sum(m.total_calls for m in self.metrics.values()),
            'total_errors': sum(m.error_count for m in self.metrics.values()),
            'cache_stats': {
                **self.cache_stats,
                'hit_rate_percent': round(cache_hit_rate, 2)
            },
            'top_operations': [
                {
                    'name': name,
                    'calls': metrics.total_calls,
                    'avg_duration_ms': round(metrics.avg_duration_ms, 2),
                    'success_rate_percent': round(metrics.success_rate, 2),
                    'p95_duration_ms': round(metrics.get_percentile(95), 2)
                }
                for name, metrics in top_operations
            ]
        }
    
    def get_operation_stats(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed stats for a specific operation"""
        if operation_name not in self.metrics:
            return None
        
        metrics = self.metrics[operation_name]
        
        return {
            'name': operation_name,
            'total_calls': metrics.total_calls,
            'total_duration_ms': round(metrics.total_duration_ms, 2),
            'avg_duration_ms': round(metrics.avg_duration_ms, 2),
            'min_duration_ms': round(metrics.min_duration_ms, 2),
            'max_duration_ms': round(metrics.max_duration_ms, 2),
            'error_count': metrics.error_count,
            'success_rate_percent': round(metrics.success_rate, 2),
            'percentiles': {
                'p50': round(metrics.get_percentile(50), 2),
                'p90': round(metrics.get_percentile(90), 2),
                'p95': round(metrics.get_percentile(95), 2),
                'p99': round(metrics.get_percentile(99), 2)
            }
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.start_time = datetime.now()
        self.cache_stats = {'hits': 0, 'misses': 0, 'evictions': 0}
        logger.info("Performance metrics reset")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def measure_operation(operation_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator/context manager for measuring operation performance"""
    return performance_monitor.measure_operation(operation_name, metadata)


def record_cache_hit(cache_type: str):
    """Record a cache hit"""
    performance_monitor.record_cache_hit(cache_type)


def record_cache_miss(cache_type: str):
    """Record a cache miss"""
    performance_monitor.record_cache_miss(cache_type)


def record_cache_eviction(cache_type: str):
    """Record a cache eviction"""
    performance_monitor.record_cache_eviction(cache_type)


def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary"""
    return performance_monitor.get_summary()


def get_operation_stats(operation_name: str) -> Optional[Dict[str, Any]]:
    """Get stats for a specific operation"""
    return performance_monitor.get_operation_stats(operation_name)