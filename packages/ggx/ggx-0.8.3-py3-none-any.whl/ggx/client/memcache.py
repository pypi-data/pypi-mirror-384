import asyncio
import time
import random
from typing import Any, Optional, Dict, Callable
from loguru import logger


class MemCache:
    """
    A high-performance caching system with TTL support, optimized for short and medium-lived data.
    
    Features:
    - TTL (Time-To-Live) support with millisecond precision
    - Lazy expiration checking on read operations
    - Background task-based expiration for accuracy
    - Key-level locking for thread-safe operations
    - Jitter support to distribute expiration spikes
    - Chainable expiration scheduling
    
    Optimized for:
    - Short TTLs (seconds to minutes): session data, rate limits, real-time state
    - Medium TTLs (minutes to hours): user data, inventories, game state
    
    Not recommended for:
    - Very long TTLs (days+): use simpler caching solutions
    - Extremely high frequency updates: consider in-memory databases
    """

    def __init__(
        self,
        default_ttl: float = 300.0,
        on_expire: Optional[Callable[[Any, Any], Any]] = None
    ):
        """
        Initialize the cache system.
        
        Args:
            default_ttl: Default time-to-live in seconds for entries without explicit TTL
            on_expire: Optional callback function called when an entry expires.
                     Signature: fn(key, value) -> None or awaitable
        """
        self._default_ttl = default_ttl
        self._on_expire = on_expire or (lambda k, v: None)
        
        # Core storage
        self._data: Dict[Any, Any] = {}          # Key-value storage
        self._expires: Dict[Any, float] = {}     # Expiration timestamps
        self._tasks: Dict[Any, asyncio.Task] = {}  # Background expiration tasks
        self._locks: Dict[Any, asyncio.Lock] = {}  # Per-key operation locks

    # === Core API ===

    def set(self, key: Any, value: Any) -> None:
        """
        Store a value permanently (without TTL).
        
        Args:
            key: Cache key identifier
            value: Data to be stored
        """
        self._data[key] = value
        self._expires.pop(key, None)
        self._cancel_task(key)

    async def set_with_ttl(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """
        Store a value with time-to-live expiration.
        
        Args:
            key: Cache key identifier
            value: Data to be stored
            ttl: Time-to-live in seconds. Uses default_ttl if None.
        """
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            await self._set_with_ttl_unlocked(key, value, ttl)

    async def _set_with_ttl_unlocked(self, key: Any, value: Any, ttl: Optional[float]) -> None:
        """Internal method to set TTL value without lock acquisition."""
        self._cancel_task(key)
        
        self._data[key] = value
        
        actual_ttl = ttl if ttl is not None else self._default_ttl
        expire_time = time.time() + actual_ttl
        self._expires[key] = expire_time
        
        # Start background expiration task
        self._tasks[key] = asyncio.create_task(
            self._expire_after_delay(key, actual_ttl)
        )

    async def _expire_after_delay(self, key: Any, delay: float) -> None:
        """
        Background task that waits for expiration and triggers cleanup.
        
        Args:
            key: Key to expire
            delay: Delay in seconds before expiration
        """
        try:
            await asyncio.sleep(delay)
            await self._expire_key(key)
        except asyncio.CancelledError:
            # Normal cancellation during key update or deletion
            pass

    def get(self, key: Any, default: Any = None) -> Any:
        """
        Retrieve a value from cache with lazy expiration check.
        
        Args:
            key: Cache key to retrieve
            default: Value to return if key doesn't exist or has expired
            
        Returns:
            Cached value or default if not found/expired
        """
        if key not in self._data:
            return default
            
        expire_time = self._expires.get(key)
        if expire_time and time.time() > expire_time:
            self._expire_key_sync(key)
            return default
            
        return self._data[key]

    def delete(self, key: Any) -> bool:
        """
        Remove a key from cache immediately.
        
        Args:
            key: Key to remove
            
        Returns:
            True if key was found and removed, False otherwise
        """
        if key in self._data:
            self._cancel_task(key)
            self._data.pop(key, None)
            self._expires.pop(key, None)
            return True
        return False

    # === Advanced Scheduling API ===

    async def set_in_timeline(self, key: Any, value: Any, delay: float, jitter: float = 0.0) -> None:
        """
        Schedule expiration relative to current time with random jitter.
        
        Useful for distributing expiration spikes across time.
        
        Args:
            key: Cache key identifier
            value: Data to be stored
            delay: Base delay in seconds until expiration
            jitter: Maximum random jitter in seconds (±value) to add to delay
        """
        jitter_val = random.uniform(-jitter, jitter) if jitter > 0 else 0.0
        actual_delay = max(0.0, delay + jitter_val)
        await self.set_with_ttl(key, value, actual_delay)

    async def chain_schedule(self, key: Any, value: Any, interval: float, jitter: float = 0.0) -> None:
        """
        Schedule expiration after the last scheduled expiration time.
        
        Ideal for creating expiration chains or ensuring minimum intervals
        between operations.
        
        Args:
            key: Cache key identifier
            value: Data to be stored
            interval: Time interval in seconds to add after last expiration
            jitter: Maximum random jitter in seconds (±value) to add to interval
        """
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            now = time.time()
            expiry = self._expires.get(key, now)
            if expiry < now:
                delay = 0.0
            else:
                delay = expiry - now
                
            jitter_val = random.uniform(-jitter, jitter) if jitter > 0 else 0.0
            delay += max(0.0, interval + jitter_val)
            
            await self._set_with_ttl_unlocked(key, value, delay)

    async def get_or_set(self, key: Any, value_coroutine, ttl: Optional[float] = None) -> Any:
        """
        Atomic get-or-set operation. Retrieves existing value or sets new value from coroutine.
        
        Args:
            key: Cache key identifier
            value_coroutine: Async function that returns value if key doesn't exist
            ttl: Optional TTL for the new value
            
        Returns:
            Existing cached value or result of value_coroutine
        """
        # Quick check without lock first
        existing = self.get(key)
        if existing is not None:
            return existing
            
        # Acquire lock and double-check
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            # Double-check after acquiring lock
            existing = self.get(key)
            if existing is not None:
                return existing
                
            # Generate and store new value
            new_value = await value_coroutine
            await self._set_with_ttl_unlocked(key, new_value, ttl)
            return new_value

    # === Internal Implementation ===

    def _expire_key_sync(self, key: Any) -> None:
        """
        Synchronously expire a key and trigger callback in background.
        
        Used during get() operations when expired key is detected.
        """
        if key not in self._data:
            return
            
        value = self._data.pop(key)
        self._expires.pop(key, None)
        self._tasks.pop(key, None)
        
        # Execute callback in background without blocking
        asyncio.create_task(self._safe_callback(key, value))

    async def _expire_key(self, key: Any) -> None:
        """
        Asynchronously expire a key and await callback completion.
        
        Used by background expiration tasks.
        """
        if key not in self._data:
            return
            
        value = self._data.pop(key)
        self._expires.pop(key, None)
        self._tasks.pop(key, None)
        
        await self._safe_callback(key, value)

    async def _safe_callback(self, key: Any, value: Any) -> None:
        """
        Safely execute expiration callback handling both sync and async callbacks.
        """
        try:
            result = self._on_expire(key, value)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error(f"Expiration callback error for key '{key}': {e}")

    def _cancel_task(self, key: Any) -> None:
        """Cancel background expiration task for a key."""
        task = self._tasks.pop(key, None)
        if task:
            task.cancel()

    # === Cache Management ===

    def clear(self) -> None:
        """
        Clear all cache entries and cancel all background tasks.
        
        Note: Expiration callbacks will NOT be executed for cleared entries.
        """
        for task in self._tasks.values():
            task.cancel()
        self._data.clear()
        self._tasks.clear()
        self._expires.clear()
        self._locks.clear()

    async def aclose(self) -> None:
        """
        Gracefully shutdown the cache, awaiting completion of expiration callbacks.
        
        This should be called during application shutdown to ensure
        all expiration callbacks complete properly.
        """
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self.clear()

    # === Utility Methods ===

    def exists(self, key: Any) -> bool:
        """
        Check if a key exists and hasn't expired.
        
        Args:
            key: Key to check
            
        Returns:
            True if key exists and is not expired, False otherwise
        """
        if key not in self._data:
            return False
        expire_time = self._expires.get(key)
        if expire_time and time.time() > expire_time:
            return False
        return True

    def get_remaining_ttl(self, key: Any) -> Optional[float]:
        """
        Get remaining time-to-live for a key.
        
        Args:
            key: Key to check
            
        Returns:
            Remaining TTL in seconds, None if key doesn't exist or has no TTL
        """
        if key not in self._expires:
            return None
            
        remaining = self._expires[key] - time.time()
        return max(0.0, remaining) if remaining > 0 else None

    def keys(self) -> list:
        """Return list of all active (non-expired) keys."""
        now = time.time()
        return [
            key for key in self._data 
            if key not in self._expires or self._expires[key] > now
        ]

    def __contains__(self, key: Any) -> bool:
        """Support for 'in' operator. Checks if key exists and is not expired."""
        return self.exists(key)

    def __len__(self) -> int:
        """Return number of active (non-expired) entries."""
        return len(self.keys())

