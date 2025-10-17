"""Check for newer versions on PyPI."""

import json
import time
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError


def get_pypi_version(package_name: str, timeout: float = 2.0) -> Optional[str]:
    """
    Fetch the latest version from PyPI.

    Args:
        package_name: Name of the package on PyPI
        timeout: Request timeout in seconds

    Returns:
        Latest version string or None if fetch fails
    """
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        req = Request(url, headers={"User-Agent": "bscli-version-checker"})
        with urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode())
            return data["info"]["version"]
    except (URLError, KeyError, json.JSONDecodeError, TimeoutError):
        return None


def parse_version(version: str) -> tuple:
    """Parse version string into comparable tuple."""
    try:
        return tuple(int(x) for x in version.split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def is_newer_version(current: str, latest: str) -> bool:
    """Check if latest version is newer than current."""
    return parse_version(latest) > parse_version(current)


def should_check_version(cache_file: Path, check_interval: int = 86400) -> bool:
    """
    Determine if we should check for updates.

    Args:
        cache_file: Path to cache file storing last check time
        check_interval: Minimum seconds between checks (default: 24 hours)

    Returns:
        True if check should be performed
    """
    if not cache_file.exists():
        return True

    try:
        last_check = float(cache_file.read_text().strip())
        return (time.time() - last_check) > check_interval
    except (ValueError, OSError):
        return True


def update_check_cache(cache_file: Path) -> None:
    """Update the last check timestamp."""
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(str(time.time()))
    except OSError:
        pass


def check_for_updates(
    current_version: str, package_name: str, config_dir: Path
) -> None:
    """
    Check for package updates and notify user if newer version exists.

    Args:
        current_version: Current installed version
        package_name: Name of the package on PyPI
        config_dir: Configuration directory for cache storage
    """
    cache_file = config_dir / ".version_check"

    # Only check once per day
    if not should_check_version(cache_file):
        return

    latest_version = get_pypi_version(package_name)
    update_check_cache(cache_file)

    if latest_version and is_newer_version(current_version, latest_version):
        print(
            f"🆕 A new version of {package_name} is available: {latest_version} (current: {current_version})"
        )
        print(f"💡 Update with: pip install --upgrade {package_name}\n")
