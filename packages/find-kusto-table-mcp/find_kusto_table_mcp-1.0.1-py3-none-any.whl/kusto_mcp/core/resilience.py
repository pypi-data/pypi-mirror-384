"""
Resilience and Error Recovery System

Provides circuit breakers, retry logic with exponential backoff,
and graceful degradation patterns for reliable operations.
"""

import asyncio
import time
import functools
from enum import Enum
from typing import Callable, Any, Optional, Type, Tuple, List, Dict
from datetime import datetime, timedelta
from collections import defaultdict, deque

from .logging_config import get_logger
from .performance import measure_operation
from .exceptions import KustoMCPError, ValidationError

logger = get_logger("resilience")


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking calls (too many failures)
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    
    Prevents cascading failures by:
    - Opening circuit after threshold failures
    - Blocking calls while open (fail fast)
    - Half-opening to test recovery
    - Auto-closing on success
    
    Usage:
        breaker = CircuitBreaker(name="kusto_query", failure_threshold=5)
        
        @breaker.protect
        async def risky_operation():
            # ... potentially failing operation
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        recovery_timeout: int = 30,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # Time to wait before trying again
        self.recovery_timeout = recovery_timeout  # Time in half-open state
        self.expected_exceptions = expected_exceptions
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: Optional[datetime] = None
        
        self.logger = get_logger(f"circuit_breaker.{name}")
    
    def protect(self, func: Callable) -> Callable:
        """Decorator to protect a function with circuit breaker"""
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise KustoMCPError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Service unavailable. Will retry after {self.timeout}s."
                    )
            
            try:
                # Execute the function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Record success
                self._on_success()
                
                return result
                
            except self.expected_exceptions as e:
                # Record failure
                self._on_failure(e)
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout
    
    def _transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN"""
        self.logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.now()
        self.success_count = 0
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:  # Need 2 successes to close
                self._transition_to_closed()
        
        # Reset failure count on success
        self.failure_count = 0
    
    def _on_failure(self, exception: Exception):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        self.logger.warning(
            f"Circuit breaker '{self.name}' failure {self.failure_count}/{self.failure_threshold}: {exception}"
        )
        
        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state immediately opens circuit
            self._transition_to_open()
        elif self.failure_count >= self.failure_threshold:
            # Too many failures, open circuit
            self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.logger.error(
            f"Circuit breaker '{self.name}' OPENED after {self.failure_count} failures"
        )
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.logger.info(f"Circuit breaker '{self.name}' CLOSED - service recovered")
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.now()
        self.failure_count = 0
        self.success_count = 0
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.logger.info(f"Circuit breaker '{self.name}' manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat() if self.last_state_change else None
        }


class RetryStrategy:
    """
    Retry logic with exponential backoff
    
    Features:
    - Configurable max attempts
    - Exponential backoff with jitter
    - Selective exception handling
    - Retry budget tracking
    
    Usage:
        strategy = RetryStrategy(max_attempts=3, base_delay=1.0)
        
        @strategy.retry
        async def flaky_operation():
            # ... operation that might fail
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        
        self.logger = logger
    
    def retry(self, func: Callable) -> Callable:
        """Decorator to add retry logic to a function"""
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, self.max_attempts + 1):
                try:
                    self.logger.debug(f"Attempt {attempt}/{self.max_attempts} for {func.__name__}")
                    
                    # Execute function
                    result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                    
                    if attempt > 1:
                        self.logger.info(f"Operation {func.__name__} succeeded on attempt {attempt}")
                    
                    return result
                    
                except self.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < self.max_attempts:
                        delay = self._calculate_delay(attempt)
                        self.logger.warning(
                            f"Attempt {attempt} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        self.logger.error(
                            f"All {self.max_attempts} attempts failed for {func.__name__}"
                        )
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff with jitter"""
        delay = min(
            self.base_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter (0-50% of delay)
            import random
            jitter_amount = delay * random.uniform(0, 0.5)
            delay += jitter_amount
        
        return delay


class BulkheadPattern:
    """
    Bulkhead pattern for resource isolation
    
    Limits concurrent operations to prevent resource exhaustion.
    Like bulkheads in ships, isolates failures to prevent cascading.
    
    Usage:
        bulkhead = BulkheadPattern(name="kusto_queries", max_concurrent=10)
        
        @bulkhead.limit
        async def resource_intensive_operation():
            # ... operation that consumes resources
    """
    
    def __init__(
        self,
        name: str,
        max_concurrent: int = 10,
        max_queued: int = 100
    ):
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_queued = max_queued
        
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_count = 0
        self.queued_count = 0
        self.total_accepted = 0
        self.total_rejected = 0
        
        self.logger = get_logger(f"bulkhead.{name}")
    
    def limit(self, func: Callable) -> Callable:
        """Decorator to apply bulkhead limiting"""
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if queue is full
            if self.queued_count >= self.max_queued:
                self.total_rejected += 1
                self.logger.warning(
                    f"Bulkhead '{self.name}' rejected request (queue full: {self.queued_count}/{self.max_queued})"
                )
                raise KustoMCPError(
                    f"Resource limit reached for '{self.name}'. "
                    f"Too many concurrent operations ({self.active_count}/{self.max_concurrent}). "
                    f"Please try again later."
                )
            
            self.queued_count += 1
            
            try:
                async with self.semaphore:
                    self.active_count += 1
                    self.queued_count -= 1
                    self.total_accepted += 1
                    
                    self.logger.debug(
                        f"Bulkhead '{self.name}' executing (active: {self.active_count}/{self.max_concurrent})"
                    )
                    
                    try:
                        result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                        return result
                    finally:
                        self.active_count -= 1
            finally:
                if self.queued_count > 0:
                    self.queued_count -= 1
        
        return wrapper
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get bulkhead metrics"""
        return {
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "active_count": self.active_count,
            "queued_count": self.queued_count,
            "total_accepted": self.total_accepted,
            "total_rejected": self.total_rejected,
            "rejection_rate": (
                self.total_rejected / (self.total_accepted + self.total_rejected)
                if (self.total_accepted + self.total_rejected) > 0
                else 0
            )
        }


class FallbackHandler:
    """
    Fallback handler for graceful degradation
    
    Provides alternative behaviors when primary operations fail.
    
    Usage:
        fallback = FallbackHandler()
        
        @fallback.with_fallback(default_value=[])
        async def risky_query():
            # ... operation that might fail
    """
    
    def __init__(self):
        self.logger = logger
    
    def with_fallback(
        self,
        fallback_func: Optional[Callable] = None,
        default_value: Any = None
    ):
        """
        Decorator to provide fallback behavior
        
        Args:
            fallback_func: Function to call on failure
            default_value: Default value to return on failure
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                except Exception as e:
                    self.logger.warning(
                        f"Primary operation {func.__name__} failed: {e}. "
                        f"Using fallback..."
                    )
                    
                    # Try fallback function
                    if fallback_func:
                        try:
                            return await fallback_func(*args, **kwargs) if asyncio.iscoroutinefunction(fallback_func) else fallback_func(*args, **kwargs)
                        except Exception as fallback_error:
                            self.logger.error(
                                f"Fallback also failed for {func.__name__}: {fallback_error}"
                            )
                    
                    # Return default value
                    if default_value is not None:
                        return default_value
                    
                    # Re-raise if no fallback worked
                    raise
            
            return wrapper
        return decorator


class RateLimiter:
    """
    Token bucket rate limiter
    
    Controls rate of operations using token bucket algorithm.
    
    Usage:
        limiter = RateLimiter(name="api_calls", rate=10, burst=20)
        
        @limiter.limit
        async def api_call():
            # ... rate-limited operation
    """
    
    def __init__(
        self,
        name: str,
        rate: float,  # tokens per second
        burst: int    # max tokens in bucket
    ):
        self.name = name
        self.rate = rate
        self.burst = burst
        
        self.tokens = float(burst)
        self.last_update = time.time()
        
        self.logger = get_logger(f"rate_limiter.{name}")
    
    def limit(self, func: Callable) -> Callable:
        """Decorator to apply rate limiting"""
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Acquire token
            await self._acquire_token()
            
            # Execute function
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        
        return wrapper
    
    async def _acquire_token(self):
        """Acquire a token, waiting if necessary"""
        while True:
            now = time.time()
            elapsed = now - self.last_update
            
            # Refill tokens based on elapsed time
            self.tokens = min(
                self.burst,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return
            
            # Wait for next token
            wait_time = (1.0 - self.tokens) / self.rate
            self.logger.debug(
                f"Rate limiter '{self.name}' waiting {wait_time:.2f}s for token"
            )
            await asyncio.sleep(wait_time)


# ============================================================================
# GLOBAL RESILIENCE PATTERNS
# ============================================================================

# Circuit breakers for different operations
circuit_breakers: Dict[str, CircuitBreaker] = {}

# Bulkheads for resource isolation
bulkheads: Dict[str, BulkheadPattern] = {}

# Rate limiters
rate_limiters: Dict[str, RateLimiter] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: int = 60
) -> CircuitBreaker:
    """Get or create circuit breaker"""
    if name not in circuit_breakers:
        circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            timeout=timeout
        )
    return circuit_breakers[name]


def get_bulkhead(
    name: str,
    max_concurrent: int = 10
) -> BulkheadPattern:
    """Get or create bulkhead"""
    if name not in bulkheads:
        bulkheads[name] = BulkheadPattern(
            name=name,
            max_concurrent=max_concurrent
        )
    return bulkheads[name]


def get_rate_limiter(
    name: str,
    rate: float,
    burst: int
) -> RateLimiter:
    """Get or create rate limiter"""
    if name not in rate_limiters:
        rate_limiters[name] = RateLimiter(
            name=name,
            rate=rate,
            burst=burst
        )
    return rate_limiters[name]


def get_resilience_metrics() -> Dict[str, Any]:
    """Get metrics for all resilience patterns"""
    return {
        "circuit_breakers": {
            name: breaker.get_state()
            for name, breaker in circuit_breakers.items()
        },
        "bulkheads": {
            name: bulkhead.get_metrics()
            for name, bulkhead in bulkheads.items()
        }
    }
