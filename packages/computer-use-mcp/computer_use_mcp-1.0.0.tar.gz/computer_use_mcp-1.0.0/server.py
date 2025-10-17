#!/usr/bin/env python3
"""Gemini Computer Use MCP Server.

Exposes Gemini's browser automation capabilities as MCP tools for use with
Claude Code and other MCP clients.

Usage:
    # Test with MCP Inspector
    uv run mcp dev server.py

    # Install in Claude Desktop
    uv run mcp install server.py
"""

import logging
import asyncio
from typing import Any
from pathlib import Path

import anyio
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from browser_agent import GeminiBrowserAgent
from task_manager import task_manager

# Load environment variables
load_dotenv()

# Configure logging to stderr (NEVER use stdout for MCP servers)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # stderr by default
)

logger = logging.getLogger("gemini-computer-use-mcp")

# Create FastMCP server
mcp = FastMCP("gemini-computer-use")


@mcp.tool()
async def browse_web(task: str, url: str = "https://www.google.com") -> dict[str, Any]:
    """
    Browse the web to complete a task using AI-powered browser automation.

    The AI agent can navigate websites, click buttons, fill forms, search for information,
    and interact with web pages just like a human user. This runs synchronously and returns
    when the task is complete.

    Args:
        task: What you want to accomplish (e.g., "Find the top 3 gaming laptops on Amazon")
        url: Starting webpage (defaults to Google)

    Returns:
        Dictionary containing:
        - ok: Boolean indicating success
        - data: Task completion message with results
        - screenshot_dir: Path to saved screenshots
        - session_id: Unique session identifier
        - progress: List of actions taken during browsing
        - error: Error message (if task failed)

    Examples:
        - "Search for Python tutorials and summarize the top result"
        - "Go to example.com and click the login button"
        - "Find product reviews for iPhone 15 Pro"

    Note: For long-running tasks, consider using start_web_task instead.
    """
    logger.info(f"Received web browsing request: {task}")

    # Create agent instance (browser will be cleaned up automatically)
    agent = GeminiBrowserAgent(logger=logger)

    try:
        # Execute task in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, agent.execute_task, task, url)

        logger.info(f"Task completed with status: {result.get('ok')}")
        return result

    finally:
        # Clean up browser resources
        agent.cleanup_browser()


@mcp.tool()
async def get_web_screenshots(session_id: str) -> dict[str, Any]:
    """
    Retrieve screenshots captured during a web browsing session.

    Each browsing session saves screenshots of the pages visited. Use this to
    review what the AI agent saw and did during task execution.

    Args:
        session_id: Session ID returned from browse_web or check_web_task

    Returns:
        Dictionary containing:
        - ok: Boolean indicating success
        - screenshots: List of screenshot file paths
        - session_id: The session identifier
        - count: Number of screenshots found
        - error: Error message (if session not found)

    Example:
        get_web_screenshots("20251017_143022_a1b2c3d4")
    """
    logger.info(f"Retrieving screenshot history for session: {session_id}")

    try:
        from browser_agent import SCREENSHOT_OUTPUT_DIR

        screenshot_dir = Path(SCREENSHOT_OUTPUT_DIR) / session_id

        if not screenshot_dir.exists():
            return {
                "ok": False,
                "error": f"No screenshots found for session {session_id}"
            }

        screenshots = sorted([
            str(p.relative_to(screenshot_dir.parent))
            for p in screenshot_dir.glob("*.png")
        ])

        return {
            "ok": True,
            "screenshots": screenshots,
            "session_id": session_id,
            "count": len(screenshots)
        }

    except Exception as e:
        logger.error(f"Error retrieving screenshots: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@mcp.tool()
async def start_web_task(task: str, url: str = "https://www.google.com") -> dict[str, Any]:
    """
    Start a web browsing task in the background and return immediately.

    Use this for tasks that might take a while (30+ seconds). The task runs
    asynchronously while you continue working. Check progress with check_web_task().

    Args:
        task: What you want to accomplish on the web
        url: Starting webpage (defaults to Google)

    Returns:
        Dictionary containing:
        - ok: Boolean indicating task was started successfully
        - task_id: Unique ID to check progress later
        - status: Will be "running"
        - message: Instructions for checking progress

    Examples:
        - start_web_task("Research top 10 AI companies and their products")
        - start_web_task("Find and compare prices for MacBook Pro on 5 different sites")

    Next steps:
        Use check_web_task(task_id) to monitor progress.
        Wait at least 5 seconds between status checks.
    """
    logger.info(f"Starting async web browsing task: {task}")

    # Create task
    task_id = task_manager.create_task(task, url)

    # Start task in background using anyio (FastMCP best practice)
    # Use anyio.to_thread.run_sync to run the blocking start_task in a thread
    # We await it but start_task itself just spawns the thread and returns immediately
    success = await anyio.to_thread.run_sync(
        task_manager.start_task,
        task_id,
        logger
    )

    if not success:
        return {
            "ok": False,
            "error": "Failed to start task"
        }

    logger.info(f"Task {task_id} started in background, returning immediately")

    return {
        "ok": True,
        "task_id": task_id,
        "status": "running",
        "message": f"Task started. Use check_web_task('{task_id}') to monitor progress."
    }


@mcp.tool()
async def check_web_task(task_id: str, compact: bool = True) -> dict[str, Any]:
    """
    Check progress of a background web browsing task.

    Returns a summary of task progress. By default, returns compact format to
    avoid filling your context window with verbose progress logs.

    IMPORTANT: To prevent context bloat, wait at least 3-5 seconds between
    checks. Use the 'recommended_poll_after' timestamp as guidance.

    Args:
        task_id: Task ID from start_web_task()
        compact: Return summary only (default: True). Set to False for full details.

    Returns:
        Dictionary containing:
        - ok: Boolean indicating success
        - task_id: Task identifier
        - status: "pending", "running", "completed", "failed", or "cancelled"
        - progress_summary: Recent actions (compact mode only)
        - progress: Full action history (full mode only)
        - result: Task results (when completed)
        - error: Error message (when failed)
        - recommended_poll_after: Timestamp to check again (when running)
        - polling_guidance: Message about polling frequency

    Examples:
        - check_web_task("abc-123-def")  # Compact summary
        - check_web_task("abc-123-def", compact=False)  # Full details

    Best Practice:
        Only poll every 3-5 seconds to keep your context window clean.
        Use the wait() tool to pause between checks if your platform doesn't
        support automatic delays.

    Recommended workflow:
        1. start_web_task("...")
        2. wait(5)
        3. check_web_task(task_id)
        4. If still running, repeat steps 2-3
    """
    logger.info(f"Checking status for task: {task_id}")

    status = task_manager.get_task_status(task_id, compact=compact)

    if not status:
        return {
            "ok": False,
            "error": f"Task {task_id} not found"
        }

    # Add poll delay guidance for running tasks
    from datetime import datetime, timedelta, timezone

    result = {
        "ok": True,
        **status
    }

    if status.get("status") == "running":
        next_check = datetime.now(timezone.utc) + timedelta(seconds=5)
        result["recommended_poll_after"] = next_check.isoformat()
        result["polling_guidance"] = "Task in progress. Wait 5 seconds before next check to avoid context bloat."

    return result


@mcp.tool()
async def stop_web_task(task_id: str) -> dict[str, Any]:
    """
    Stop a running web browsing task.

    Immediately halts task execution and cleans up browser resources. Use this
    when you need to cancel a long-running task that's no longer needed.

    Args:
        task_id: Task ID from start_web_task()

    Returns:
        Dictionary containing:
        - ok: Boolean indicating success
        - message: Confirmation message
        - task_id: The stopped task ID
        - error: Error message (if task not found or already completed)

    Examples:
        - stop_web_task("abc-123-def")

    Note: Cannot stop tasks that are already completed or failed.
    """
    logger.info(f"Stopping web task: {task_id}")

    success = task_manager.cancel_task(task_id)

    if success:
        return {
            "ok": True,
            "message": f"Task {task_id} cancelled successfully",
            "task_id": task_id
        }
    else:
        return {
            "ok": False,
            "error": f"Could not cancel task {task_id} (not found or already completed)",
            "task_id": task_id
        }


@mcp.tool()
async def wait(seconds: int) -> dict[str, Any]:
    """
    Wait for a specified number of seconds before continuing.

    Use this when you need to pause between operations, such as:
    - Waiting between status checks to avoid rapid polling
    - Giving a web task time to make progress
    - Rate limiting your requests
    - Waiting for external processes to complete

    Args:
        seconds: Number of seconds to wait (1-60)

    Returns:
        Dictionary containing:
        - ok: Boolean indicating success
        - waited_seconds: How long the wait lasted
        - message: Confirmation message

    Examples:
        - wait(5)  # Wait 5 seconds
        - wait(10)  # Wait 10 seconds

    Best Practice:
        Use this instead of immediately polling check_web_task multiple times.
        Recommended wait time between status checks: 3-5 seconds.

    Note: Maximum wait time is 60 seconds to prevent timeout issues.
    """
    # Validate input
    if seconds < 1:
        return {
            "ok": False,
            "error": "Wait time must be at least 1 second"
        }

    if seconds > 60:
        return {
            "ok": False,
            "error": "Wait time cannot exceed 60 seconds. For longer waits, call this tool multiple times."
        }

    logger.info(f"Waiting for {seconds} seconds...")

    # Use anyio sleep for async compatibility
    import time
    await anyio.sleep(seconds)

    logger.info(f"Wait completed: {seconds} seconds")

    return {
        "ok": True,
        "waited_seconds": seconds,
        "message": f"Successfully waited {seconds} seconds"
    }


@mcp.tool()
async def list_web_tasks() -> dict[str, Any]:
    """
    List all web browsing tasks, including active and completed ones.

    Shows a summary of all tasks in the current session. Useful for tracking
    multiple concurrent browsing operations.

    Returns:
        Dictionary containing:
        - ok: Boolean indicating success
        - tasks: Array of task status objects (compact format)
        - count: Total number of tasks
        - active_count: Number of currently running tasks

    Examples:
        - list_web_tasks()

    Note: Returns compact task summaries. Use check_web_task(task_id) for details.
    """
    logger.info("Listing all web tasks")

    tasks = task_manager.list_tasks()
    active_count = sum(1 for t in tasks if t.get("status") in ["pending", "running"])

    return {
        "ok": True,
        "tasks": tasks,
        "count": len(tasks),
        "active_count": active_count
    }


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
