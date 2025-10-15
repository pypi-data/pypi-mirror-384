import os
import contextlib
import tempfile
import requests
from adbutils import adb, AdbDevice
from rich.console import Console

ASSET_NAME = "mahoraga-portal"
APK_DOWNLOAD_URL = "https://storage.googleapis.com/misc_quash_static/mahoraga-portal-v0.1.apk"

PORTAL_PACKAGE_NAME = "com.mahoraga.portal"
A11Y_SERVICE_NAME = (
    f"{PORTAL_PACKAGE_NAME}/com.mahoraga.portal.MahoragaAccessibilityService"
)


def download_portal_apk(debug: bool = False) -> str:
    """Download the Mahoraga Portal APK from cloud storage."""
    console = Console()

    try:
        console.print("📥 Downloading Quash Portal APK...")
        if debug:
            console.print(f"Download URL: {APK_DOWNLOAD_URL}")

        response = requests.get(APK_DOWNLOAD_URL, stream=True)
        response.raise_for_status()

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.apk')

        # Download with progress
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    progress = (downloaded / total_size) * 100
                    console.print(f"\rProgress: {progress:.1f}%", end="")

        temp_file.close()
        console.print(f"\n✅ Downloaded APK to {temp_file.name}")
        return temp_file.name

    except requests.RequestException as e:
        raise Exception(f"Failed to download Portal APK: {e}")
    except Exception as e:
        raise Exception(f"Error downloading Portal APK: {e}")


def get_local_portal_apk(apk_path: str = None):
    """Get the path to a local portal APK file."""
    if apk_path and os.path.exists(apk_path):
        return apk_path

    # Look for APK in common locations
    common_paths = [
        f"{ASSET_NAME}.apk",
        f"./assets/{ASSET_NAME}.apk",
        f"./portal/{ASSET_NAME}.apk"
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    # If no local APK found, download it
    return download_portal_apk()


@contextlib.contextmanager
def use_portal_apk(apk_path: str = None, debug: bool = False):
    console = Console()
    temp_file = None

    try:
        local_apk_path = get_local_portal_apk(apk_path)
        console.print(f"📱 Using Portal APK: [bold]{os.path.basename(local_apk_path)}[/bold]")
        if debug:
            console.print(f"APK Path: {local_apk_path}")

        # Track if this is a temp file we downloaded
        if local_apk_path.startswith(tempfile.gettempdir()):
            temp_file = local_apk_path

        yield local_apk_path
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise
    finally:
        # Clean up downloaded temp file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
                if debug:
                    console.print(f"🗑️ Cleaned up temp file: {temp_file}")
            except Exception:
                pass  # Ignore cleanup errors


def enable_portal_accessibility(device: AdbDevice):
    device.shell(
        f"settings put secure enabled_accessibility_services {A11Y_SERVICE_NAME}"
    )
    device.shell("settings put secure accessibility_enabled 1")


def check_portal_accessibility(device: AdbDevice, debug: bool = False) -> bool:
    a11y_services = device.shell("settings get secure enabled_accessibility_services")
    if not A11Y_SERVICE_NAME in a11y_services:
        if debug:
            print(a11y_services)
        return False

    a11y_enabled = device.shell("settings get secure accessibility_enabled")
    if a11y_enabled != "1":
        if debug:
            print(a11y_enabled)
        return False

    return True


def ping_portal(device: AdbDevice, debug: bool = False):
    """
    Ping the Quash Portal to check if it is installed and accessible.
    """
    try:
        packages = device.list_packages()
    except Exception as e:
        raise Exception(f"Failed to list packages: {e}")

    if not PORTAL_PACKAGE_NAME in packages:
        if debug:
            print(packages)
        raise Exception("Portal is not installed on the device")

    if not check_portal_accessibility(device, debug):
        device.shell("am start -a android.settings.ACCESSIBILITY_SETTINGS")
        raise Exception(
            "Quash Portal is not enabled as an accessibility service on the device"
        )


def ping_portal_content(device: AdbDevice, debug: bool = False):
    try:
        state = device.shell("content query --uri content://com.mahoraga.portal/state")
        if not "Row: 0 result=" in state:
            raise Exception("Failed to get state from Quash Portal")
    except Exception as e:
        raise Exception(f"Quash Portal is not reachable: {e}")


def ping_portal_tcp(device: AdbDevice, debug: bool = False):
    """Check TCP forwarding to portal."""
    from .adb_tools import AdbTools
    try:
        tools = AdbTools(serial=device.serial, use_tcp=True)
    except Exception as e:
        raise Exception(f"Failed to setup TCP forwarding: {e}")