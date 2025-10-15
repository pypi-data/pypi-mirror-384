"""
Configure tool - Manage agent configuration parameters.
Allows users to set and update Quash agent execution parameters.
"""

from typing import Dict, Any, Optional
from ..state import get_state


# Valid configuration parameters and their types
VALID_PARAMS = {
    "quash_api_key": str,
    "model": str,
    "temperature": float,
    "max_steps": int,
    "vision": bool,
    "reasoning": bool,
    "reflection": bool,
    "debug": bool,
}


def validate_config(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate configuration parameters.

    Returns:
        (is_valid, error_message)
    """
    for key, value in config.items():
        if key not in VALID_PARAMS:
            return False, f"Invalid parameter: '{key}'. Valid parameters are: {', '.join(VALID_PARAMS.keys())}"

        expected_type = VALID_PARAMS[key]
        if not isinstance(value, expected_type):
            return False, f"Parameter '{key}' must be of type {expected_type.__name__}, got {type(value).__name__}"

    # Validate specific constraints
    if "temperature" in config:
        temp = config["temperature"]
        if not 0 <= temp <= 2:
            return False, "temperature must be between 0 and 2"

    if "max_steps" in config:
        steps = config["max_steps"]
        if steps < 1:
            return False, "max_steps must be at least 1"

    if "model" in config:
        model = config["model"]
        # Basic model name validation
        if not model or not isinstance(model, str) or len(model) < 3:
            return False, "Invalid model name"

    return True, None


async def configure(
    quash_api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_steps: Optional[int] = None,
    vision: Optional[bool] = None,
    reasoning: Optional[bool] = None,
    reflection: Optional[bool] = None,
    debug: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Configure agent execution parameters.
    Only updates parameters that are provided (not None).

    Args:
        quash_api_key: Quash API key for authentication and access
        model: LLM model name (e.g., "openai/gpt-4o")
        temperature: Temperature for LLM (0-2)
        max_steps: Maximum number of execution steps
        vision: Enable vision capabilities (screenshots)
        reasoning: Enable planning with reasoning
        reflection: Enable reflection for self-improvement
        debug: Enable verbose debug logging

    Returns:
        Dict with configuration status and current settings
    """
    state = get_state()

    # Collect provided parameters
    updates = {}
    if quash_api_key is not None:
        updates["api_key"] = quash_api_key
    if model is not None:
        updates["model"] = model
    if temperature is not None:
        updates["temperature"] = temperature
    if max_steps is not None:
        updates["max_steps"] = max_steps
    if vision is not None:
        updates["vision"] = vision
    if reasoning is not None:
        updates["reasoning"] = reasoning
    if reflection is not None:
        updates["reflection"] = reflection
    if debug is not None:
        updates["debug"] = debug

    # If no updates provided, just return current config
    if not updates:
        return {
            "status": "no_changes",
            "current_config": state.get_config_summary(),
            "message": "ℹ️ No parameters provided. Current configuration unchanged."
        }

    # Validate updates (map api_key back to quash_api_key for validation)
    validation_updates = updates.copy()
    if "api_key" in validation_updates:
        validation_updates["quash_api_key"] = validation_updates.pop("api_key")

    is_valid, error_msg = validate_config(validation_updates)
    if not is_valid:
        return {
            "status": "error",
            "message": f"❌ Configuration error: {error_msg}",
            "current_config": state.get_config_summary()
        }

    # Apply updates
    state.update_config(**updates)

    # Prepare response
    updated_keys = list(updates.keys())
    if "api_key" in updated_keys:
        updated_keys[updated_keys.index("api_key")] = "quash_api_key"

    return {
        "status": "configured",
        "updated_parameters": updated_keys,
        "current_config": state.get_config_summary(),
        "message": f"✅ Configuration updated: {', '.join(updated_keys)}"
    }