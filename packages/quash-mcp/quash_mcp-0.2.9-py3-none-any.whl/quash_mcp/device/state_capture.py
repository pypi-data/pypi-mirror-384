"""
Device state capture utilities.
Captures UI state and screenshots from Android devices.
"""

import logging
import requests
from typing import Dict, Any, Optional, Tuple
from adbutils import adb

logger = logging.getLogger("quash-device")


def get_current_package(serial: str) -> str:
    """
    Get the currently focused app package.

    Args:
        serial: Device serial number

    Returns:
        Package name of current app
    """
    try:
        device = adb.device(serial)
        output = device.shell("dumpsys window windows | grep -E 'mCurrentFocus'")
        # Parse output like: mCurrentFocus=Window{abc123 u0 com.android.settings/com.android.settings.MainActivity}
        if "/" in output:
            package = output.split("/")[0].split()[-1]
            return package
        return "unknown"
    except Exception as e:
        logger.warning(f"Failed to get current package: {e}")
        return "unknown"


def get_accessibility_tree(serial: str, tcp_port: int = 8080) -> str:
    """
    Get accessibility tree from Portal app via TCP.

    Args:
        serial: Device serial number
        tcp_port: Local TCP port for Portal communication

    Returns:
        Accessibility tree XML string
    """
    try:
        device = adb.device(serial)
        local_port = device.forward_port(tcp_port)

        response = requests.get(
            f"http://localhost:{local_port}/a11y_tree",
            timeout=10
        )

        if response.status_code == 200:
            # Portal returns JSON with status and data fields
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", "<hierarchy></hierarchy>")
            else:
                logger.warning(f"Portal error: {data.get('error', 'Unknown error')}")
                return "<hierarchy></hierarchy>"
        else:
            logger.warning(f"Failed to get accessibility tree: HTTP {response.status_code}")
            return "<hierarchy></hierarchy>"

    except Exception as e:
        logger.warning(f"Failed to get accessibility tree: {e}")
        return "<hierarchy></hierarchy>"


def capture_screenshot(serial: str) -> Optional[bytes]:
    """
    Capture screenshot from device.

    Args:
        serial: Device serial number

    Returns:
        Screenshot as PNG bytes, or None if failed
    """
    try:
        device = adb.device(serial)
        screenshot_bytes = device.shell("screencap -p", stream=True)
        return screenshot_bytes
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return None


def get_device_state(serial: str) -> Tuple[Dict[str, Any], Optional[bytes]]:
    """
    Get complete device state: UI state and screenshot.

    Args:
        serial: Device serial number

    Returns:
        Tuple of (ui_state_dict, screenshot_bytes)
    """
    # Get current package
    current_package = get_current_package(serial)

    # Get accessibility tree
    a11y_tree = get_accessibility_tree(serial)

    # Build UI state
    ui_state = {
        "a11y_tree": a11y_tree,
        "phone_state": {
            "package": current_package,
            "activity": "unknown",  # Can be added later
        }
    }

    # Capture screenshot
    screenshot = capture_screenshot(serial)

    return ui_state, screenshot