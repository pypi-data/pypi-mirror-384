"""
Execute tool V3 - Step-by-step execution with local device access.

AI logic runs on backend (private), device access happens locally (public).
This hybrid approach keeps proprietary code private while allowing local device control.
"""

import time
import uuid
import asyncio
from typing import Dict, Any, Callable, Optional
from ..state import get_state
from ..backend_client import get_backend_client
from ..device.state_capture import get_device_state
from ..device.adb_tools import AdbTools

# Import mahoraga components for tool functions
try:
    from mahoraga.tools import Tools, describe_tools
    from mahoraga.tools.adb import AdbTools as MahoragaAdbTools
    from mahoraga.agent.context.personas import DEFAULT
    from mahoraga.agent.utils.async_utils import async_to_sync
except ImportError as e:
    print(f"Warning: Could not import mahoraga components: {e}")
    Tools = None
    describe_tools = None
    MahoragaAdbTools = None
    DEFAULT = None
    async_to_sync = None


async def execute_v3(
    task: str,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Execute automation task using step-by-step backend communication.

    Each step:
    1. Capture device state locally (UI + optional screenshot)
    2. Send to backend for AI decision
    3. Execute returned action locally
    4. Repeat until complete

    Args:
        task: Natural language task description
        progress_callback: Optional callback for progress updates

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

    # Get API key and config
    quash_api_key = state.config["api_key"]
    config = {
        "model": state.config["model"],
        "temperature": state.config["temperature"],
        "vision": state.config["vision"],
        "reasoning": state.config["reasoning"],
        "reflection": state.config["reflection"],
        "debug": state.config["debug"]
    }

    # Validate API key
    validation_result = await backend.validate_api_key(quash_api_key)

    if not validation_result.get("valid", False):
        error_msg = validation_result.get("error", "Invalid API key")
        return {
            "status": "error",
            "message": f"❌ API Key validation failed: {error_msg}",
            "prerequisite": "configure"
        }

    # Check credits
    user_info = validation_result.get("user", {})
    credits = user_info.get("credits", 0)

    if credits <= 0:
        return {
            "status": "error",
            "message": f"❌ Insufficient credits. Current balance: ${credits:.2f}",
            "user": user_info
        }

    # Progress logging helper
    def log_progress(message: str):
        if progress_callback:
            progress_callback(message)

    log_progress(f"✅ API Key validated - Credits: ${credits:.2f}")
    log_progress(f"👤 User: {user_info.get('name', 'Unknown')}")
    log_progress(f"🚀 Starting task: {task}")
    log_progress(f"📱 Device: {state.device_serial}")
    log_progress(f"🧠 Model: {config['model']}")

    # Initialize execution
    start_time = time.time()
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    step_number = 0
    chat_history = []
    total_tokens = {"prompt": 0, "completion": 0, "total": 0}
    total_cost = 0.0

    # Initialize local ADB tools for code execution
    adb_tools = AdbTools(serial=state.device_serial, use_tcp=True)

    # Code executor namespace - add tool functions so generated code can call them
    executor_globals = {
        "__builtins__": __builtins__,
        "adb_tools": adb_tools
    }

    # Add tool functions to executor namespace (like start_app, swipe, etc.)
    if describe_tools and DEFAULT and MahoragaAdbTools:
        try:
            # Create a mahoraga AdbTools instance for tool execution
            # This instance has all the tool methods like swipe, start_app, etc.
            mahoraga_tools = MahoragaAdbTools(
                serial=state.device_serial,
                use_tcp=True,
                remote_tcp_port=8080
            )

            # Get all tool functions from mahoraga AdbTools instance
            tool_list = describe_tools(mahoraga_tools, exclude_tools=None)

            # Filter by allowed tools from DEFAULT persona
            allowed_tool_names = DEFAULT.allowed_tools if hasattr(DEFAULT, 'allowed_tools') else []
            filtered_tools = {name: func for name, func in tool_list.items() if name in allowed_tool_names}

            # Add each tool function to executor globals
            for tool_name, tool_function in filtered_tools.items():
                # Convert async functions to sync if needed
                if asyncio.iscoroutinefunction(tool_function):
                    if async_to_sync:
                        tool_function = async_to_sync(tool_function)

                # Add to globals so code can call it directly
                executor_globals[tool_name] = tool_function

            log_progress(f"🔧 Loaded {len(filtered_tools)} tool functions: {list(filtered_tools.keys())}")
        except Exception as e:
            log_progress(f"⚠️ Warning: Could not load tool functions: {e}")
            import traceback
            log_progress(f"Traceback: {traceback.format_exc()}")

    executor_locals = {}

    try:
        # ============================================================
        # STEP-BY-STEP EXECUTION LOOP
        # ============================================================
        while step_number < 15:  # Max 15 steps
            step_number += 1
            log_progress(f"🧠 Step {step_number}: Thinking...")

            # 1. Capture device state
            try:
                ui_state_dict, screenshot_bytes = get_device_state(state.device_serial)

                # Only include screenshot if vision is enabled
                if not config["vision"]:
                    screenshot_bytes = None

            except Exception as e:
                log_progress(f"⚠️ Warning: Failed to capture device state: {e}")
                ui_state_dict = {
                    "a11y_tree": "<hierarchy></hierarchy>",
                    "phone_state": {"package": "unknown"}
                }
                screenshot_bytes = None

            # 2. Send to backend for AI decision
            step_result = await backend.execute_step(
                api_key=quash_api_key,
                session_id=session_id,
                step_number=step_number,
                task=task,
                ui_state=ui_state_dict,
                chat_history=chat_history,
                config=config,
                screenshot_bytes=screenshot_bytes
            )

            # Handle backend errors
            if "error" in step_result:
                log_progress(f"💥 Backend error: {step_result['message']}")
                return {
                    "status": "error",
                    "message": step_result["message"],
                    "error": step_result["error"],
                    "steps_taken": step_number,
                    "tokens": total_tokens,
                    "cost": total_cost,
                    "duration_seconds": time.time() - start_time
                }

            # Update usage tracking
            step_tokens = step_result.get("tokens_used", {})
            step_cost = step_result.get("cost", 0.0)

            total_tokens["prompt"] += step_tokens.get("prompt", 0)
            total_tokens["completion"] += step_tokens.get("completion", 0)
            total_tokens["total"] += step_tokens.get("total", 0)
            total_cost += step_cost

            # Get action from backend
            action = step_result.get("action", {})
            action_type = action.get("type")
            code = action.get("code")
            reasoning = action.get("reasoning")

            # Log reasoning
            if reasoning:
                log_progress(f"🤔 Reasoning: {reasoning}")

            # Update chat history
            assistant_response = step_result.get("assistant_response", "")
            chat_history.append({"role": "assistant", "content": assistant_response})

            # 3. Check if task is complete
            if step_result.get("completed", False):
                success = step_result.get("success", False)
                final_message = step_result.get("final_message", "Task completed")

                duration = time.time() - start_time

                if success:
                    log_progress(f"✅ Task completed successfully in {step_number} steps")
                    log_progress(f"💰 Usage: {total_tokens['total']} tokens, ${total_cost:.4f}")

                    return {
                        "status": "success",
                        "steps_taken": step_number,
                        "final_message": final_message,
                        "message": f"✅ Success: {final_message}",
                        "tokens": total_tokens,
                        "cost": total_cost,
                        "duration_seconds": duration
                    }
                else:
                    log_progress(f"❌ Task failed: {final_message}")
                    log_progress(f"💰 Usage: {total_tokens['total']} tokens, ${total_cost:.4f}")

                    return {
                        "status": "failed",
                        "steps_taken": step_number,
                        "final_message": final_message,
                        "message": f"❌ Failed: {final_message}",
                        "tokens": total_tokens,
                        "cost": total_cost,
                        "duration_seconds": duration
                    }

            # 4. Execute action locally
            if code and action_type == "execute_code":
                log_progress(f"⚡ Executing action...")

                try:
                    # Execute code in sandbox
                    exec(code, executor_globals, executor_locals)

                    # Get execution result
                    execution_output = executor_locals.get("_result", "Code executed successfully")

                    # Add execution result to chat history
                    chat_history.append({
                        "role": "user",
                        "content": f"Execution Result:\n```\n{execution_output}\n```"
                    })

                except Exception as e:
                    error_msg = f"Error during execution: {str(e)}"
                    log_progress(f"💥 Action failed: {error_msg}")

                    # Add error to chat history
                    chat_history.append({
                        "role": "user",
                        "content": f"Execution Result:\n```\n{error_msg}\n```"
                    })

            else:
                # No code to execute
                log_progress("⚠️ No action code provided by backend")
                chat_history.append({
                    "role": "user",
                    "content": "No code was provided. Please provide code to execute."
                })

        # Max steps reached
        log_progress(f"⚠️ Reached maximum steps ({step_number})")
        log_progress(f"💰 Usage: {total_tokens['total']} tokens, ${total_cost:.4f}")

        return {
            "status": "failed",
            "steps_taken": step_number,
            "final_message": f"Reached maximum step limit of {step_number}",
            "message": "❌ Failed: Maximum steps reached",
            "tokens": total_tokens,
            "cost": total_cost,
            "duration_seconds": time.time() - start_time
        }

    except KeyboardInterrupt:
        log_progress("⏹️ Task interrupted by user")
        return {
            "status": "interrupted",
            "message": "⏹️ Task execution interrupted",
            "steps_taken": step_number,
            "tokens": total_tokens,
            "cost": total_cost,
            "duration_seconds": time.time() - start_time
        }

    except Exception as e:
        error_msg = str(e)
        log_progress(f"💥 Error: {error_msg}")
        return {
            "status": "error",
            "message": f"💥 Execution error: {error_msg}",
            "error": error_msg,
            "steps_taken": step_number,
            "tokens": total_tokens,
            "cost": total_cost,
            "duration_seconds": time.time() - start_time
        }

    finally:
        # Cleanup TCP forwarding
        if adb_tools:
            adb_tools.teardown_tcp_forward()