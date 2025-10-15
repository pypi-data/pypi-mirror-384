"""
Backend API Client for Quash MCP.
Handles all communication with the Quash backend API.
"""

import os
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BackendClient:
    """Client for communicating with Quash backend API."""

    def __init__(self):
        # Get backend URL from environment variable, default to production backend
        self.base_url = os.getenv("MAHORAGA_BACKEND_URL", "http://13.220.180.140:8000")
        self.timeout = 300.0  # 5 minutes for long-running LLM calls
        logger.info(f"🔧 Backend client initialized: URL={self.base_url}")

    async def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Validate quash_api_key and check user credits.

        Args:
            api_key: The mahoraga API key to validate

        Returns:
            Dict with validation result:
            {
                "valid": bool,
                "user": {"email": str, "name": str, "credits": float},
                "openrouter_api_key": str,
                "error": str (if invalid)
            }
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/validate",
                    json={"api_key": api_key}
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "valid": False,
                        "error": f"API error: {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"Failed to validate API key: {e}")
            return {
                "valid": False,
                "error": f"Connection error: {str(e)}"
            }

    async def execute_task(
        self,
        api_key: str,
        task: str,
        device_serial: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute task with Quash agent on backend (V2 - AI on backend).

        Args:
            api_key: Quash API key
            task: Task description
            device_serial: Device serial number
            config: Execution configuration (model, temp, vision, reasoning, etc.)

        Returns:
            Dict with execution result:
            {
                "status": "success"|"failed"|"error"|"interrupted",
                "message": str,
                "steps_taken": int,
                "final_message": str,
                "tokens": {"prompt": int, "completion": int, "total": int},
                "cost": float,
                "duration_seconds": float,
                "error": str (if error)
            }
        """
        logger.info(f"🚀 Executing task on backend: {task[:50]}...")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/agent/execute",
                    json={
                        "api_key": api_key,
                        "task": task,
                        "device_serial": device_serial,
                        "config": config
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Backend execution completed: {result['status']}")
                    return result
                else:
                    error_msg = f"Backend error: HTTP {response.status_code}"
                    logger.error(error_msg)
                    return {
                        "status": "error",
                        "message": error_msg,
                        "error": error_msg
                    }

        except Exception as e:
            error_msg = f"Failed to execute on backend: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "error": str(e)
            }

    async def log_execution(
        self,
        api_key: str,
        execution_id: str,
        task: str,
        device_serial: str,
        status: str,
        tokens: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None,
        error: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        duration_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Log execution completion and usage to backend.

        Args:
            api_key: Quash API key
            execution_id: Unique execution identifier
            task: Task description
            device_serial: Device serial number
            status: "completed", "failed", or "interrupted"
            tokens: Token usage dict
            cost: Execution cost in USD
            error: Error message if failed
            config: Execution configuration (model, temp, vision, etc.)
            duration_seconds: Time taken to complete

        Returns:
            Dict with logging result:
            {
                "logged": bool,
                "credits_deducted": float,
                "new_balance": float,
                "error": str (if failed)
            }
        """
        logger.info(f"📊 Logging execution - Cost: ${cost}, Status: {status}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/execution/complete",
                    json={
                        "api_key": api_key,
                        "execution_id": execution_id,
                        "task": task,
                        "device_serial": device_serial,
                        "status": status,
                        "tokens": tokens,
                        "cost": cost,
                        "error": error,
                        "config": config,
                        "duration_seconds": duration_seconds
                    }
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to log execution: {response.status_code}")
                    return {"logged": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Failed to log execution: {e}")
            return {"logged": False, "error": str(e)}

    async def execute_step(
        self,
        api_key: str,
        session_id: str,
        step_number: int,
        task: str,
        ui_state: Dict[str, Any],
        chat_history: list,
        config: Dict[str, Any],
        screenshot_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Execute single agent step (V3 - Step-by-step execution).

        Sends device state to backend, receives next action to execute.

        Args:
            api_key: Quash API key
            session_id: Unique session identifier
            step_number: Current step number
            task: Original task description
            ui_state: Device UI state (a11y_tree, phone_state)
            chat_history: Previous conversation messages
            config: Execution configuration
            screenshot_bytes: Optional screenshot (only if vision=True)

        Returns:
            Dict with action to execute:
            {
                "action": {"type": str, "code": str, "reasoning": str},
                "completed": bool,
                "success": bool (if completed),
                "final_message": str (if completed),
                "assistant_response": str,
                "tokens_used": {"prompt": int, "completion": int, "total": int},
                "cost": float
            }
        """
        import json

        try:
            # Prepare form data (multipart)
            data_dict = {
                "api_key": api_key,
                "session_id": session_id,
                "step_number": step_number,
                "task": task,
                "ui_state": ui_state,
                "chat_history": chat_history,
                "config": config
            }

            # Convert to JSON string
            data_json = json.dumps(data_dict)

            # Prepare form data (data field as string)
            form_data = {"data": data_json}

            # Prepare files dict (only screenshot if provided)
            files = {}
            if screenshot_bytes:
                files["screenshot"] = ("screenshot.png", screenshot_bytes, "image/png")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Send both form data and files (multipart/form-data)
                response = await client.post(
                    f"{self.base_url}/api/agent/step",
                    data=form_data,
                    files=files if files else None
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    error_msg = f"Backend error: HTTP {response.status_code}"
                    logger.error(error_msg)
                    return {
                        "status": "error",
                        "message": error_msg,
                        "error": error_msg
                    }

        except Exception as e:
            error_msg = f"Failed to execute step: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "error": str(e)
            }


# Singleton instance
_backend_client = None


def get_backend_client() -> BackendClient:
    """Get the global backend client instance."""
    global _backend_client
    if _backend_client is None:
        _backend_client = BackendClient()
    return _backend_client