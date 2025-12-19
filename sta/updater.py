"""Update checker and installer for STA Starship Simulator.

Checks GitHub Releases for new versions and handles downloading/installing updates.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from sta.version import __version__, GITHUB_OWNER, GITHUB_REPO


class UpdateInfo:
    """Information about an available update."""

    def __init__(self, version: str, download_url: str, release_notes: str, published_at: str):
        self.version = version
        self.download_url = download_url
        self.release_notes = release_notes
        self.published_at = published_at

    def __repr__(self):
        return f"UpdateInfo(version={self.version!r})"


def get_current_version() -> str:
    """Get the currently installed version."""
    return __version__


def parse_version(version_str: str) -> tuple:
    """Parse a version string into a comparable tuple."""
    # Remove 'v' prefix if present
    version_str = version_str.lstrip('v')
    parts = version_str.split('.')
    result = []
    for part in parts:
        # Handle pre-release suffixes like "1.0.0-beta"
        if '-' in part:
            num, suffix = part.split('-', 1)
            result.append(int(num))
            result.append(suffix)
        else:
            try:
                result.append(int(part))
            except ValueError:
                result.append(part)
    return tuple(result)


def is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current version."""
    try:
        latest_parts = parse_version(latest)
        current_parts = parse_version(current)
        return latest_parts > current_parts
    except (ValueError, TypeError):
        # If parsing fails, do string comparison
        return latest.lstrip('v') > current.lstrip('v')


def check_for_updates() -> Optional[UpdateInfo]:
    """Check GitHub Releases for a newer version.

    Returns:
        UpdateInfo if a newer version is available, None otherwise.
        Returns None on any error (network issues, etc.)
    """
    api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

    try:
        request = urllib.request.Request(
            api_url,
            headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': f'STA-Starship-Simulator/{__version__}'
            }
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        latest_version = data.get('tag_name', '').lstrip('v')
        if not latest_version:
            return None

        current_version = get_current_version()

        if not is_newer_version(latest_version, current_version):
            return None

        # Find the Mac .app download (look for .zip or .dmg containing mac/darwin)
        download_url = None
        for asset in data.get('assets', []):
            name = asset.get('name', '').lower()
            if ('mac' in name or 'darwin' in name or 'osx' in name) and \
               (name.endswith('.zip') or name.endswith('.dmg')):
                download_url = asset.get('browser_download_url')
                break

        # If no Mac-specific asset, look for any .zip
        if not download_url:
            for asset in data.get('assets', []):
                if asset.get('name', '').endswith('.zip'):
                    download_url = asset.get('browser_download_url')
                    break

        if not download_url:
            # No downloadable asset found
            return None

        return UpdateInfo(
            version=latest_version,
            download_url=download_url,
            release_notes=data.get('body', ''),
            published_at=data.get('published_at', '')
        )

    except Exception as e:
        # Log but don't crash - update checking should be non-critical
        print(f"Update check failed: {e}")
        return None


def download_update(update_info: UpdateInfo, progress_callback=None) -> Optional[Path]:
    """Download an update to a temporary location.

    Args:
        update_info: The update to download
        progress_callback: Optional callable(bytes_downloaded, total_bytes) for progress

    Returns:
        Path to the downloaded file, or None on failure
    """
    try:
        request = urllib.request.Request(
            update_info.download_url,
            headers={'User-Agent': f'STA-Starship-Simulator/{__version__}'}
        )

        # Create temp file with appropriate extension
        suffix = '.zip' if update_info.download_url.endswith('.zip') else '.dmg'
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix='sta_update_')
        os.close(fd)

        with urllib.request.urlopen(request, timeout=300) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192

            with open(temp_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback and total_size:
                        progress_callback(downloaded, total_size)

        return Path(temp_path)

    except Exception as e:
        print(f"Download failed: {e}")
        return None


def get_app_bundle_path() -> Optional[Path]:
    """Get the path to the current .app bundle if running from one."""
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        exe_path = Path(sys.executable)
        # Navigate up from MacOS/executable to .app
        if exe_path.parent.name == 'MacOS':
            app_path = exe_path.parent.parent.parent
            if app_path.suffix == '.app':
                return app_path
    return None


def install_update(downloaded_file: Path, restart: bool = True) -> bool:
    """Install a downloaded update.

    For .zip files: Extracts and replaces the current .app bundle
    For .dmg files: Mounts, copies the .app, and unmounts

    Args:
        downloaded_file: Path to the downloaded update file
        restart: Whether to restart the app after installing

    Returns:
        True if installation succeeded (app will restart), False otherwise
    """
    current_app = get_app_bundle_path()
    if not current_app:
        print("Cannot install update: not running from an app bundle")
        return False

    try:
        if downloaded_file.suffix == '.zip':
            return _install_from_zip(downloaded_file, current_app, restart)
        elif downloaded_file.suffix == '.dmg':
            return _install_from_dmg(downloaded_file, current_app, restart)
        else:
            print(f"Unknown update format: {downloaded_file.suffix}")
            return False
    except Exception as e:
        print(f"Installation failed: {e}")
        return False


def _install_from_zip(zip_path: Path, current_app: Path, restart: bool) -> bool:
    """Install update from a zip file."""
    import zipfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_path)

        # Find the .app in the extracted contents
        new_app = None
        for item in temp_path.iterdir():
            if item.suffix == '.app':
                new_app = item
                break

        # Check subdirectories if not found at top level
        if not new_app:
            for subdir in temp_path.iterdir():
                if subdir.is_dir():
                    for item in subdir.iterdir():
                        if item.suffix == '.app':
                            new_app = item
                            break

        if not new_app:
            print("No .app bundle found in update")
            return False

        # Replace the current app
        backup_path = current_app.with_suffix('.app.backup')

        # Remove old backup if exists
        if backup_path.exists():
            shutil.rmtree(backup_path)

        # Move current app to backup
        shutil.move(str(current_app), str(backup_path))

        try:
            # Copy new app to original location
            shutil.copytree(str(new_app), str(current_app))

            # Make executable
            exe_path = current_app / 'Contents' / 'MacOS'
            for exe in exe_path.iterdir():
                os.chmod(exe, 0o755)

            # Remove backup on success
            shutil.rmtree(backup_path)

            if restart:
                # Launch the new app and exit
                subprocess.Popen(['open', str(current_app)])
                sys.exit(0)

            return True

        except Exception as e:
            # Restore backup on failure
            print(f"Update failed, restoring backup: {e}")
            if backup_path.exists():
                shutil.rmtree(current_app, ignore_errors=True)
                shutil.move(str(backup_path), str(current_app))
            raise


def _install_from_dmg(dmg_path: Path, current_app: Path, restart: bool) -> bool:
    """Install update from a DMG file."""
    mount_point = None

    try:
        # Mount the DMG
        result = subprocess.run(
            ['hdiutil', 'attach', str(dmg_path), '-mountpoint', '/Volumes/STAUpdate', '-nobrowse'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Failed to mount DMG: {result.stderr}")
            return False

        mount_point = Path('/Volumes/STAUpdate')

        # Find the .app in the mounted DMG
        new_app = None
        for item in mount_point.iterdir():
            if item.suffix == '.app':
                new_app = item
                break

        if not new_app:
            print("No .app bundle found in DMG")
            return False

        # Replace the current app (same process as zip)
        backup_path = current_app.with_suffix('.app.backup')

        if backup_path.exists():
            shutil.rmtree(backup_path)

        shutil.move(str(current_app), str(backup_path))

        try:
            shutil.copytree(str(new_app), str(current_app))

            exe_path = current_app / 'Contents' / 'MacOS'
            for exe in exe_path.iterdir():
                os.chmod(exe, 0o755)

            shutil.rmtree(backup_path)

            if restart:
                subprocess.Popen(['open', str(current_app)])
                sys.exit(0)

            return True

        except Exception as e:
            print(f"Update failed, restoring backup: {e}")
            if backup_path.exists():
                shutil.rmtree(current_app, ignore_errors=True)
                shutil.move(str(backup_path), str(current_app))
            raise

    finally:
        # Always unmount the DMG
        if mount_point and mount_point.exists():
            subprocess.run(['hdiutil', 'detach', str(mount_point), '-force'],
                         capture_output=True)
