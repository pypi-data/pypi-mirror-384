"""
Execute tool - Run automation tasks via step-by-step backend communication.

V3: Hybrid architecture - AI logic on backend (private), device access local (public).
"""

from typing import Dict, Any, Callable, Optional
from .execute_v3 import execute_v3


async def execute(
    task: str,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Execute an automation task on the connected Android device.

    Uses step-by-step execution:
    - Captures device state locally
    - Sends to backend for AI decision
    - Executes actions locally
    - Keeps proprietary AI logic private on backend

    Args:
        task: Natural language task description
        progress_callback: Optional callback for progress updates

    Returns:
        Dict with execution result and details
    """
    return await execute_v3(task=task, progress_callback=progress_callback)