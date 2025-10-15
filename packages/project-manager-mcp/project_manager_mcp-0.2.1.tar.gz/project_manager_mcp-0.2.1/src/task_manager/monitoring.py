"""
Performance Monitoring and Background Tasks

Provides system performance monitoring, metrics collection, and background
maintenance tasks for the Project Manager MCP system. Includes performance
endpoints, memory tracking, and automated lock cleanup.
"""

import asyncio
import psutil
import time
import logging
import os
import signal
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from collections import defaultdict, deque

# Performance monitoring configuration
METRICS_HISTORY_SIZE = 1000  # Keep last 1000 data points for trending
LOCK_CLEANUP_INTERVAL = int(os.getenv("LOCK_CLEANUP_INTERVAL", "300"))  # seconds
# Auto-exit when no WebSocket connections for this many seconds (0 disables)
IDLE_EXIT_SECONDS = int(os.getenv("AUTO_EXIT_ON_IDLE_SECONDS", "20"))
IDLE_CHECK_INTERVAL = 1  # seconds
MEMORY_MONITORING_INTERVAL = 60  # 1 minute for memory tracking

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance measurement with timestamp."""
    timestamp: datetime
    value: float
    operation: str


@dataclass
class SystemMetrics:
    """Current system performance metrics."""
    active_connections: int
    total_tasks: int
    locked_tasks: int
    completed_tasks_today: int
    avg_query_time_ms: float
    avg_broadcast_time_ms: float
    locks_acquired_today: int
    expired_locks_cleaned: int
    lock_conflicts: int
    memory_usage_mb: float
    cpu_usage_percent: float
    last_lock_cleanup: str


class PerformanceMonitor:
    """
    Performance monitoring system for collecting and analyzing system metrics.
    
    Features:
    - Query execution time tracking
    - WebSocket broadcast performance monitoring  
    - Memory usage trending
    - Lock operation statistics
    - Background metric collection
    """
    
    def __init__(self):
        self.query_times: deque = deque(maxlen=METRICS_HISTORY_SIZE)
        self.broadcast_times: deque = deque(maxlen=METRICS_HISTORY_SIZE)
        self.daily_stats = defaultdict(int)
        self.last_cleanup_time: Optional[datetime] = None
        self.start_time = datetime.now(timezone.utc)
        
        # Reset daily stats at midnight
        self._last_reset_date = datetime.now(timezone.utc).date()
    
    def record_query_time(self, operation: str, duration_ms: float):
        """
        Record database query execution time.
        
        Args:
            operation: Description of the database operation
            duration_ms: Query execution time in milliseconds
        """
        metric = PerformanceMetric(
            timestamp=datetime.now(timezone.utc),
            value=duration_ms,
            operation=operation
        )
        self.query_times.append(metric)
        
        # Log slow queries for optimization attention
        if duration_ms > 50:  # Threshold for slow query warning
            logger.warning(f"Slow query detected: {operation} took {duration_ms:.2f}ms")
    
    def record_broadcast_time(self, connection_count: int, duration_ms: float):
        """
        Record WebSocket broadcast performance.
        
        Args:
            connection_count: Number of connections broadcasted to
            duration_ms: Total broadcast duration in milliseconds
        """
        # Normalize by connection count for per-connection latency metric
        per_connection_ms = duration_ms / max(connection_count, 1)
        
        metric = PerformanceMetric(
            timestamp=datetime.now(timezone.utc),
            value=per_connection_ms,
            operation=f"broadcast_to_{connection_count}_connections"
        )
        self.broadcast_times.append(metric)
        
        # Log inefficient broadcasts for optimization
        if per_connection_ms > 20:  # 20ms per connection threshold
            logger.warning(f"Slow broadcast: {per_connection_ms:.2f}ms per connection")
    
    def increment_daily_stat(self, stat_name: str, amount: int = 1):
        """
        Increment daily statistics counter.
        
        Args:
            stat_name: Name of the statistic to increment
            amount: Amount to increment by (default 1)
        """
        self._check_daily_reset()
        self.daily_stats[stat_name] += amount
    
    def _check_daily_reset(self):
        """Reset daily statistics if date has changed."""
        current_date = datetime.now(timezone.utc).date()
        if current_date != self._last_reset_date:
            logger.info("Resetting daily statistics for new day")
            self.daily_stats.clear()
            self._last_reset_date = current_date
    
    def get_average_query_time(self) -> float:
        """Get average query execution time from recent history."""
        if not self.query_times:
            return 0.0
        return sum(m.value for m in self.query_times) / len(self.query_times)
    
    def get_average_broadcast_time(self) -> float:
        """Get average per-connection broadcast time from recent history."""
        if not self.broadcast_times:
            return 0.0
        return sum(m.value for m in self.broadcast_times) / len(self.broadcast_times)
    
    def get_memory_usage_mb(self) -> float:
        """Get current process memory usage in MB."""
        try:
            process = psutil.Process()
            memory_bytes = process.memory_info().rss
            return memory_bytes / (1024 * 1024)  # Convert to MB
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0
    
    def get_cpu_usage_percent(self) -> float:
        """Get current CPU usage percentage."""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception as e:
            logger.warning(f"Failed to get CPU usage: {e}")
            return 0.0
    
    def update_cleanup_time(self):
        """Update the last lock cleanup timestamp."""
        self.last_cleanup_time = datetime.now(timezone.utc)
    
    def get_system_metrics(self, connection_manager, database) -> SystemMetrics:
        """
        Collect comprehensive system performance metrics.
        
        Args:
            connection_manager: WebSocket connection manager instance
            database: TaskDatabase instance
            
        Returns:
            SystemMetrics: Current system performance data
        """
        try:
            # Get basic counts from database
            # ASSUMPTION: These queries should be fast with proper indexing
            all_tasks = database.get_all_tasks()
            total_tasks = len(all_tasks)
            locked_tasks = sum(1 for task in all_tasks if task.get('is_locked', False))
            
            # Calculate today's completed tasks
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_str = today_start.isoformat() + 'Z'
            completed_today = sum(
                1 for task in all_tasks 
                if (task.get('status') == 'completed' and 
                    task.get('updated_at', '') >= today_start_str)
            )
            
            return SystemMetrics(
                active_connections=connection_manager.get_connection_count(),
                total_tasks=total_tasks,
                locked_tasks=locked_tasks,
                completed_tasks_today=completed_today,
                avg_query_time_ms=self.get_average_query_time(),
                avg_broadcast_time_ms=self.get_average_broadcast_time(),
                locks_acquired_today=self.daily_stats.get('locks_acquired', 0),
                expired_locks_cleaned=self.daily_stats.get('locks_cleaned', 0),
                lock_conflicts=self.daily_stats.get('lock_conflicts', 0),
                memory_usage_mb=self.get_memory_usage_mb(),
                cpu_usage_percent=self.get_cpu_usage_percent(),
                last_lock_cleanup=(
                    self.last_cleanup_time.isoformat() + 'Z' 
                    if self.last_cleanup_time else "never"
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return minimal metrics on error
            return SystemMetrics(
                active_connections=0,
                total_tasks=0,
                locked_tasks=0,
                completed_tasks_today=0,
                avg_query_time_ms=0.0,
                avg_broadcast_time_ms=0.0,
                locks_acquired_today=0,
                expired_locks_cleaned=0,
                lock_conflicts=0,
                memory_usage_mb=self.get_memory_usage_mb(),
                cpu_usage_percent=self.get_cpu_usage_percent(),
                last_lock_cleanup="error"
            )


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


class BackgroundTasks:
    """
    Background task management for automated system maintenance.
    
    Handles periodic operations like lock cleanup and performance monitoring
    that run alongside the main FastAPI application.
    """
    
    def __init__(self):
        self.tasks: List[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()
    
    async def start_background_tasks(self, database, connection_manager):
        """
        Start all background maintenance tasks.
        
        Args:
            database: TaskDatabase instance for cleanup operations
            connection_manager: WebSocket manager for monitoring
        """
        logger.info("Starting background tasks...")
        
        # Start lock cleanup task
        cleanup_task = asyncio.create_task(
            self._lock_cleanup_worker(database, connection_manager)
        )
        self.tasks.append(cleanup_task)
        
        # Start memory monitoring task  
        memory_task = asyncio.create_task(
            self._memory_monitoring_worker()
        )
        self.tasks.append(memory_task)

        # Start idle exit watcher if enabled
        if IDLE_EXIT_SECONDS > 0:
            idle_task = asyncio.create_task(
                self._idle_exit_worker(connection_manager)
            )
            self.tasks.append(idle_task)
        
        logger.info(f"Started {len(self.tasks)} background tasks")
    
    async def stop_background_tasks(self):
        """Stop all background tasks gracefully."""
        logger.info("Stopping background tasks...")
        
        # Signal shutdown to all tasks
        self.shutdown_event.set()
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete or timeout
        if self.tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.tasks, return_exceptions=True),
                    timeout=10.0  # 10 second timeout for graceful shutdown
                )
                logger.info("All background tasks stopped")
            except asyncio.TimeoutError:
                logger.warning("Background task shutdown timeout")
    
    async def _lock_cleanup_worker(self, database, connection_manager):
        """
        Background worker for automated lock cleanup.
        
        Runs every 5 minutes to clean up expired task locks and maintain
        system performance under high concurrency.
        """
        logger.info("Lock cleanup worker started")
        
        while not self.shutdown_event.is_set():
            try:
                start_time = time.time()
                
                # Clean up expired locks and broadcast unlock events
                expired_ids = []
                try:
                    expired_ids = database.cleanup_expired_locks_with_ids()
                except Exception:
                    # Fallback to count-only cleanup if detailed method unavailable
                    count_only = database.cleanup_expired_locks()
                    expired_ids = []
                    if count_only:
                        logger.info(f"Cleaned up {count_only} expired locks (ids unavailable)")
                        performance_monitor.increment_daily_stat('locks_cleaned', count_only)
                
                if expired_ids:
                    logger.info(f"Cleaned up {len(expired_ids)} expired locks: {expired_ids}")
                    performance_monitor.increment_daily_stat('locks_cleaned', len(expired_ids))
                    # Broadcast unlock events for each task
                    for task_id in expired_ids:
                        try:
                            await connection_manager.optimized_broadcast({
                                "type": "task.unlocked",
                                "task_id": task_id,
                                "agent_id": None,
                                "reason": "lock_expired"
                            })
                        except Exception as be:
                            logger.warning(f"Failed to broadcast unlock for task {task_id}: {be}")
                
                # Update monitoring timestamp
                performance_monitor.update_cleanup_time()
                
                # Record cleanup operation performance
                cleanup_duration = (time.time() - start_time) * 1000
                performance_monitor.record_query_time('lock_cleanup', cleanup_duration)
                
            except Exception as e:
                logger.error(f"Lock cleanup worker error: {e}")
            
            # Wait for next cleanup cycle or shutdown
            try:
                await asyncio.wait_for(
                    self.shutdown_event.wait(),
                    timeout=LOCK_CLEANUP_INTERVAL
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                continue  # Continue with next cleanup cycle
    
    async def _memory_monitoring_worker(self):
        """
        Background worker for memory usage monitoring.
        
        Tracks memory trends and logs warnings for potential memory leaks.
        """
        logger.info("Memory monitoring worker started")
        memory_history = deque(maxlen=60)  # Keep 1 hour of data (1 minute intervals)
        
        while not self.shutdown_event.is_set():
            try:
                current_memory = performance_monitor.get_memory_usage_mb()
                memory_history.append(current_memory)
                
                # Check for potential memory leaks (sustained growth)
                if len(memory_history) >= 30:  # At least 30 minutes of data
                    avg_recent = sum(list(memory_history)[-10:]) / 10  # Last 10 minutes
                    avg_older = sum(list(memory_history)[-30:-10]) / 20  # 10-30 minutes ago
                    
                    growth_rate = (avg_recent - avg_older) / avg_older * 100
                    
                    if growth_rate > 20:  # 20% memory growth
                        logger.warning(
                            f"Potential memory leak detected: {growth_rate:.1f}% growth "
                            f"(current: {current_memory:.1f}MB)"
                        )
                
                # Log memory status periodically
                if len(memory_history) % 15 == 0:  # Every 15 minutes
                    logger.info(f"Memory usage: {current_memory:.1f}MB")
                
            except Exception as e:
                logger.error(f"Memory monitoring worker error: {e}")
            
            # Wait for next monitoring cycle or shutdown
            try:
                await asyncio.wait_for(
                    self.shutdown_event.wait(),
                    timeout=MEMORY_MONITORING_INTERVAL
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                continue  # Continue with next monitoring cycle

    async def _idle_exit_worker(self, connection_manager):
        """
        Background worker that terminates the process if there are no
        WebSocket connections (dashboard or planning) for IDLE_EXIT_SECONDS.
        """
        logger.info(
            f"Idle exit worker started (timeout={IDLE_EXIT_SECONDS}s, interval={IDLE_CHECK_INTERVAL}s)"
        )

        empty_since: Optional[float] = None

        def total_connections() -> int:
            try:
                total = 0
                # Prefer explicit sets if available
                if hasattr(connection_manager, 'active_connections'):
                    total += len(getattr(connection_manager, 'active_connections', []))
                if hasattr(connection_manager, 'planning_connections'):
                    total += len(getattr(connection_manager, 'planning_connections', []))
                # Fallback to method if sets not present
                if total == 0 and hasattr(connection_manager, 'get_connection_count'):
                    total = int(connection_manager.get_connection_count())
                return total
            except Exception:
                return 0

        while not self.shutdown_event.is_set():
            try:
                total = total_connections()
                if total > 0:
                    empty_since = None
                else:
                    now = time.time()
                    if empty_since is None:
                        empty_since = now
                    elif now - empty_since >= IDLE_EXIT_SECONDS:
                        logger.info(
                            f"No WebSocket connections for {IDLE_EXIT_SECONDS}s — exiting process"
                        )
                        try:
                            os.kill(os.getpid(), signal.SIGTERM)
                        except Exception as e:
                            logger.error(f"Failed to send SIGTERM: {e}")
                            # Hard exit as last resort
                            os._exit(0)
                        break

                # Sleep or until shutdown
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(),
                        timeout=IDLE_CHECK_INTERVAL
                    )
                    break
                except asyncio.TimeoutError:
                    continue
            except Exception as e:
                logger.error(f"Idle exit worker error: {e}")
                # Avoid tight error loop
                await asyncio.sleep(IDLE_CHECK_INTERVAL)


# Global background task manager
background_tasks = BackgroundTasks()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return performance_monitor


def get_background_tasks() -> BackgroundTasks:
    """Get the global background task manager instance."""
    return background_tasks
