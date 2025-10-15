"""
Build tool - Setup dependencies for Quash MCP.
Checks and installs required dependencies on the user's machine.
"""

import sys
import subprocess
import shutil
import platform
from typing import Dict, Any, Tuple


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is >= 3.11."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        return True, f"✓ Python {version.major}.{version.minor}.{version.micro}"
    return False, f"✗ Python {version.major}.{version.minor}.{version.micro} (requires >= 3.11)"


def check_adb() -> Tuple[bool, str]:
    """Check if ADB is installed."""
    if shutil.which("adb"):
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version_line = result.stdout.split('\n')[0]
            return True, f"✓ ADB installed ({version_line})"
        except Exception:
            return True, "✓ ADB installed"
    return False, "✗ ADB not found"


def install_adb() -> Tuple[bool, str]:
    """Attempt to install ADB based on OS."""
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            # Check if Homebrew is available
            if shutil.which("brew"):
                subprocess.run(
                    ["brew", "install", "android-platform-tools"],
                    check=True,
                    capture_output=True
                )
                return True, "✓ ADB installed via Homebrew"
            else:
                return False, "✗ Homebrew not found. Install from: https://brew.sh/"

        elif system == "Linux":
            # Try apt-get
            if shutil.which("apt-get"):
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "adb"],
                    check=True,
                    capture_output=True
                )
                return True, "✓ ADB installed via apt-get"
            # Try dnf
            elif shutil.which("dnf"):
                subprocess.run(
                    ["sudo", "dnf", "install", "-y", "android-tools"],
                    check=True,
                    capture_output=True
                )
                return True, "✓ ADB installed via dnf"
            else:
                return False, "✗ Package manager not found. Install ADB manually."

        elif system == "Windows":
            return False, "✗ Please install ADB manually from: https://developer.android.com/tools/releases/platform-tools"

        else:
            return False, f"✗ Unsupported OS: {system}"

    except subprocess.CalledProcessError as e:
        return False, f"✗ Installation failed: {str(e)}"
    except Exception as e:
        return False, f"✗ Error: {str(e)}"


def check_mahoraga() -> Tuple[bool, str]:
    """Check if Quash package is available."""
    try:
        import mahoraga
        return True, "✓ Quash package ready"
    except ImportError:
        return False, "✗ Quash package not installed"


def install_mahoraga() -> Tuple[bool, str]:
    """Install Quash package."""
    try:
        # Get the path to mahoraga directory
        import os
        mahoraga_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "mahoraga"
        )

        if os.path.exists(mahoraga_path):
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", mahoraga_path],
                check=True,
                capture_output=True
            )
            return True, "✓ Quash installed successfully"
        else:
            return False, f"✗ Quash directory not found at: {mahoraga_path}"
    except subprocess.CalledProcessError as e:
        return False, f"✗ Installation failed: {e.stderr.decode() if e.stderr else str(e)}"
    except Exception as e:
        return False, f"✗ Error: {str(e)}"


async def build() -> Dict[str, Any]:
    """
    Setup and verify all dependencies required for Quash.
    Auto-installs missing dependencies where possible.

    Returns:
        Dict with status and details of all dependencies
    """
    details = {}
    all_ok = True

    # Check Python version
    python_ok, python_msg = check_python_version()
    details["python"] = python_msg
    if not python_ok:
        all_ok = False

    # Check and install ADB
    adb_ok, adb_msg = check_adb()
    if not adb_ok:
        # Try to auto-install
        install_ok, install_msg = install_adb()
        details["adb"] = install_msg
        if not install_ok:
            all_ok = False
    else:
        details["adb"] = adb_msg

    # Check and install Quash
    mahoraga_ok, mahoraga_msg = check_mahoraga()
    if not mahoraga_ok:
        # Try to auto-install
        install_ok, install_msg = install_mahoraga()
        details["mahoraga"] = install_msg
        if not install_ok:
            all_ok = False
    else:
        details["mahoraga"] = mahoraga_msg

    # Check portal APK (just verify it exists in mahoraga)
    try:
        from mahoraga.portal import use_portal_apk
        details["portal_apk"] = "✓ Portal APK available"
    except Exception as e:
        details["portal_apk"] = f"✗ Portal APK not found: {str(e)}"
        all_ok = False

    # Determine overall status
    if all_ok:
        status = "success"
        message = "✅ All dependencies ready! You can now use Quash."
    else:
        failed_items = [k for k, v in details.items() if v.startswith("✗")]
        if len(failed_items) == len(details):
            status = "failed"
            message = f"❌ Setup failed. Missing: {', '.join(failed_items)}"
        else:
            status = "partial"
            message = f"⚠️ Partially ready. Issues with: {', '.join(failed_items)}"

    return {
        "status": status,
        "details": details,
        "message": message
    }