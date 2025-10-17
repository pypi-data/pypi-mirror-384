"""Background Task Manager for Browser Automation.

Manages async browser automation tasks with status tracking.
"""

import asyncio
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from browser_agent import GeminiBrowserAgent


class TaskStatus:
    """Task status constants."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BrowserTask:
    """Represents a background browser automation task."""

    def __init__(self, task_id: str, task_description: str, url: str):
        self.task_id = task_id
        self.task_description = task_description
        self.url = url
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.agent: Optional[GeminiBrowserAgent] = None
        self.progress_updates: list = []
        # Note: We don't store thread reference to avoid serialization issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for API responses."""
        return {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "url": self.url,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress_updates.copy() if self.progress_updates else [],
            "result": self.result,
            "error": self.error,
        }

    def to_compact_dict(self) -> Dict[str, Any]:
        """Convert task to compact dictionary with progress summary.

        Returns a smaller response suitable for frequent polling to avoid
        context window bloat in AI models.
        """
        # Get last 3 progress items
        recent_progress = []
        if self.progress_updates:
            recent_progress = [
                item["message"] for item in self.progress_updates[-3:]
            ]

        # Build compact response
        compact = {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "url": self.url,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress_summary": {
                "total_steps": len(self.progress_updates) if self.progress_updates else 0,
                "recent_actions": recent_progress
            }
        }

        # Add result or error if task is complete
        if self.status == TaskStatus.COMPLETED:
            compact["result"] = self.result
        elif self.status == TaskStatus.FAILED:
            compact["error"] = self.error

        return compact


class BrowserTaskManager:
    """Manages background browser automation tasks."""

    def __init__(self):
        self.tasks: Dict[str, BrowserTask] = {}
        self._lock = threading.Lock()

    def create_task(self, task_description: str, url: str = "https://www.google.com") -> str:
        """Create a new browser automation task.

        Args:
            task_description: Description of the browsing task
            url: Starting URL

        Returns:
            task_id: Unique identifier for the task
        """
        task_id = str(uuid.uuid4())
        task = BrowserTask(task_id, task_description, url)

        with self._lock:
            self.tasks[task_id] = task

        return task_id

    def start_task(self, task_id: str, logger=None) -> bool:
        """Start executing a task in the background.

        Args:
            task_id: Task identifier
            logger: Optional logger instance

        Returns:
            True if task started, False if task not found or already running
        """
        with self._lock:
            task = self.tasks.get(task_id)
            if not task or task.status != TaskStatus.PENDING:
                return False

            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc).isoformat()

        # Run task in background thread (don't store reference)
        thread = threading.Thread(
            target=self._execute_task,
            args=(task_id, logger),
            daemon=True,
            name=f"BrowserTask-{task_id[:8]}"
        )
        thread.start()

        if logger:
            logger.info(f"Started background thread for task {task_id[:8]}... Thread: {thread.name}")

        return True

    def _execute_task(self, task_id: str, logger=None):
        """Execute the browser automation task (runs in background thread)."""
        if logger:
            logger.info(f"[Thread {threading.current_thread().name}] Starting execution for task {task_id[:8]}...")

        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                if logger:
                    logger.error(f"Task {task_id} not found in _execute_task")
                return

        try:
            # Create browser agent
            agent = GeminiBrowserAgent(logger=logger)
            task.agent = agent

            # Execute the task
            result = agent.execute_task(task.task_description, task.url)

            with self._lock:
                task.result = result
                task.progress_updates = agent.progress_updates.copy()
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            with self._lock:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now(timezone.utc).isoformat()

        finally:
            # Clean up browser
            if task.agent:
                task.agent.cleanup_browser()

    def get_task_status(self, task_id: str, compact: bool = True) -> Optional[Dict[str, Any]]:
        """Get current status of a task.

        Args:
            task_id: Task identifier
            compact: If True, return compact summary (default). If False, return full progress.

        Returns:
            Task status dictionary or None if not found
        """
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None

            # Get live progress from agent if task is running
            if task.status == TaskStatus.RUNNING and task.agent:
                task.progress_updates = task.agent.progress_updates.copy()

            # Return compact or full format
            if compact:
                return task.to_compact_dict()
            else:
                return task.to_dict()

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was cancelled, False otherwise
        """
        with self._lock:
            task = self.tasks.get(task_id)
            if not task or task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                return False

            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now(timezone.utc).isoformat()

            # Clean up browser if running
            if task.agent:
                task.agent.cleanup_browser()

            return True

    def list_tasks(self) -> list[Dict[str, Any]]:
        """List all tasks.

        Returns:
            List of task status dictionaries
        """
        with self._lock:
            return [task.to_dict() for task in self.tasks.values()]

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove completed tasks older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)

        with self._lock:
            to_remove = []
            for task_id, task in self.tasks.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    if task.completed_at:
                        completed_time = datetime.fromisoformat(task.completed_at).timestamp()
                        if completed_time < cutoff:
                            to_remove.append(task_id)

            for task_id in to_remove:
                del self.tasks[task_id]


# Global task manager instance
task_manager = BrowserTaskManager()
