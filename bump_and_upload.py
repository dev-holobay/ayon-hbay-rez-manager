#!/usr/bin/env python
"""Bump version, commit, tag, package and upload AYON addon.

This script automates the complete workflow for releasing an AYON addon:
1. Bumps version in package.py, pyproject.toml, and client/*/version.py
2. Commits changes with version message
3. Creates git tag
4. Pushes to remote
5. Creates package using create_package.py
6. Uploads to AYON server

Requirements:
- ayon-python-api (pip install ayon-python-api)
- python-dotenv (pip install python-dotenv)
- .env file with AYON_SERVER_URL and AYON_API_KEY

Usage:
    python bump_and_upload.py              # bump patch by default
    python bump_and_upload.py --bump minor
    python bump_and_upload.py --bump major
    python bump_and_upload.py --bump patch
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import ayon_api
    from ayon_api import get_server_api_connection
except ModuleNotFoundError:
    print("ERROR: ayon-python-api not installed. Run: pip install ayon-python-api")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    logging.warning("dotenv not installed, relying on environment variables")


def setup_logging(debug=False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("bump_and_upload")


def parse_version(version_str):
    """Parse semantic version string into (major, minor, patch)."""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    return tuple(map(int, match.groups()))


def bump_version(version_str, bump_type="patch"):
    """Bump semantic version."""
    major, minor, patch = parse_version(version_str)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def update_file_version(file_path, old_version, new_version, log):
    """Update version in a file using regex."""
    if not file_path.exists():
        log.warning(f"File not found, skipping: {file_path}")
        return False

    content = file_path.read_text(encoding='utf-8')

    # Different patterns for different file types
    if file_path.name == "package.py":
        pattern = rf'(version\s*=\s*["\']){re.escape(old_version)}(["\'])'
        replacement = rf'\g<1>{new_version}\g<2>'
    elif file_path.name == "pyproject.toml":
        pattern = rf'(version\s*=\s*["\']){re.escape(old_version)}(["\'])'
        replacement = rf'\g<1>{new_version}\g<2>'
    elif file_path.name == "version.py":
        pattern = rf'(__version__\s*=\s*["\']){re.escape(old_version)}(["\'])'
        replacement = rf'\g<1>{new_version}\g<2>'
    else:
        log.warning(f"Unknown file type: {file_path}")
        return False

    new_content, count = re.subn(pattern, replacement, content)

    if count == 0:
        log.warning(f"Version not found in {file_path}")
        return False

    file_path.write_text(new_content, encoding='utf-8')
    log.info(f"✓ Updated {file_path.relative_to(Path.cwd())}")
    return True


def get_current_version(repo_root):
    """Get current version from package.py."""
    package_py = repo_root / "package.py"
    if not package_py.exists():
        raise FileNotFoundError("package.py not found")

    content = {}
    with open(package_py) as f:
        exec(f.read(), content)

    return content.get("version"), content.get("name")


def find_client_version_py(repo_root, addon_name):
    """Find the version.py file in client directory."""
    # Convert addon name format: hbay_pipe_manager
    client_dir = repo_root / "client" / addon_name
    version_py = client_dir / "version.py"

    if version_py.exists():
        return version_py

    return None


def run_command(cmd, log, check=True):
    """Run shell command and return result."""
    log.debug(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode != 0 and check:
        log.error(f"Command failed: {' '.join(cmd)}")
        log.error(f"Error: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Bump version and upload AYON addon"
    )
    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Version bump type (default: patch)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Skip git push (for testing)"
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip upload to server (for testing)"
    )

    args = parser.parse_args()
    log = setup_logging(args.debug)

    repo_root = Path.cwd()
    log.info(f"Repository: {repo_root}")

    # Get current version and addon name
    try:
        current_version, addon_name = get_current_version(repo_root)
        log.info(f"Current version: {current_version}")
    except Exception as e:
        log.error(f"Failed to read current version: {e}")
        return 1

    # Calculate new version
    new_version = bump_version(current_version, args.bump)
    log.info(f"New version: {new_version} ({args.bump} bump)")

    # Confirm with user
    response = input(f"\nBump version {current_version} → {new_version}? [y/N]: ")
    if response.lower() != 'y':
        log.info("Aborted by user")
        return 0

    # Update version in all files
    log.info("\n=== Updating version files ===")
    files_to_update = [
        repo_root / "package.py",
        repo_root / "pyproject.toml",
    ]

    # Find and add client version.py
    client_version = find_client_version_py(repo_root, addon_name)
    if client_version:
        files_to_update.append(client_version)

    updated_files = []
    for file_path in files_to_update:
        if update_file_version(file_path, current_version, new_version, log):
            updated_files.append(file_path)

    if not updated_files:
        log.error("No files were updated!")
        return 1

    # Git operations
    log.info("\n=== Git operations ===")
    try:
        # Add files
        for file_path in updated_files:
            run_command(["git", "add", str(file_path)], log)

        # Commit
        commit_msg = f"Bump version to {new_version}"
        run_command(["git", "commit", "-m", commit_msg], log)
        log.info(f"✓ Committed: {commit_msg}")

        # Tag
        tag_name = f"v{new_version}"
        run_command(["git", "tag", "-a", tag_name, "-m", f"Version {new_version}"], log)
        log.info(f"✓ Tagged: {tag_name}")

        # Push
        if not args.skip_push:
            run_command(["git", "push"], log)
            run_command(["git", "push", "--tags"], log)
            log.info("✓ Pushed to remote")
        else:
            log.info("⊘ Skipped push (--skip-push)")

    except subprocess.CalledProcessError as e:
        log.error(f"Git operation failed: {e}")
        return 1

    # Create package
    log.info("\n=== Creating package ===")
    create_package_script = repo_root / "create_package.py"
    if not create_package_script.exists():
        log.error("create_package.py not found!")
        return 1

    try:
        result = run_command([sys.executable, str(create_package_script)], log)
        log.info("✓ Package created")
    except subprocess.CalledProcessError:
        log.error("Failed to create package")
        return 1

    # Upload to server
    if not args.skip_upload:
        log.info("\n=== Uploading to AYON server ===")

        # Check environment
        if not os.getenv("AYON_SERVER_URL") or not os.getenv("AYON_API_KEY"):
            log.error("Missing AYON_SERVER_URL or AYON_API_KEY in environment")
            log.error("Please create a .env file with these variables")
            return 1

        try:
            ayon_api.init_service()

            # Find the package zip
            package_dir = repo_root / "package"
            zip_path = package_dir / f"{addon_name}-{new_version}.zip"

            if not zip_path.exists():
                log.error(f"Package not found: {zip_path}")
                return 1

            log.info(f"Uploading: {zip_path.name}")
            response = ayon_api.upload_addon_zip(str(zip_path))
            log.info("✓ Upload successful")

            # Restart server
            server = get_server_api_connection()
            if server:
                server.trigger_server_restart()
                log.info("✓ Server restart triggered")
            else:
                log.warning("Could not trigger server restart")

        except Exception as e:
            log.error(f"Upload failed: {e}")
            return 1
    else:
        log.info("⊘ Skipped upload (--skip-upload)")

    log.info(f"\n🎉 Successfully released {addon_name} v{new_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
