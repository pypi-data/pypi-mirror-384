"""
Device management module for Quash MCP.

This module contains utilities for managing Android devices, including:
- Portal APK installation and setup
- ADB device communication
- Accessibility service management
"""

from .portal import (
    download_portal_apk,
    get_local_portal_apk,
    use_portal_apk,
    enable_portal_accessibility,
    check_portal_accessibility,
    ping_portal,
    ping_portal_content,
    ping_portal_tcp,
    PORTAL_PACKAGE_NAME,
    A11Y_SERVICE_NAME,
)

__all__ = [
    "download_portal_apk",
    "get_local_portal_apk",
    "use_portal_apk",
    "enable_portal_accessibility",
    "check_portal_accessibility",
    "ping_portal",
    "ping_portal_content",
    "ping_portal_tcp",
    "PORTAL_PACKAGE_NAME",
    "A11Y_SERVICE_NAME",
]