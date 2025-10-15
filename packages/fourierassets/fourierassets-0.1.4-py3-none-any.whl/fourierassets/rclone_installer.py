"""
rclone installation checker and installer for fourierassets.
"""

import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from typing import Tuple
from pathlib import Path

from .logger import get_logger


class RcloneInstaller:
    """Handle rclone installation verification and automatic installation."""

    RCLONE_VERSION = "v1.71.0"
    # Primary mirror (internal nexus)
    PRIMARY_BASE_URL = (
        f"https://nexus.fftaicorp.com/repository/downloads.rclone.org/{RCLONE_VERSION}/"
    )
    # Fallback mirror (official site)
    FALLBACK_BASE_URL = f"https://downloads.rclone.org/{RCLONE_VERSION}/"

    def __init__(self, verbose=False):
        self.logger = get_logger(f"{__name__}.RcloneInstaller")
        self.verbose = verbose

    def check_rclone_available(self) -> bool:
        """Check if rclone is available in system PATH or user bin directory."""
        # First check system PATH
        rclone_path = shutil.which("rclone")
        if rclone_path:
            self.logger.debug("Found rclone in PATH at: %s", rclone_path)
            return True

        # Check user bin directory
        user_bin = self.get_user_bin_path()
        user_rclone = user_bin / (
            "rclone.exe" if platform.system() == "Windows" else "rclone"
        )
        if user_rclone.exists() and user_rclone.is_file():
            self.logger.debug("Found rclone in user bin at: %s", user_rclone)
            # Update PATH for current session to include user bin
            current_path = os.environ.get("PATH", "")
            if str(user_bin) not in current_path:
                os.environ["PATH"] = f"{user_bin}{os.pathsep}{current_path}"
                self.logger.debug("Added user bin to PATH: %s", user_bin)
            return True

        self.logger.debug("rclone not found in PATH or user bin directory")
        return False

    def get_system_info(self) -> Tuple[str, str]:
        """Get system platform and architecture information."""
        system = platform.system().lower()
        machine = platform.machine().lower()

        # Normalize system names
        if system == "darwin":
            system = "osx"

        # Normalize architecture names
        if machine in ["x86_64", "amd64"]:
            arch = "amd64"
        elif machine in ["aarch64", "arm64"]:
            arch = "arm64"
        elif machine.startswith("arm"):
            arch = "arm"
        elif machine in ["i386", "i686"]:
            arch = "386"
        else:
            arch = machine

        return system, arch

    def get_download_filename(self) -> str:
        """Generate the rclone download filename based on system."""
        system, arch = self.get_system_info()

        if system == "windows":
            return f"rclone-{self.RCLONE_VERSION}-{system}-{arch}.zip"
        else:
            return f"rclone-{self.RCLONE_VERSION}-{system}-{arch}.zip"

    def get_user_bin_path(self) -> Path:
        """Get user-writable bin directory."""
        home = Path.home()

        # Try common user bin directories
        candidates = [
            home / ".local" / "bin",  # Linux standard
            home / "bin",  # macOS/Unix common
            home / "usr" / "local" / "bin",  # Alternative
        ]

        for bin_path in candidates:
            try:
                bin_path.mkdir(parents=True, exist_ok=True)
                # Test if we can write to this directory
                test_file = bin_path / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
                self.logger.debug("Using bin directory: %s", bin_path)
                return bin_path
            except (PermissionError, OSError):
                continue

        # Fallback: create a fourierassets-specific bin directory
        fallback_bin = home / ".fourierassets" / "bin"
        fallback_bin.mkdir(parents=True, exist_ok=True)
        self.logger.debug("Using fallback bin directory: %s", fallback_bin)
        return fallback_bin

    def is_path_in_env(self, path: Path) -> bool:
        """Check if a path is in the system PATH."""
        env_path = os.environ.get("PATH", "")
        return str(path) in env_path.split(os.pathsep)

    def test_url_accessibility(
        self, base_url: str, filename: str, timeout: int = 10
    ) -> bool:
        """Test if a download URL is accessible."""
        test_url = base_url + filename
        try:
            self.logger.debug("Testing URL accessibility: %s", test_url)
            request = urllib.request.Request(test_url, method="HEAD")
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status == 200:
                    self.logger.debug("URL is accessible: %s", test_url)
                    return True
                else:
                    self.logger.debug(
                        "URL returned status %d: %s", response.status, test_url
                    )
                    return False
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            self.logger.debug("URL not accessible: %s, error: %s", test_url, e)
            return False
        except Exception as e:
            self.logger.debug(
                "Unexpected error testing URL: %s, error: %s", test_url, e
            )
            return False

    def get_best_download_url(self, filename: str) -> str:
        """Get the best available download URL, trying primary first, then fallback."""
        # Try primary mirror (nexus) first
        if self.test_url_accessibility(self.PRIMARY_BASE_URL, filename):
            self.logger.info("Using primary mirror: %s", self.PRIMARY_BASE_URL)
            if self.verbose:
                print("📡 Using internal mirror (faster download)")
            return self.PRIMARY_BASE_URL + filename

        # Fall back to official mirror
        if self.test_url_accessibility(self.FALLBACK_BASE_URL, filename):
            self.logger.info("Using fallback mirror: %s", self.FALLBACK_BASE_URL)
            if self.verbose:
                print("🌐 Using official mirror")
            return self.FALLBACK_BASE_URL + filename

        # If both fail, still try the fallback (might work despite HEAD request failing)
        self.logger.warning(
            "Both mirrors failed accessibility test, trying fallback anyway"
        )
        if self.verbose:
            print("⚠️ Mirror accessibility test failed, attempting official mirror")
        return self.FALLBACK_BASE_URL + filename

    def download_and_install_rclone(self) -> bool:
        """Download and install rclone binary."""
        try:
            filename = self.get_download_filename()
            download_url = self.get_best_download_url(filename)

            self.logger.info("Downloading rclone from: %s", download_url)
            if self.verbose:
                print(f"Downloading rclone {self.RCLONE_VERSION}...")

            # Create temporary directory for download
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                zip_file_path = temp_path / filename

                # Download the file
                try:
                    urllib.request.urlretrieve(download_url, zip_file_path)
                    self.logger.debug("Downloaded to: %s", zip_file_path)
                except Exception as e:
                    self.logger.error("Failed to download rclone: %s", e)
                    return False

                # Extract the zip file
                extract_path = temp_path / "extracted"
                extract_path.mkdir()

                with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                    zip_ref.extractall(extract_path)

                # Find the rclone binary
                rclone_binary = None
                for root, _dirs, files in os.walk(extract_path):
                    for file in files:
                        if file == "rclone" or file == "rclone.exe":
                            rclone_binary = Path(root) / file
                            break
                    if rclone_binary:
                        break

                if not rclone_binary or not rclone_binary.exists():
                    self.logger.error(
                        "Could not find rclone binary in downloaded package"
                    )
                    return False

                # Get user bin directory
                bin_path = self.get_user_bin_path()
                target_name = (
                    "rclone.exe" if platform.system() == "Windows" else "rclone"
                )
                target_path = bin_path / target_name

                # Copy the binary
                shutil.copy2(rclone_binary, target_path)

                # Make it executable on Unix systems
                if platform.system() != "Windows":
                    target_path.chmod(target_path.stat().st_mode | stat.S_IEXEC)

                self.logger.info("Installed rclone to: %s", target_path)

                # Check if bin directory is in PATH
                if not self.is_path_in_env(bin_path):
                    if self.verbose:
                        self.logger.warning("Bin directory %s is not in PATH", bin_path)
                        print(
                            f"\n⚠️  Installation complete, but {bin_path} is not in your PATH."
                        )
                        print("To use rclone, either:")
                        print(f"1. Add {bin_path} to your PATH environment variable")
                        print(
                            "2. Restart your terminal (some shells auto-include ~/.local/bin)"
                        )
                        print(f"3. Use the full path: {target_path}")
                    else:
                        self.logger.debug("Bin directory %s is not in PATH", bin_path)

                return True

        except Exception as e:
            self.logger.error("Failed to download and install rclone: %s", e)
            return False

    def is_unix_system(self) -> bool:
        """Check if current system is Unix-like."""
        return platform.system() in ["Linux", "Darwin"]  # Darwin is macOS

    def install_rclone_unix(self) -> bool:
        """Install rclone on Unix systems using the official install script."""
        if not self.is_unix_system():
            raise OSError("This installation method only supports Unix-like systems")

        try:
            self.logger.info("Installing rclone using official install script...")

            # Run the installation command
            cmd = "curl -fsSL https://rclone.org/install.sh | sudo bash"

            print("Installing rclone...")
            print("This will run: curl https://rclone.org/install.sh | sudo bash")
            print("You may be prompted for your password.")

            # Use shell=True to properly handle the pipe
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=False,  # Let user see the output
                text=True,
            )

            if result.returncode == 0:
                self.logger.info("rclone installation completed successfully")
                return True
            else:
                self.logger.error(
                    "rclone installation failed with return code %d", result.returncode
                )
                return False

        except subprocess.CalledProcessError as e:
            self.logger.error("Failed to install rclone: %s", e)
            return False
        except Exception as e:
            self.logger.error("Unexpected error during rclone installation: %s", e)
            return False

    def prompt_manual_installation(self):
        """Provide manual installation instructions for non-Unix systems."""
        system = platform.system()

        print("\n" + "=" * 60)
        print("rclone is required but not found on your system!")
        print("=" * 60)

        if system == "Windows":
            print("\nFor Windows, please install rclone manually:")
            print("1. Download rclone from: https://rclone.org/downloads/")
            print("2. Extract the archive and add rclone.exe to your PATH")
            print("3. Or use chocolatey: choco install rclone")
            print("4. Or use scoop: scoop install rclone")
        else:
            print(f"\nFor {system}, please install rclone manually:")
            print("Visit: https://rclone.org/install/")

        print("\nAfter installation, please restart your terminal and try again.")
        print("=" * 60)

    def ensure_rclone_available(self, auto_install: bool = True) -> bool:
        """
        Ensure rclone is available, automatically installing if needed.

        Args:
            auto_install: If True, attempt automatic installation

        Returns:
            bool: True if rclone is available, False otherwise
        """
        # First check if it's already available
        if self.check_rclone_available():
            return True

        if self.verbose:
            self.logger.warning("rclone not found in system PATH")
        else:
            self.logger.debug("rclone not found in system PATH")

        # If not available and auto_install is enabled
        if auto_install:
            if self.verbose:
                print(
                    "\nrclone is required but not found. Attempting automatic installation..."
                )

            # Automatically try to install without user confirmation
            if self.download_and_install_rclone():
                # Check again after installation
                if self.check_rclone_available():
                    if self.verbose:
                        print("✓ rclone installed successfully!")
                    return True
                else:
                    print(
                        "✗ rclone installation may have failed. Please check manually."
                    )
                    print("You may need to restart your terminal or update your PATH.")
                    self.prompt_manual_installation()
                    return False
            else:
                print("✗ Failed to install rclone automatically.")
                self.prompt_manual_installation()
                return False
        else:
            # Auto install disabled
            self.prompt_manual_installation()
            return False


def check_rclone_dependency(verbose=False):
    """
    Check rclone dependency and install if needed.
    This function is called during package initialization.

    Args:
        verbose: If True, show detailed output and warnings
    """
    installer = RcloneInstaller(verbose=verbose)

    if not installer.ensure_rclone_available(auto_install=True):
        print("\nError: rclone is required for fourierassets to work properly.")
        print("Please install rclone manually and try again.")
        sys.exit(1)


def verify_rclone_silent() -> bool:
    """
    Silently check if rclone is available without prompting for installation.
    Returns True if available, False otherwise.
    """
    installer = RcloneInstaller(verbose=False)
    return installer.check_rclone_available()
