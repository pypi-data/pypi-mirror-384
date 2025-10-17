import asyncio
import time
import random
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass, field
from heapq import heappush, heappop
from loguru import logger

@dataclass(frozen=True, order=True)
class _PlannedJob:
    run_at_monotonic: float
    key: str = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)

class Planner:
    """
    Optimized Planner with heap-based scheduling and performance improvements
    """
    def __init__(
        self,
        on_expire,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        process_interval: float = 0.1,  # Reduced for better responsiveness
        max_proc: int = 10000,  # Increased capacity
        batch_size: int = 10  # Process multiple jobs at once
    ):
        
        if not asyncio.iscoroutinefunction(on_expire):
            raise TypeError("on_expire should be coroutine function")
        
        self.on_expire = on_expire
        self.loop = loop or asyncio.get_event_loop()
        self._job_queue: asyncio.Queue[_PlannedJob] = asyncio.Queue(maxsize=max_proc)
        self._scheduled_jobs: Set[str] = set()  # Fast lookup for existing jobs
        self._timer_heap = []  # Min-heap for efficient timer management
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._shutdown = False
        self.process_interval = float(process_interval)
        self.batch_size = batch_size
        self._last_processed = time.monotonic()

    @property
    def running(self) -> bool:
        return self._running and not self._shutdown

    @property
    def stopped(self) -> bool:
        return self._shutdown

    @property
    def pending_count(self) -> int:
        """Get number of pending jobs"""
        return len(self._scheduled_jobs)

    async def start(self):
        """Start the planner with optimized initialization"""
        if self._running:
            return
        
        self._running = True
        self._shutdown = False
        
        # Start multiple workers for parallel processing
        self._worker_task = asyncio.create_task(
            self._worker_loop(), 
            name="planner-worker-main"
        )
        
        # Start timer manager
        asyncio.create_task(
            self._timer_manager_loop(),
            name="planner-timer-manager"
        )

    async def close(self):
        """Optimized shutdown with proper cleanup"""
        if self._shutdown:
            return
            
        self._shutdown = True
        self._running = False
        
        # Cancel all pending timers
        while self._timer_heap:
            _, timer_task = heappop(self._timer_heap)
            if not timer_task.done():
                timer_task.cancel()
        
        # Clear collections
        self._scheduled_jobs.clear()
        
        # Send sentinel to stop worker
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
        """Fast reset - clear all pending jobs"""
        # Cancel all timers
        while self._timer_heap:
            _, timer_task = heappop(self._timer_heap)
            if not timer_task.done():
                timer_task.cancel()
        
        # Clear job queue efficiently
        while not self._job_queue.empty():
            try:
                self._job_queue.get_nowait()
                self._job_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        self._scheduled_jobs.clear()

    async def full_reset(self):
        """Complete reset with restart"""
        await self.close()
        await asyncio.sleep(0.1)  # Brief pause
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
        """Optimized scheduling with heap-based timers"""
        
        if self._shutdown:
            return False

        # Fast check if job already exists
        if key in self._scheduled_jobs:
            if not replace_existing:
                return False
            # Remove existing job - we'll replace it
            self._scheduled_jobs.discard(key)

        now = time.monotonic()
        j = random.uniform(-jitter, jitter) if jitter > 0 else 0.0
        run_at = now + max(0.0, float(interval) + j)
        
        # Add to scheduled jobs set
        self._scheduled_jobs.add(key)
        
        # Create timer task
        timer_task = asyncio.create_task(
            self._create_timer(key, payload, run_at),
            name=f"planner-timer-{key}"
        )
        
        # Add to min-heap for efficient management
        heappush(self._timer_heap, (run_at, timer_task))
        
        return True

    async def schedule_at_time(
        self,
        key: str,
        payload: Dict[str, Any],
        run_at: float,
        replace_existing: bool = True
    ) -> bool:
        """Schedule job at specific monotonic time"""
        return await self.schedule_after_last(
            key, payload, interval=run_at - time.monotonic(), 
            jitter=0.0, replace_existing=replace_existing
        )

    async def _create_timer(self, key: str, payload: Dict[str, Any], run_at: float):
        """Create optimized timer task"""
        try:
            delay = run_at - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            
            if self._shutdown:
                return
                
            # Remove from scheduled jobs when timer expires
            self._scheduled_jobs.discard(key)
            
            # Add to job queue for processing
            job = _PlannedJob(run_at, key, payload)
            await self._job_queue.put(job)
            
        except asyncio.CancelledError:
            # Timer was cancelled - remove from scheduled jobs
            self._scheduled_jobs.discard(key)
            raise
        except Exception as e:
            logger.error(f"Timer error for job {key}: {e}")
            self._scheduled_jobs.discard(key)

    async def _timer_manager_loop(self):
        """Manage timer heap and clean up completed timers"""
        while self.running:
            try:
                await asyncio.sleep(5.0)  # Check every 5 seconds
                
                # Clean up completed timers from heap
                current_time = time.monotonic()
                temp_heap = []
                
                while self._timer_heap:
                    run_at, timer_task = heappop(self._timer_heap)
                    
                    if timer_task.done():
                        continue  # Discard completed tasks
                    
                    # Keep tasks that are still relevant
                    if run_at > current_time + 3600:  # Too far in future
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
        """Optimized worker with batch processing"""
        batch = []
        last_batch_time = time.monotonic()
        
        while self.running:
            try:
                # Get job with timeout for batching
                try:
                    job = await asyncio.wait_for(
                        self._job_queue.get(), 
                        timeout=0.1  # Short timeout for batching
                    )
                except asyncio.TimeoutError:
                    # Process batch if we have jobs and enough time passed
                    if batch and (time.monotonic() - last_batch_time) >= self.process_interval:
                        await self._process_batch(batch)
                        batch = []
                        last_batch_time = time.monotonic()
                    continue

                if job.key == "__SENTINEL__":
                    break

                batch.append(job)
                
                # Process batch when full or enough time passed
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

        # Process any remaining jobs
        if batch:
            await self._process_batch(batch)

    async def _process_batch(self, batch: list):
        """Process multiple jobs in parallel"""
        if not batch:
            return
            
        tasks = []
        for job in batch:
            task = asyncio.create_task(
                self._process_single_job(job),
                name=f"planner-process-{job.key}"
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
        
        # Mark all jobs as done in queue
        for _ in batch:
            self._job_queue.task_done()

    async def _process_single_job(self, job: _PlannedJob):
        """Process a single job with error handling"""
        try:
            await self.on_expire(job.key, job.payload)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Job {job.key} processing error: {e}")

    def cancel_job(self, key: str) -> bool:
        """Cancel a specific job"""
        if key not in self._scheduled_jobs:
            return False
            
        self._scheduled_jobs.discard(key)
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get planner statistics"""
        return {
            "running": self.running,
            "pending_jobs": len(self._scheduled_jobs),
            "scheduled_timers": len(self._timer_heap),
            "queue_size": self._job_queue.qsize(),
            "process_interval": self.process_interval
        }