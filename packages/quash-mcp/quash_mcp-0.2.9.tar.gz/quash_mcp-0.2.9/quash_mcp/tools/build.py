"""
Build tool V2 - Comprehensive dependency checker and installer.
Checks, installs, validates versions, and fixes PATH issues.
"""

import sys
import subprocess
import shutil
import platform
import os
from typing import Dict, Any, Tuple, List
from pathlib import Path


class DependencyChecker:
    """Comprehensive dependency checker and installer"""

    def __init__(self):
        self.os_type = platform.system()  # Darwin, Linux, Windows
        self.issues = []
        self.successes = []

    # ==================== PYTHON VERSION ====================

    def check_python_version(self) -> Tuple[bool, str, str]:
        """Check if Python version is >= 3.11 and show path"""
        version = sys.version_info
        current = f"{version.major}.{version.minor}.{version.micro}"
        python_path = sys.executable

        if version.major >= 3 and version.minor >= 11:
            return True, f"✓ Python {current} at {python_path}", None
        else:
            return False, f"✗ Python {current} at {python_path} (requires >= 3.11)", \
                   f"Please upgrade Python to 3.11 or higher. Current: {current}"

    def install_python(self) -> Tuple[bool, str]:
        """Attempt to install Python 3.13 based on OS"""

        if self.os_type == "Darwin":  # macOS
            return self._install_python_macos()
        elif self.os_type == "Linux":
            return self._install_python_linux()
        elif self.os_type == "Windows":
            return self._install_python_windows()
        else:
            return False, f"✗ Unsupported OS: {self.os_type}"

    def _install_python_macos(self) -> Tuple[bool, str]:
        """Install Python 3.13 on macOS via Homebrew"""
        if not shutil.which("brew"):
            return False, "✗ Homebrew not found. Install from: https://brew.sh/"

        try:
            print("  Installing Python 3.13 via Homebrew...")
            subprocess.run(
                ["brew", "install", "python@3.13"],
                check=True,
                capture_output=True,
                timeout=600,
                text=True
            )
            return True, "✓ Python 3.13 installed via Homebrew. Please restart your terminal and run build again."
        except subprocess.TimeoutExpired:
            return False, "✗ Installation timed out"
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            return False, f"✗ Homebrew install failed: {error_msg}"
        except Exception as e:
            return False, f"✗ Installation error: {str(e)}"

    def _install_python_linux(self) -> Tuple[bool, str]:
        """Install Python 3.13 on Linux"""
        # Try deadsnakes PPA for Ubuntu/Debian
        if shutil.which("apt-get"):
            try:
                print("  Adding deadsnakes PPA and installing Python 3.13...")
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "software-properties-common"],
                    check=True,
                    capture_output=True,
                    timeout=120
                )
                subprocess.run(
                    ["sudo", "add-apt-repository", "-y", "ppa:deadsnakes/ppa"],
                    check=True,
                    capture_output=True,
                    timeout=120
                )
                subprocess.run(
                    ["sudo", "apt-get", "update"],
                    check=True,
                    capture_output=True,
                    timeout=120
                )
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "python3.13", "python3.13-venv"],
                    check=True,
                    capture_output=True,
                    timeout=300
                )
                return True, "✓ Python 3.13 installed. Use 'python3.13' to run."
            except Exception as e:
                return False, f"✗ apt-get install failed: {str(e)}"

        # Try dnf for Fedora/RHEL
        elif shutil.which("dnf"):
            try:
                print("  Installing Python 3.13 via dnf...")
                subprocess.run(
                    ["sudo", "dnf", "install", "-y", "python3.13"],
                    check=True,
                    capture_output=True,
                    timeout=300
                )
                return True, "✓ Python 3.13 installed via dnf"
            except Exception as e:
                return False, f"✗ dnf install failed: {str(e)}"
        else:
            return False, "✗ No supported package manager found"

    def _install_python_windows(self) -> Tuple[bool, str]:
        """Install Python on Windows"""
        return False, (
            "✗ Please install Python manually:\n"
            "  1. Download: https://www.python.org/downloads/\n"
            "  2. Run installer and check 'Add to PATH'\n"
            "  3. Install Python 3.11 or higher"
        )

    # ==================== ADB ====================

    def check_adb(self) -> Tuple[bool, str, str]:
        """Check if ADB is installed and get version"""
        adb_path = shutil.which("adb")

        if adb_path:
            try:
                result = subprocess.run(
                    ["adb", "version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                version_line = result.stdout.split('\n')[0]
                return True, f"✓ ADB installed at {adb_path} ({version_line})", None
            except Exception as e:
                return True, f"✓ ADB found at {adb_path} (version check failed)", None

        return False, "✗ ADB not found in PATH", None

    def install_adb(self) -> Tuple[bool, str]:
        """Attempt to install ADB based on OS"""

        if self.os_type == "Darwin":  # macOS
            return self._install_adb_macos()
        elif self.os_type == "Linux":
            return self._install_adb_linux()
        elif self.os_type == "Windows":
            return self._install_adb_windows()
        else:
            return False, f"✗ Unsupported OS: {self.os_type}"

    def _install_adb_macos(self) -> Tuple[bool, str]:
        """Install ADB on macOS"""
        # Check if Homebrew is installed
        if not shutil.which("brew"):
            return False, "✗ Homebrew not found. Install from: https://brew.sh/"

        try:
            print("  Installing ADB via Homebrew...")
            result = subprocess.run(
                ["brew", "install", "android-platform-tools"],
                capture_output=True,
                timeout=300,
                text=True
            )

            # Check if already installed (cask returns different messages)
            combined_output = (result.stdout + result.stderr).lower()
            already_installed = (
                "android-platform-tools" in combined_output and
                ("already installed" in combined_output or
                 "not upgrading" in combined_output or
                 "reinstalling" in combined_output)
            )

            # Verify ADB is in PATH after installation
            if not shutil.which("adb"):
                if already_installed:
                    print("  ADB package already installed but not in PATH, reinstalling...")
                    # For casks, we need to reinstall to recreate symlinks
                    try:
                        subprocess.run(
                            ["brew", "reinstall", "android-platform-tools"],
                            check=True,
                            capture_output=True,
                            timeout=120
                        )
                    except Exception as reinstall_error:
                        pass  # Continue to manual symlink creation

                    # Always check and create symlink manually after reinstall
                    # (casks don't automatically create symlinks in /opt/homebrew/bin)
                    if not shutil.which("adb"):
                        print("  Reinstall completed, creating symlink manually...")
                        cask_path = Path("/opt/homebrew/Caskroom/android-platform-tools")
                        if cask_path.exists():
                            # Find the version directory (sorted to get latest)
                            versions = sorted(cask_path.glob("*"))
                            if versions:
                                adb_src = versions[-1] / "platform-tools" / "adb"
                                if adb_src.exists():
                                    adb_link = Path("/opt/homebrew/bin/adb")
                                    try:
                                        if adb_link.exists() or adb_link.is_symlink():
                                            adb_link.unlink()
                                        adb_link.symlink_to(adb_src)
                                        print(f"  Created symlink: {adb_link} -> {adb_src}")
                                    except Exception as symlink_error:
                                        return False, f"✗ Failed to create symlink: {str(symlink_error)}"
                                else:
                                    return False, f"✗ ADB binary not found at {adb_src}"
                            else:
                                return False, f"✗ No version directories found in {cask_path}"
                        else:
                            return False, f"✗ Caskroom path not found: {cask_path}"
                else:
                    print("  Installation completed but ADB not found in PATH")

            # Final verification
            if shutil.which("adb"):
                return True, "✓ ADB installed successfully via Homebrew"
            else:
                return False, "✗ ADB installation completed but not found in PATH. Try restarting terminal."

        except subprocess.TimeoutExpired:
            return False, "✗ Installation timed out"
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            # Even if brew install fails due to already installed, continue to verification
            if "already installed" in error_msg.lower():
                if shutil.which("adb"):
                    return True, "✓ ADB already installed via Homebrew"
            return False, f"✗ Homebrew install failed: {error_msg}"
        except Exception as e:
            return False, f"✗ Installation error: {str(e)}"

    def _install_adb_linux(self) -> Tuple[bool, str]:
        """Install ADB on Linux"""
        # Try apt-get first (Debian/Ubuntu)
        if shutil.which("apt-get"):
            try:
                print("  Installing ADB via apt-get (may require sudo)...")
                subprocess.run(
                    ["sudo", "apt-get", "update"],
                    check=True,
                    capture_output=True,
                    timeout=120
                )
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "adb"],
                    check=True,
                    capture_output=True,
                    timeout=300
                )
                return True, "✓ ADB installed successfully via apt-get"
            except Exception as e:
                return False, f"✗ apt-get install failed: {str(e)}"

        # Try dnf (Fedora/RHEL)
        elif shutil.which("dnf"):
            try:
                print("  Installing ADB via dnf (may require sudo)...")
                subprocess.run(
                    ["sudo", "dnf", "install", "-y", "android-tools"],
                    check=True,
                    capture_output=True,
                    timeout=300
                )
                return True, "✓ ADB installed successfully via dnf"
            except Exception as e:
                return False, f"✗ dnf install failed: {str(e)}"

        else:
            return False, "✗ No supported package manager found (apt-get/dnf)"

    def _install_adb_windows(self) -> Tuple[bool, str]:
        """Install ADB on Windows"""
        # Windows doesn't have good package manager by default
        # Provide download link instead
        return False, (
            "✗ Please install ADB manually:\n"
            "  1. Download: https://developer.android.com/tools/releases/platform-tools\n"
            "  2. Extract to C:\\platform-tools\n"
            "  3. Add to PATH: C:\\platform-tools"
        )

    def check_adb_in_path(self) -> Tuple[bool, str, str]:
        """Check if ADB is in PATH and suggest fix if not"""
        adb_path = shutil.which("adb")

        if adb_path:
            return True, f"✓ ADB in PATH: {adb_path}", None

        # Try to find ADB in common locations
        common_paths = []

        if self.os_type == "Darwin":
            common_paths = [
                "/opt/homebrew/bin/adb",
                "/usr/local/bin/adb",
                Path.home() / "Library/Android/sdk/platform-tools/adb",
            ]
        elif self.os_type == "Linux":
            common_paths = [
                "/usr/bin/adb",
                "/usr/local/bin/adb",
                Path.home() / "Android/Sdk/platform-tools/adb",
            ]
        elif self.os_type == "Windows":
            common_paths = [
                "C:\\platform-tools\\adb.exe",
                "C:\\Android\\sdk\\platform-tools\\adb.exe",
                Path.home() / "AppData/Local/Android/Sdk/platform-tools/adb.exe",
            ]

        for path in common_paths:
            if Path(path).exists():
                return False, f"⚠️  ADB found at {path} but not in PATH", str(path)

        return False, "✗ ADB not found anywhere", None

    def add_to_path(self, adb_path: str) -> Tuple[bool, str]:
        """Add ADB directory to PATH"""
        adb_dir = str(Path(adb_path).parent)

        shell_rc = None
        if self.os_type == "Darwin":
            # Check which shell
            shell = os.environ.get("SHELL", "")
            if "zsh" in shell:
                shell_rc = Path.home() / ".zshrc"
            else:
                shell_rc = Path.home() / ".bash_profile"
        elif self.os_type == "Linux":
            shell_rc = Path.home() / ".bashrc"

        if shell_rc:
            try:
                with open(shell_rc, "a") as f:
                    f.write(f'\n# Added by Quash MCP\nexport PATH="$PATH:{adb_dir}"\n')

                return True, (
                    f"✓ Added to PATH in {shell_rc}\n"
                    f"  Please run: source {shell_rc}\n"
                    f"  Or restart your terminal"
                )
            except Exception as e:
                return False, f"✗ Failed to update {shell_rc}: {str(e)}"

        return False, "✗ Could not determine shell config file"

    # ==================== MAHORAGA PACKAGE ====================

    def check_mahoraga(self) -> Tuple[bool, str, str]:
        """Check if Quash package is installed"""
        try:
            import mahoraga
            version = getattr(mahoraga, "__version__", "unknown")
            location = Path(mahoraga.__file__).parent
            return True, f"✓ Quash v{version} installed at {location}", None
        except ImportError:
            return False, "✗ Quash package not installed", None

    def install_mahoraga(self) -> Tuple[bool, str]:
        """Install Quash package"""
        try:
            # Check if we're in development mode (source available)
            project_root = Path(__file__).parent.parent.parent.parent
            mahoraga_src = project_root / "mahoraga"

            if mahoraga_src.exists() and (mahoraga_src / "pyproject.toml").exists():
                # Install from local source
                print(f"  Installing Quash from {mahoraga_src}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", str(mahoraga_src)],
                    check=True,
                    capture_output=True
                )
                return True, f"✓ Quash installed from local source: {mahoraga_src}"
            else:
                # Try to install from PyPI (if published)
                print("  Installing Quash from PyPI...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "mahoraga"],
                    check=True,
                    capture_output=True
                )
                return True, "✓ Quash installed from PyPI"

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            return False, f"✗ Installation failed: {error_msg}"
        except Exception as e:
            return False, f"✗ Error: {str(e)}"

    def check_mahoraga_version(self) -> Tuple[bool, str, str]:
        """Check if Quash version is compatible"""
        try:
            import mahoraga
            version = getattr(mahoraga, "__version__", "0.0.0")

            # Parse version
            major, minor, patch = version.split(".")[:3]

            # We need at least 0.3.0
            if int(major) == 0 and int(minor) >= 3:
                return True, f"✓ Quash v{version} (compatible)", None
            elif int(major) > 0:
                return True, f"✓ Quash v{version} (compatible)", None
            else:
                return False, f"✗ Quash v{version} (requires >= 0.3.0)", version
        except Exception as e:
            return False, f"✗ Version check failed: {str(e)}", None

    # ==================== PYTHON DEPENDENCIES ====================

    def check_python_dependencies(self) -> Tuple[bool, str, List[str]]:
        """Check if all required Python packages are installed with correct versions"""
        required_packages = {
            "click": "8.1.0",
            "rich": "13.0.0",
            "pydantic": "2.0.0",
            "aiofiles": "23.0.0",
            "openai": "1.0.0",
            "pillow": "10.0.0",
            "python-dotenv": "1.0.0",
            "requests": "2.31.0",
            "llama-index": None,  # No specific version
            "llama-index-llms-openai-like": None,
            "adbutils": "2.10.0",  # Exact version
            "apkutils": "2.0.0",  # Exact version
        }

        missing = []
        incompatible = []

        for package, min_version in required_packages.items():
            try:
                # Import the package to check if it's installed
                if package == "python-dotenv":
                    import dotenv
                    pkg = dotenv
                    pkg_name = "dotenv"
                elif package == "pillow":
                    from PIL import Image
                    pkg = Image
                    pkg_name = "PIL"
                elif package == "llama-index-llms-openai-like":
                    from llama_index.llms import openai_like
                    pkg = openai_like
                    pkg_name = "llama_index.llms.openai_like"
                else:
                    pkg_name = package.replace("-", "_")
                    pkg = __import__(pkg_name)

                # Check version if required
                if min_version:
                    version = getattr(pkg, "__version__", None)
                    if version:
                        # Parse version numbers
                        current_parts = version.split(".")[:3]
                        required_parts = min_version.split(".")[:3]

                        # For exact version requirements (adbutils, apkutils)
                        if package in ["adbutils", "apkutils"]:
                            if version != min_version:
                                incompatible.append(f"{package}=={min_version} (current: {version})")
                        else:
                            # For minimum version requirements
                            try:
                                current_ver = tuple(int(x) for x in current_parts)
                                required_ver = tuple(int(x) for x in required_parts)
                                if current_ver < required_ver:
                                    incompatible.append(f"{package}>={min_version} (current: {version})")
                            except ValueError:
                                # If version parsing fails, skip version check
                                pass
            except ImportError:
                missing.append(package)

        if missing or incompatible:
            msg_parts = []
            if missing:
                msg_parts.append(f"Missing: {', '.join(missing)}")
            if incompatible:
                msg_parts.append(f"Incompatible: {', '.join(incompatible)}")
            return False, f"✗ Python dependencies: {'; '.join(msg_parts)}", missing + incompatible
        else:
            return True, f"✓ All Python dependencies installed", None

    def install_python_dependencies(self) -> Tuple[bool, str]:
        """Install all required Python dependencies"""
        try:
            print("  Installing Python dependencies...")

            # Install from Quash's pyproject.toml if available
            project_root = Path(__file__).parent.parent.parent.parent
            mahoraga_src = project_root / "mahoraga"

            if mahoraga_src.exists() and (mahoraga_src / "pyproject.toml").exists():
                print(f"  Installing from {mahoraga_src}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", str(mahoraga_src)],
                    check=True,
                    capture_output=True,
                    timeout=300
                )
                return True, "✓ Python dependencies installed from local source"
            else:
                # Install individual packages with version constraints
                packages = [
                    "click>=8.1.0",
                    "rich>=13.0.0",
                    "pydantic>=2.0.0",
                    "aiofiles>=23.0.0",
                    "openai>=1.0.0",
                    "pillow>=10.0.0",
                    "python-dotenv>=1.0.0",
                    "requests>=2.31.0",
                    "llama-index",
                    "llama-index-llms-openai-like",
                    "adbutils==2.10.0",
                    "apkutils==2.0.0",
                ]

                print(f"  Installing {len(packages)} packages...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + packages,
                    check=True,
                    capture_output=True,
                    timeout=600
                )
                return True, "✓ Python dependencies installed"

        except subprocess.TimeoutExpired:
            return False, "✗ Dependency installation timed out"
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            return False, f"✗ Dependency installation failed: {error_msg}"
        except Exception as e:
            return False, f"✗ Installation error: {str(e)}"

    # ==================== PORTAL APK ====================

    def check_portal(self) -> Tuple[bool, str, str]:
        """Check if Portal APK download works"""
        try:
            from quash_mcp.device.portal import download_portal_apk
            return True, "✓ Portal APK download available", None
        except ImportError as e:
            return False, f"✗ Portal module not found: {str(e)}", None
        except Exception as e:
            return False, f"✗ Portal check failed: {str(e)}", None


async def build() -> Dict[str, Any]:
    """
    Comprehensive build check and setup.

    1. Checks all dependencies
    2. Validates versions
    3. Auto-installs where possible
    4. Fixes PATH issues

    Returns:
        Dict with detailed status of all checks and fixes
    """
    checker = DependencyChecker()
    details = {}
    fixes_applied = []
    all_ok = True

    print("=" * 70)
    print("MAHORAGA MCP - DEPENDENCY CHECK & SETUP")
    print("=" * 70)
    print()

    # 1. Check Python Version
    print("1️⃣  Checking Python version...")
    py_ok, py_msg, py_fix = checker.check_python_version()
    details["python"] = py_msg
    print(f"   {py_msg}")

    if not py_ok:
        # Try to install Python 3.13
        print("   Attempting to install Python 3.13...")
        install_ok, install_msg = checker.install_python()
        details["python_install"] = install_msg
        print(f"   {install_msg}")

        if not install_ok:
            all_ok = False
        else:
            fixes_applied.append("Installed Python 3.13")
            print(f"   ⚠️  Please restart your terminal and run build again with python3.13")
    print()

    # 2. Check ADB
    print("2️⃣  Checking ADB...")
    adb_ok, adb_msg, _ = checker.check_adb()
    details["adb"] = adb_msg
    print(f"   {adb_msg}")

    if not adb_ok:
        # Try to install
        print("   Attempting to install ADB...")
        install_ok, install_msg = checker.install_adb()
        details["adb_install"] = install_msg
        print(f"   {install_msg}")

        if not install_ok:
            all_ok = False
        else:
            fixes_applied.append("Installed ADB")

    # 3. Check ADB in PATH
    print("3️⃣  Checking ADB PATH...")
    path_ok, path_msg, found_path = checker.check_adb_in_path()
    details["adb_path"] = path_msg
    print(f"   {path_msg}")

    if not path_ok and found_path:
        # Try to add to PATH
        print("   Attempting to add ADB to PATH...")
        path_fix_ok, path_fix_msg = checker.add_to_path(found_path)
        details["adb_path_fix"] = path_fix_msg
        print(f"   {path_fix_msg}")

        if path_fix_ok:
            fixes_applied.append("Added ADB to PATH")
    elif not path_ok:
        all_ok = False
    print()

    # 4. Check Quash Package (Optional - only for developers with local source)
    print("4️⃣  Checking Quash package (optional for development)...")
    mhg_ok, mhg_msg, _ = checker.check_mahoraga()
    details["mahoraga"] = mhg_msg
    print(f"   {mhg_msg}")

    mahoraga_just_installed = False
    if not mhg_ok:
        # Check if we're in development mode (source available)
        project_root = Path(__file__).parent.parent.parent.parent
        mahoraga_src = project_root / "mahoraga"

        if mahoraga_src.exists() and (mahoraga_src / "pyproject.toml").exists():
            # Only try to install if local source is available (development mode)
            print("   Local Quash source detected. Attempting to install...")
            install_ok, install_msg = checker.install_mahoraga()
            details["mahoraga_install"] = install_msg
            print(f"   {install_msg}")

            if install_ok:
                fixes_applied.append("Installed Quash from local source")
                mahoraga_just_installed = True
        else:
            # Production mode - skip mahoraga (not needed, device tools in quash_mcp)
            print("   ⏭️  Skipped (not required for end users)")
            details["mahoraga"] = "⏭️  Skipped (device tools included in quash-mcp)"
    print()

    # 5. Check Quash Version (only if installed)
    if mhg_ok or mahoraga_just_installed:
        print("5️⃣  Checking Quash version...")
        ver_ok, ver_msg, ver_fix = checker.check_mahoraga_version()
        details["mahoraga_version"] = ver_msg
        print(f"   {ver_msg}")

        if not ver_ok:
            # Don't fail build for version mismatch - just warn
            if ver_fix:
                fix_msg = f"💡 Consider upgrading: pip install --upgrade mahoraga"
                details["mahoraga_version_fix"] = fix_msg
                print(f"   {fix_msg}")
        print()
    else:
        print("5️⃣  Checking Quash version...")
        print("   ⏭️  Skipped (Quash package not installed)")
        details["mahoraga_version"] = "⏭️  Skipped"
        print()

    # 6. Check Python Dependencies
    # Note: Only check if Quash wasn't just installed, because 'pip install -e'
    # automatically installs all dependencies from pyproject.toml
    if mahoraga_just_installed:
        print("6️⃣  Checking Python dependencies...")
        print(f"   ⏭️  Skipped (dependencies installed with Quash in step 4)")
        details["python_dependencies"] = "⏭️  Skipped (installed with Quash)"
    else:
        print("6️⃣  Checking Python dependencies...")
        deps_ok, deps_msg, missing_deps = checker.check_python_dependencies()
        details["python_dependencies"] = deps_msg
        print(f"   {deps_msg}")

        if not deps_ok:
            # Try to install missing/incompatible dependencies
            print("   Attempting to install Python dependencies...")
            install_ok, install_msg = checker.install_python_dependencies()
            details["python_dependencies_install"] = install_msg
            print(f"   {install_msg}")

            if not install_ok:
                all_ok = False
            else:
                fixes_applied.append("Installed Python dependencies")
    print()

    # 7. Check Portal
    print("7️⃣  Checking Portal APK...")
    portal_ok, portal_msg, _ = checker.check_portal()
    details["portal"] = portal_msg
    print(f"   {portal_msg}")

    if not portal_ok:
        all_ok = False
    print()

    # Final Summary
    print("=" * 70)
    if all_ok:
        status = "success"
        message = "✅ All dependencies ready! You can now use Quash."
        if fixes_applied:
            message += f"\n   Fixes applied: {', '.join(fixes_applied)}"
    else:
        failed = [k for k, v in details.items() if v.startswith("✗")]
        status = "failed"
        message = f"❌ Setup incomplete. Issues with: {', '.join(failed)}"
        message += "\n   Please review the details above and follow the suggestions."

    print(message)
    print("=" * 70)

    return {
        "status": status,
        "details": details,
        "fixes_applied": fixes_applied,
        "message": message
    }