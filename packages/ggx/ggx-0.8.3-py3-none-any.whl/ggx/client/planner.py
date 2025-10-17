import asyncio
import time
import random
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass, field
from heapq import heappush, heappop
from loguru import logger

@dataclass(frozen=True, order=True)
class _PlannedJob:
    """
    Internal data class representing a scheduled job.
    
    Attributes:
        run_at_monotonic: Monotonic time when job should run
        key: Unique identifier for the job
        payload: Data associated with the job
    """
    run_at_monotonic: float
    key: str = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)

class Planner:
    """
    Optimized asynchronous job scheduler with heap-based scheduling.
    
    Features:
    - Heap-based timer management for efficient scheduling
    - Batch processing for improved performance
    - Parallel job execution
    - Automatic cleanup of completed timers
    - Graceful shutdown handling
    
    Args:
        on_expire: Coroutine function called when job expires
        loop: Event loop to use (default: current event loop)
        process_interval: Interval between batch processing in seconds
        max_proc: Maximum capacity of job queue
        batch_size: Number of jobs to process in a single batch
    """
    def __init__(
        self,
        on_expire,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        process_interval: float = 0.1,
        max_proc: int = 10000,
        batch_size: int = 10
    ):
        """
        Initialize the Planner with optimized settings.
        
        Raises:
            TypeError: If on_expire is not a coroutine function
        """
        if not asyncio.iscoroutinefunction(on_expire):
            raise TypeError("on_expire should be coroutine function")
        
        self.on_expire = on_expire
        self.loop = loop or asyncio.get_event_loop()
        self._job_queue: asyncio.Queue[_PlannedJob] = asyncio.Queue(maxsize=max_proc)
        self._scheduled_jobs: Set[str] = set()
        self._timer_heap = []
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._shutdown = False
        self.process_interval = float(process_interval)
        self.batch_size = batch_size
        self._last_processed = time.monotonic()

    @property
    def running(self) -> bool:
        """Check if planner is currently running and not shutting down."""
        return self._running and not self._shutdown

    @property
    def stopped(self) -> bool:
        """Check if planner has been shut down."""
        return self._shutdown

    @property
    def pending_count(self) -> int:
        """Get number of currently pending jobs."""
        return len(self._scheduled_jobs)

    async def start(self):
        """
        Start the planner with optimized initialization.
        
        Starts both the worker loop and timer manager loop for
        parallel job processing and timer management.
        """
        if self._running:
            return
        
        self._running = True
        self._shutdown = False
        
        self._worker_task = asyncio.create_task(
            self._worker_loop(), 
            name="planner-worker-main"
        )
        
        asyncio.create_task(
            self._timer_manager_loop(),
            name="planner-timer-manager"
        )

    async def close(self):
        """
        Optimized shutdown with proper cleanup.
        
        Cancels all pending timers, clears job collections, and
        stops worker tasks gracefully.
        """
        if self._shutdown:
            return
            
        self._shutdown = True
        self._running = False
        
        # Cancel all pending timers
        while self._timer_heap:
            _, timer_task = heappop(self._timer_heap)
            if not timer_task.done():
                timer_task.cancel()
        
        self._scheduled_jobs.clear()
        
        if self._worker_task and not self._worker_task.done():
            await self._job_queue.put(_PlannedJob(
                time.monotonic(), "__SENTINEL__", {}
            ))
            try:
                await asyncio.wait_for(self._worker_task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._worker_task.cancel()
        
        self._worker_task = None

    async def reset(self):
        """
        Fast reset - clear all pending jobs without restarting.
        
        Cancels all timers and clears the job queue while maintaining
        the running state of the planner.
        """
        while self._timer_heap:
            _, timer_task = heappop(self._timer_heap)
            if not timer_task.done():
                timer_task.cancel()
        
        while not self._job_queue.empty():
            try:
                self._job_queue.get_nowait()
                self._job_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        self._scheduled_jobs.clear()

    async def full_reset(self):
        """
        Complete reset with restart.
        
        Performs full shutdown and restart of the planner for
        complete state cleanup.
        """
        await self.close()
        await asyncio.sleep(0.1)
        await self.start()

    async def schedule_after_last(
        self, 
        key: str, 
        payload: Dict[str, Any], 
        *, 
        interval: float = 1.0, 
        jitter: float = 0.0,
        replace_existing: bool = True
    ) -> bool:
        """
        Schedule a job to run after a specified interval.
        
        Args:
            key: Unique job identifier
            payload: Job data dictionary
            interval: Time interval in seconds before job execution
            jitter: Random time variation (+/-) to add to interval
            replace_existing: Whether to replace existing job with same key
            
        Returns:
            bool: True if job was scheduled successfully, False otherwise
        """
        if self._shutdown:
            return False

        if key in self._scheduled_jobs:
            if not replace_existing:
                return False
            self._scheduled_jobs.discard(key)

        now = time.monotonic()
        j = random.uniform(-jitter, jitter) if jitter > 0 else 0.0
        run_at = now + max(0.0, float(interval) + j)
        
        self._scheduled_jobs.add(key)
        
        timer_task = asyncio.create_task(
            self._create_timer(key, payload, run_at),
            name=f"planner-timer-{key}"
        )
        
        heappush(self._timer_heap, (run_at, timer_task))
        
        return True

    async def schedule_at_time(
        self,
        key: str,
        payload: Dict[str, Any],
        run_at: float,
        replace_existing: bool = True
    ) -> bool:
        """
        Schedule job at specific monotonic time.
        
        Args:
            key: Unique job identifier
            payload: Job data dictionary
            run_at: Absolute monotonic time when job should run
            replace_existing: Whether to replace existing job with same key
            
        Returns:
            bool: True if job was scheduled successfully, False otherwise
        """
        return await self.schedule_after_last(
            key, payload, interval=run_at - time.monotonic(), 
            jitter=0.0, replace_existing=replace_existing
        )

    async def _create_timer(self, key: str, payload: Dict[str, Any], run_at: float):
        """
        Create optimized timer task for job execution.
        
        Internal method that waits until scheduled time, then
        adds job to processing queue.
        
        Args:
            key: Job identifier
            payload: Job data
            run_at: Scheduled execution time
        """
        try:
            delay = run_at - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            
            if self._shutdown:
                return
                
            self._scheduled_jobs.discard(key)
            
            job = _PlannedJob(run_at, key, payload)
            await self._job_queue.put(job)
            
        except asyncio.CancelledError:
            self._scheduled_jobs.discard(key)
            raise
        except Exception as e:
            logger.error(f"Timer error for job {key}: {e}")
            self._scheduled_jobs.discard(key)

    async def _timer_manager_loop(self):
        """
        Manage timer heap and clean up completed timers.
        
        Background task that periodically cleans up the timer heap
        by removing completed tasks and canceling distant future timers.
        """
        while self.running:
            try:
                await asyncio.sleep(5.0)
                
                current_time = time.monotonic()
                temp_heap = []
                
                while self._timer_heap:
                    run_at, timer_task = heappop(self._timer_heap)
                    
                    if timer_task.done():
                        continue
                    
                    if run_at > current_time + 3600:
                        timer_task.cancel()
                        continue
                    
                    heappush(temp_heap, (run_at, timer_task))
                
                self._timer_heap = temp_heap
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Timer manager error: {e}")
                await asyncio.sleep(1.0)

    async def _worker_loop(self):
        """
        Optimized worker with batch processing.
        
        Main worker loop that processes jobs in batches for
        improved performance and throughput.
        """
        batch = []
        last_batch_time = time.monotonic()
        
        while self.running:
            try:
                try:
                    job = await asyncio.wait_for(
                        self._job_queue.get(), 
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    if batch and (time.monotonic() - last_batch_time) >= self.process_interval:
                        await self._process_batch(batch)
                        batch = []
                        last_batch_time = time.monotonic()
                    continue

                if job.key == "__SENTINEL__":
                    break

                batch.append(job)
                
                current_time = time.monotonic()
                if (len(batch) >= self.batch_size or 
                    (batch and (current_time - last_batch_time) >= self.process_interval)):
                    await self._process_batch(batch)
                    batch = []
                    last_batch_time = current_time
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(0.1)

        if batch:
            await self._process_batch(batch)

    async def _process_batch(self, batch: list):
        """
        Process multiple jobs in parallel.
        
        Args:
            batch: List of _PlannedJob objects to process
        """
        if not batch:
            return
            
        tasks = []
        for job in batch:
            task = asyncio.create_task(
                self._process_single_job(job),
                name=f"planner-process-{job.key}"
            )
            tasks.append(task)
        
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
        
        for _ in batch:
            self._job_queue.task_done()

    async def _process_single_job(self, job: _PlannedJob):
        """
        Process a single job with error handling.
        
        Args:
            job: _PlannedJob object to process
        """
        try:
            await self.on_expire(job.key, job.payload)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Job {job.key} processing error: {e}")

    def cancel_job(self, key: str) -> bool:
        """
        Cancel a specific job by key.
        
        Args:
            key: Job identifier to cancel
            
        Returns:
            bool: True if job was found and cancelled, False otherwise
        """
        if key not in self._scheduled_jobs:
            return False
            
        self._scheduled_jobs.discard(key)
        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get planner statistics and current state.
        
        Returns:
            Dict with planner statistics including:
            - running: Whether planner is running
            - pending_jobs: Number of scheduled jobs
            - scheduled_timers: Number of active timers
            - queue_size: Current job queue size
            - process_interval: Current processing interval
        """
        return {
            "running": self.running,
            "pending_jobs": len(self._scheduled_jobs),
            "scheduled_timers": len(self._timer_heap),
            "queue_size": self._job_queue.qsize(),
            "process_interval": self.process_interval
        }