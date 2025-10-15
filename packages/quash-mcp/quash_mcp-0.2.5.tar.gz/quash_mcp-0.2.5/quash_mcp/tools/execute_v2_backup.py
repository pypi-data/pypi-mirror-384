"""
Execute tool - Run automation tasks via backend API.
All AI/agent logic runs on the backend to protect business logic.
"""

from typing import Dict, Any, Callable, Optional
from ..state import get_state
from ..backend_client import get_backend_client


async def execute(
    task: str,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Execute an automation task on the connected Android device.

    All AI execution happens on the backend - this keeps proprietary logic private.

    Args:
        task: Natural language task description
        progress_callback: Optional callback for progress updates (not used in V2)

    Returns:
        Dict with execution result and details
    """
    state = get_state()
    backend = get_backend_client()

    # Check prerequisites
    if not state.is_device_connected():
        return {
            "status": "error",
            "message": "❌ No device connected. Please run 'connect' first.",
            "prerequisite": "connect"
        }

    if not state.is_configured():
        return {
            "status": "error",
            "message": "❌ Configuration incomplete. Please run 'configure' with your Quash API key.",
            "prerequisite": "configure"
        }

    if not state.portal_ready:
        return {
            "status": "error",
            "message": "⚠️ Portal accessibility service not ready. Please ensure it's enabled on the device.",
            "prerequisite": "connect"
        }

    # Get API key and config from state
    quash_api_key = state.config["api_key"]

    # Validate API key with backend
    validation_result = await backend.validate_api_key(quash_api_key)

    if not validation_result.get("valid", False):
        error_msg = validation_result.get("error", "Invalid API key")
        return {
            "status": "error",
            "message": f"❌ API Key validation failed: {error_msg}",
            "prerequisite": "configure"
        }

    # Check user credits
    user_info = validation_result.get("user", {})
    credits = user_info.get("credits", 0)

    if credits <= 0:
        return {
            "status": "error",
            "message": f"❌ Insufficient credits. Current balance: ${credits:.2f}. Please add credits at https://quashbugs.com",
            "user": user_info
        }

    # Progress callback (for backward compatibility)
    def log_progress(message: str):
        """Send progress updates."""
        if progress_callback:
            progress_callback(message)

    log_progress(f"✅ API Key validated - Credits: ${credits:.2f}")
    log_progress(f"👤 User: {user_info.get('name', 'Unknown')}")
    log_progress(f"🚀 Starting task: {task}")
    log_progress(f"📱 Device: {state.device_serial}")
    log_progress(f"🧠 Model: {state.config['model']}")
    log_progress("⚙️ Executing on backend...")

    try:
        # ============================================================
        # EXECUTE ON BACKEND - ALL AI LOGIC IS PRIVATE
        # The backend handles: LLM setup, agent initialization,
        # execution, pricing, usage tracking, credit deduction
        # ============================================================

        result = await backend.execute_task(
            api_key=quash_api_key,
            task=task,
            device_serial=state.device_serial,
            config={
                "model": state.config["model"],
                "temperature": state.config["temperature"],
                "vision": state.config["vision"],
                "reasoning": state.config["reasoning"],
                "reflection": state.config["reflection"],
                "debug": state.config["debug"]
            }
        )

        # Process result
        status = result.get("status")
        message = result.get("message", "")
        steps_taken = result.get("steps_taken", 0)
        final_message = result.get("final_message", "")
        tokens = result.get("tokens", {})
        cost = result.get("cost", 0.0)
        duration = result.get("duration_seconds", 0.0)
        error = result.get("error")

        # Log usage info
        if tokens and cost:
            total_tokens = tokens.get("total", 0)
            log_progress(f"💰 Usage: {total_tokens} tokens, ${cost:.4f}")

        # Return formatted result
        if status == "success":
            log_progress(f"✅ Task completed successfully in {steps_taken} steps")
            return {
                "status": "success",
                "steps_taken": steps_taken,
                "final_message": final_message,
                "message": message,
                "tokens": tokens,
                "cost": cost,
                "duration_seconds": duration
            }
        elif status == "failed":
            log_progress(f"❌ Task failed: {final_message}")
            return {
                "status": "failed",
                "steps_taken": steps_taken,
                "final_message": final_message,
                "message": message,
                "tokens": tokens,
                "cost": cost,
                "duration_seconds": duration
            }
        elif status == "interrupted":
            log_progress("⏹️ Task interrupted")
            return {
                "status": "interrupted",
                "message": message
            }
        else:  # error
            log_progress(f"💥 Error: {error or message}")
            return {
                "status": "error",
                "message": message,
                "error": error or message
            }

    except KeyboardInterrupt:
        log_progress("⏹️ Task interrupted by user")
        return {
            "status": "interrupted",
            "message": "⏹️ Task execution interrupted"
        }

    except Exception as e:
        error_msg = str(e)
        log_progress(f"💥 Error: {error_msg}")
        return {
            "status": "error",
            "message": f"💥 Execution error: {error_msg}",
            "error": error_msg
        }