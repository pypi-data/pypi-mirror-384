#!/usr/bin/env python3
"""
Version checking utility for doc-utils.

Checks PyPI for the latest version and notifies users if an update is available.
Includes caching to avoid excessive PyPI requests.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from importlib.metadata import version as get_installed_version
from pathlib import Path
from typing import Optional, Tuple


def get_cache_dir() -> Path:
    """Get the cache directory for version check data."""
    # Use XDG_CACHE_HOME if set, otherwise ~/.cache
    cache_home = os.environ.get('XDG_CACHE_HOME')
    if cache_home:
        cache_dir = Path(cache_home) / 'doc-utils'
    else:
        cache_dir = Path.home() / '.cache' / 'doc-utils'

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cache_file() -> Path:
    """Get the cache file path."""
    return get_cache_dir() / 'version_check.json'


def read_cache() -> Optional[dict]:
    """Read version check cache."""
    cache_file = get_cache_file()
    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
            # Check if cache is still valid (24 hours)
            last_check = datetime.fromisoformat(data['last_check'])
            if datetime.now() - last_check < timedelta(hours=24):
                return data
    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    return None


def write_cache(latest_version: str, current_version: str):
    """Write version check cache."""
    cache_file = get_cache_file()
    data = {
        'last_check': datetime.now().isoformat(),
        'latest_version': latest_version,
        'current_version': current_version,
    }

    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    except Exception:
        # Silently fail if we can't write cache
        pass


def fetch_latest_version() -> Optional[str]:
    """Fetch the latest version from PyPI."""
    try:
        # Use PyPI JSON API
        url = 'https://pypi.org/pypi/rolfedh-doc-utils/json'
        with urllib.request.urlopen(url, timeout=2) as response:
            data = json.loads(response.read())
            return data['info']['version']
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError):
        # Silently fail if we can't reach PyPI
        return None


def parse_version(version_str: str) -> Tuple[int, ...]:
    """Parse version string into tuple of integers for comparison."""
    try:
        # Remove any pre-release or dev suffixes
        version_str = version_str.split('+')[0].split('-')[0]
        return tuple(int(x) for x in version_str.split('.'))
    except (ValueError, AttributeError):
        return (0,)


def check_for_update(force_check: bool = False) -> Optional[str]:
    """
    Check if a newer version is available.

    Args:
        force_check: If True, bypass cache and always check PyPI

    Returns:
        The latest version string if an update is available, None otherwise
    """
    try:
        current_version = get_installed_version('rolfedh-doc-utils')
    except Exception:
        # Can't determine installed version
        return None

    # Check cache first (unless forced)
    if not force_check:
        cache_data = read_cache()
        if cache_data:
            latest_version = cache_data['latest_version']
            # Only notify if there's a newer version
            if parse_version(latest_version) > parse_version(current_version):
                return latest_version
            return None

    # Fetch from PyPI
    latest_version = fetch_latest_version()
    if not latest_version:
        return None

    # Cache the result
    write_cache(latest_version, current_version)

    # Check if update is available
    if parse_version(latest_version) > parse_version(current_version):
        return latest_version

    return None


def detect_install_method() -> str:
    """
    Detect how the package was installed.

    Returns:
        'pipx', 'pip', or 'unknown'
    """
    # Check if running from pipx venv
    if 'pipx' in sys.prefix:
        return 'pipx'

    # Check PIPX_HOME environment variable
    pipx_home = os.environ.get('PIPX_HOME') or os.path.join(Path.home(), '.local', 'pipx')
    if pipx_home and str(Path(sys.prefix)).startswith(str(Path(pipx_home))):
        return 'pipx'

    # Default to pip
    return 'pip'


def show_update_notification(latest_version: str, current_version: str = None):
    """Show update notification to user."""
    if not current_version:
        try:
            current_version = get_installed_version('rolfedh-doc-utils')
        except Exception:
            current_version = 'unknown'

    # Detect installation method and recommend appropriate upgrade command
    install_method = detect_install_method()

    # Use stderr to avoid interfering with tool output
    print(f"\n📦 Update available: {current_version} → {latest_version}", file=sys.stderr)

    if install_method == 'pipx':
        print(f"   Run: pipx upgrade rolfedh-doc-utils", file=sys.stderr)
    else:
        print(f"   Run: pip install --upgrade rolfedh-doc-utils", file=sys.stderr)

    print("", file=sys.stderr)


def check_version_on_startup():
    """
    Check for updates on tool startup.

    This should be called early in the main() function of each CLI tool.
    It runs asynchronously and won't block the tool execution.
    """
    # Skip version check in certain conditions
    if any([
        os.environ.get('DOC_UTILS_NO_VERSION_CHECK'),  # User opt-out
        os.environ.get('CI'),  # Running in CI
        not sys.stderr.isatty(),  # Not running in terminal
    ]):
        return

    try:
        latest_version = check_for_update()
        if latest_version:
            show_update_notification(latest_version)
    except Exception:
        # Never let version checking break the tool
        pass


def disable_version_check():
    """
    Instructions for disabling version check.

    Users can disable by setting DOC_UTILS_NO_VERSION_CHECK environment variable.
    """
    print("To disable version checking, set the environment variable:")
    print("  export DOC_UTILS_NO_VERSION_CHECK=1")
    print("\nOr add it to your shell configuration file.")


if __name__ == "__main__":
    # For testing/debugging
    import argparse
    parser = argparse.ArgumentParser(description="Check for doc-utils updates")
    parser.add_argument('--force', action='store_true', help='Force check (bypass cache)')
    parser.add_argument('--disable-instructions', action='store_true',
                       help='Show instructions for disabling version check')
    args = parser.parse_args()

    if args.disable_instructions:
        disable_version_check()
    else:
        latest = check_for_update(force_check=args.force)
        if latest:
            show_update_notification(latest)
        else:
            print("You are running the latest version!")