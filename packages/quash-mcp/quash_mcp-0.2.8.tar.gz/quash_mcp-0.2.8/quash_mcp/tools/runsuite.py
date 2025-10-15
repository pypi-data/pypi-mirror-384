"""
Run Suite tool - Execute multiple tasks in sequence like test suites.
Mimics the Electron app's suite execution functionality.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from ..state import get_state
from .execute import execute


async def runsuite(
    suite_name: str,
    tasks: List[Dict[str, Any]],
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Execute a suite of tasks in sequence.

    Args:
        suite_name: Name of the suite being executed
        tasks: List of task definitions with:
            - prompt (str): Task instruction
            - type (str): 'setup', 'test', or 'teardown' (optional, default 'test')
            - retries (int): Number of retry attempts (optional, default 0)
            - continueOnFailure (bool): Continue suite if task fails (optional, default False)
            - waitBefore (int): Seconds to wait before executing (optional, default 0)
        progress_callback: Optional callback for progress updates

    Returns:
        Dict with suite execution results
    """
    state = get_state()

    # Validate prerequisites
    if not state.is_ready():
        return {
            "status": "error",
            "message": "❌ Not ready to execute suite. Please connect device and configure first.",
            "suite_name": suite_name,
            "completed_tasks": 0,
            "total_tasks": len(tasks)
        }

    # Validate tasks
    if not tasks or len(tasks) == 0:
        return {
            "status": "error",
            "message": "❌ Suite must have at least one task",
            "suite_name": suite_name,
            "completed_tasks": 0,
            "total_tasks": 0
        }

    # Execution tracking
    suite_start_time = time.time()
    results = []
    completed_tasks = 0
    failed_tasks = 0
    skipped_tasks = 0

    def log_progress(message: str):
        """Helper to log progress"""
        if progress_callback:
            progress_callback(message)

    log_progress(f"🚀 Starting suite: {suite_name}")
    log_progress(f"📋 Total tasks: {len(tasks)}")
    log_progress("")

    # Execute each task
    for idx, task_def in enumerate(tasks, 1):
        task_prompt = task_def.get('prompt')
        task_type = task_def.get('type', 'test')
        retries = task_def.get('retries', 0)
        continue_on_failure = task_def.get('continueOnFailure', False)
        wait_before = task_def.get('waitBefore', 0)

        # Validate task has prompt
        if not task_prompt:
            log_progress(f"⚠️  Task {idx}: Skipped (no prompt)")
            skipped_tasks += 1
            results.append({
                "task_number": idx,
                "type": task_type,
                "status": "skipped",
                "message": "No prompt provided"
            })
            continue

        # Wait before executing if specified
        if wait_before > 0:
            log_progress(f"⏳ Task {idx}: Waiting {wait_before}s before execution...")
            await asyncio.sleep(wait_before)

        # Task execution with retries
        task_success = False
        task_attempts = 0
        max_attempts = retries + 1
        task_result = None

        log_progress(f"▶️  Task {idx}/{len(tasks)} [{task_type.upper()}]: {task_prompt[:60]}{'...' if len(task_prompt) > 60 else ''}")

        while task_attempts < max_attempts and not task_success:
            task_attempts += 1

            if task_attempts > 1:
                log_progress(f"   🔄 Retry {task_attempts - 1}/{retries}...")

            try:
                # Execute the task
                task_result = await execute(
                    task=task_prompt,
                    progress_callback=lambda msg: log_progress(f"      {msg}")
                )

                if task_result.get('status') == 'success':
                    task_success = True
                    log_progress(f"   ✅ Task {idx} completed")
                else:
                    if task_attempts < max_attempts:
                        log_progress(f"   ⚠️  Task {idx} failed, retrying...")
                    else:
                        log_progress(f"   ❌ Task {idx} failed after {task_attempts} attempt(s)")

            except Exception as e:
                log_progress(f"   ❌ Task {idx} error: {str(e)}")
                task_result = {
                    "status": "failed",
                    "message": str(e)
                }

        # Record task result
        if task_success:
            completed_tasks += 1
            results.append({
                "task_number": idx,
                "type": task_type,
                "prompt": task_prompt[:100],
                "status": "completed",
                "attempts": task_attempts,
                "message": task_result.get('message', 'Success')
            })
        else:
            failed_tasks += 1
            results.append({
                "task_number": idx,
                "type": task_type,
                "prompt": task_prompt[:100],
                "status": "failed",
                "attempts": task_attempts,
                "message": task_result.get('message', 'Failed') if task_result else 'Unknown error'
            })

            # Check if we should continue or stop
            if not continue_on_failure:
                log_progress("")
                log_progress(f"⛔ Stopping suite execution (task {idx} failed and continueOnFailure=False)")
                log_progress(f"📊 Remaining tasks: {len(tasks) - idx} (skipped)")
                skipped_tasks = len(tasks) - idx
                break

        log_progress("")

    # Calculate suite results
    suite_duration = time.time() - suite_start_time
    total_tasks = len(tasks)
    pass_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Determine overall status
    if completed_tasks == total_tasks:
        status = "completed"
        message = f"✅ Suite '{suite_name}' completed successfully"
    elif completed_tasks > 0:
        status = "partial"
        message = f"⚠️  Suite '{suite_name}' partially completed"
    else:
        status = "failed"
        message = f"❌ Suite '{suite_name}' failed"

    # Final summary
    log_progress("=" * 60)
    log_progress(f"📊 Suite Execution Summary: {suite_name}")
    log_progress("=" * 60)
    log_progress(f"✅ Completed: {completed_tasks}/{total_tasks}")
    log_progress(f"❌ Failed: {failed_tasks}")
    log_progress(f"⏭️  Skipped: {skipped_tasks}")
    log_progress(f"📈 Pass Rate: {pass_rate:.1f}%")
    log_progress(f"⏱️  Duration: {suite_duration:.1f}s")
    log_progress("=" * 60)

    result = {
        "status": status,
        "message": message,
        "suite_name": suite_name,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "skipped_tasks": skipped_tasks,
        "pass_rate": round(pass_rate, 1),
        "duration_seconds": round(suite_duration, 1),
        "task_results": results
    }

    # Save latest suite execution to state
    state.latest_suite = result

    return result