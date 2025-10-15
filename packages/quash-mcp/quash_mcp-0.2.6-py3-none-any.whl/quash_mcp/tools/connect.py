"""
Connect tool - Manage Android device connectivity.
Connects to Android devices/emulators and verifies accessibility service.
"""

import subprocess
from typing import Dict, Any, Optional
from ..state import get_state


def list_devices() -> list:
    """List all connected Android devices."""
    try:
        from adbutils import adb
        devices = adb.list()
        return [{"serial": d.serial, "state": d.state} for d in devices]
    except Exception as e:
        return []


def get_device_info(serial: str) -> Optional[Dict[str, str]]:
    """Get detailed information about a device."""
    try:
        from adbutils import adb
        device = adb.device(serial)

        # Get device properties
        model = device.prop.get("ro.product.model", "Unknown")
        android_version = device.prop.get("ro.build.version.release", "Unknown")

        return {
            "serial": serial,
            "model": model,
            "android_version": android_version
        }
    except Exception as e:
        return None


def check_portal_service(serial: str) -> bool:
    """Check if Quash Portal accessibility service is enabled."""
    try:
        from adbutils import adb
        from quash_mcp.device.portal import ping_portal

        device = adb.device(serial)
        ping_portal(device, debug=False)
        return True
    except Exception:
        return False


def setup_portal(serial: str) -> tuple[bool, str]:
    """Setup Quash Portal on the device."""
    try:
        from adbutils import adb
        from quash_mcp.device.portal import use_portal_apk, enable_portal_accessibility

        device = adb.device(serial)

        # Install APK
        with use_portal_apk(None, debug=False) as apk_path:
            device.install(apk_path, uninstall=True, flags=["-g"], silent=True)

        # Enable accessibility service
        enable_portal_accessibility(device)

        return True, "Portal installed and enabled successfully"
    except Exception as e:
        return False, f"Failed to setup portal: {str(e)}"


async def connect(device_serial: Optional[str] = None) -> Dict[str, Any]:
    """
    Connect to an Android device or emulator.
    If device_serial is not provided, auto-selects if only one device is connected.

    Args:
        device_serial: Optional device serial number

    Returns:
        Dict with connection status and device information
    """
    state = get_state()

    # List available devices
    devices = list_devices()

    if not devices:
        return {
            "status": "failed",
            "message": "❌ No Android devices found. Please connect a device or start an emulator.",
            "instructions": [
                "To start an emulator: Open Android Studio > AVD Manager > Start",
                "To connect a physical device: Enable USB debugging and connect via USB",
                "To connect over WiFi: Run 'adb tcpip 5555' then 'adb connect <device-ip>:5555'"
            ]
        }

    # Select device
    selected_serial = device_serial
    if not selected_serial:
        if len(devices) == 1:
            selected_serial = devices[0]["serial"]
        else:
            return {
                "status": "failed",
                "message": f"❌ Multiple devices found ({len(devices)}). Please specify which one to use.",
                "available_devices": devices
            }

    # Verify device exists
    if not any(d["serial"] == selected_serial for d in devices):
        return {
            "status": "failed",
            "message": f"❌ Device '{selected_serial}' not found.",
            "available_devices": devices
        }

    # Get device info
    device_info = get_device_info(selected_serial)
    if not device_info:
        return {
            "status": "failed",
            "message": f"❌ Failed to get information for device '{selected_serial}'."
        }

    # Check portal accessibility service
    portal_ready = check_portal_service(selected_serial)

    if not portal_ready:
        # Attempt to setup portal
        setup_success, setup_msg = setup_portal(selected_serial)
        if setup_success:
            portal_ready = True
            portal_message = "✓ Portal setup completed"
        else:
            portal_message = f"⚠️ Portal not ready: {setup_msg}"
    else:
        portal_message = "✓ Portal already enabled"

    # Update state
    state.device_serial = selected_serial
    state.device_info = device_info
    state.portal_ready = portal_ready

    return {
        "status": "connected" if portal_ready else "partial",
        "device": device_info,
        "portal_ready": portal_ready,
        "portal_message": portal_message,
        "message": f"✅ Connected to {device_info['model']} ({selected_serial})"
    }