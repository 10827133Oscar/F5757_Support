#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-Use Tool Hook: Desktop Notification for Tracked Files

This hook monitors file modifications by Claude Code and sends desktop notifications
when tracked files are modified.
"""

import sys
import json
import os
from pathlib import Path
from notifypy import Notify


# 追蹤檔案清單 - 可根據需求修改
# 預設清單（如果 tracked_files.txt 不存在或讀取失敗時使用）
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
            print(f"讀取追蹤檔案清單失敗，使用預設清單：{e}", file=sys.stderr)
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
    Send desktop notification for file modification.

    Args:
        file_path: The path of the modified file
        tool_name: The tool used to modify the file (Edit/Write)
    """
    if not file_path:
        return

    notification = Notify()
    notification.title = "Claude Code 檔案修改通知"
    notification.message = f"已修改追蹤檔案：{Path(file_path).name}\n工具：{tool_name}"
    # notification.icon = ""  # 可以設置自定義圖標路徑

    try:
        notification.send(block=False)
    except Exception as e:
        print(f"發送通知失敗：{e}", file=sys.stderr)


def main():
    """
    Main function to process hook data and send notifications.
    """
    try:
        # Load tracked files list
        tracked_files = load_tracked_files()

        # Read JSON data from stdin
        hook_data = json.load(sys.stdin)

        # Extract relevant information
        tool_name = hook_data.get("tool_name", "")
        tool_input = hook_data.get("tool_input", {})
        tool_response = hook_data.get("tool_response", {})
        cwd = hook_data.get("cwd", "")

        # Get file path from tool_input or tool_response
        file_path = None

        if "file_path" in tool_input:
            file_path = tool_input["file_path"]
        elif "filePath" in tool_response:
            file_path = tool_response["filePath"]

        # If no file path found, exit
        if not file_path:
            return

        # Check if the file is tracked
        if is_tracked_file(file_path, cwd, tracked_files):
            send_notification(file_path, tool_name)
            print(f"✓ 已發送通知：{Path(file_path).name}", file=sys.stderr)

    except json.JSONDecodeError as e:
        print(f"JSON 解析錯誤：{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Hook 執行錯誤：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
