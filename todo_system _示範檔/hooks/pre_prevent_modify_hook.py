#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-Use Tool Hook: Prevent Modification of Tracked Files

This hook prevents Claude Code from modifying tracked files before the tool is executed.
When a tracked file is about to be modified, it:
1. Blocks the modification
2. Sends a desktop notification
3. Returns exit code 2
4. Outputs an error message in English
"""

import sys
import json
import os
from pathlib import Path
from notifypy import Notify


# Tracked files list - modify as needed
# Default list (used if tracked_files.txt doesn't exist or fails to load)
DEFAULT_TRACKED_FILES = [
    "main.py",
    "src/todo_manager.py",
    "pyproject.toml",
    "README.md",
]


def load_tracked_files() -> list[str]:
    """
    Load tracked files from configuration file or use default list.

    Returns:
        List of file paths to track
    """
    config_file = Path(__file__).parent / "tracked_files.txt"

    if config_file.exists():
        try:
            tracked_files = []
            with open(config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        tracked_files.append(line)
            return tracked_files if tracked_files else DEFAULT_TRACKED_FILES
        except Exception as e:
            print(f"Error: Failed to load tracked files list, using defaults: {e}", file=sys.stderr)
            return DEFAULT_TRACKED_FILES
    else:
        return DEFAULT_TRACKED_FILES


def normalize_path(file_path: str, cwd: str) -> str:
    """
    Normalize file path to relative path for comparison.

    Args:
        file_path: The file path from the hook data
        cwd: Current working directory

    Returns:
        Normalized relative path
    """
    try:
        # Convert to Path object
        path = Path(file_path)
        cwd_path = Path(cwd)

        # Try to get relative path
        if path.is_absolute():
            try:
                relative_path = path.relative_to(cwd_path)
                return str(relative_path).replace('\\', '/')
            except ValueError:
                # If path is not relative to cwd, use the filename
                return path.name
        else:
            return str(path).replace('\\', '/')
    except Exception:
        # Fallback to the original path
        return file_path


def is_tracked_file(file_path: str, cwd: str, tracked_files: list[str]) -> bool:
    """
    Check if the file is in the tracked files list.

    Args:
        file_path: The file path to check
        cwd: Current working directory
        tracked_files: List of tracked file paths

    Returns:
        True if the file is tracked, False otherwise
    """
    normalized_path = normalize_path(file_path, cwd)

    # Check exact match or filename match
    for tracked in tracked_files:
        tracked_normalized = tracked.replace('\\', '/')

        # Exact match
        if normalized_path == tracked_normalized:
            return True

        # Filename match
        if Path(normalized_path).name == Path(tracked_normalized).name:
            return True

        # Check if the path ends with the tracked path (for absolute paths)
        if normalized_path.endswith(tracked_normalized):
            return True

    return False


def send_notification(file_path: str, tool_name: str):
    """
    Send desktop notification for blocked file modification.

    Args:
        file_path: The path of the file that was blocked
        tool_name: The tool that was blocked (Edit/Write)
    """
    if not file_path:
        return

    notification = Notify()
    notification.title = "Claude Code - Modification Blocked"
    notification.message = f"Blocked modification of tracked file:\n{Path(file_path).name}\nTool: {tool_name}"
    # notification.icon = ""  # You can set a custom icon path

    try:
        notification.send(block=False)
    except Exception as e:
        print(f"Error: Failed to send notification: {e}", file=sys.stderr)


def main():
    """
    Main function to process hook data and block file modifications.
    """
    try:
        # Load tracked files list
        tracked_files = load_tracked_files()

        # Read JSON data from stdin
        hook_data = json.load(sys.stdin)

        # Extract relevant information
        tool_name = hook_data.get("tool_name", "")
        tool_input = hook_data.get("tool_input", {})
        cwd = hook_data.get("cwd", "")

        # Only check for file modification tools
        if tool_name not in ["Edit", "Write", "NotebookEdit"]:
            return

        # Get file path from tool_input
        file_path = None

        if "file_path" in tool_input:
            file_path = tool_input["file_path"]
        elif "notebook_path" in tool_input:
            file_path = tool_input["notebook_path"]

        # If no file path found, exit
        if not file_path:
            return

        # Check if the file is tracked
        if is_tracked_file(file_path, cwd, tracked_files):
            # Send notification
            send_notification(file_path, tool_name)

            # Output error message in English
            print(f"Error: Modification of tracked file '{Path(file_path).name}' is blocked.", file=sys.stderr)
            print(f"Error: This file is in the tracked files list and cannot be modified.", file=sys.stderr)
            print(f"Error: To modify this file, please remove it from the tracked files list in 'hooks/tracked_files.txt'.", file=sys.stderr)

            # Exit with code 2 to block the tool execution
            sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: JSON parsing error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Hook execution error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
