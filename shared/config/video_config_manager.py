#!/usr/bin/env python3
"""
Video Configuration Manager

Utility functions for managing video-specific lane configurations.
"""

import os
import json
from typing import Optional, Dict
from pathlib import Path


def _normalize_video_path(video_source: str) -> str:
    """
    Normalize video path to just the filename with extension.

    Examples:
        "videos/Delhi2.mp4" -> "Delhi2.mp4"
        "Delhi2.mp4" -> "Delhi2.mp4"
        "./videos/Delhi2.mp4" -> "Delhi2.mp4"
    """
    return os.path.basename(video_source)


def _get_video_name_for_config(video_source: str) -> str:
    """
    Get video name without extension for config file naming.

    Examples:
        "videos/Delhi2.mp4" -> "Delhi2"
        "Delhi2.mp4" -> "Delhi2"
    """
    video_name = _normalize_video_path(video_source)
    return os.path.splitext(video_name)[0]


def get_video_config_path(video_source: str, config_dir: str = "config") -> Optional[str]:
    """
    Get the configuration file path for a specific video.

    Checks both direct config files and master config registry.

    Args:
        video_source: Path to the video file (can be relative or absolute)
        config_dir: Directory containing configuration files

    Returns:
        Path to the video-specific configuration file, or None if not found
    """
    video_name = _get_video_name_for_config(video_source)
    direct_config_path = os.path.join(
        config_dir, f"lane_config_{video_name}.json")

    # First check direct config file
    if os.path.exists(direct_config_path):
        return direct_config_path

    # Then check master config
    master_config_path = get_master_config_path(config_dir)
    if os.path.exists(master_config_path):
        try:
            with open(master_config_path, 'r') as f:
                master_config = json.load(f)

            # Check with normalized video name (with extension)
            normalized_name = _normalize_video_path(video_source)
            if normalized_name in master_config:
                config_file = master_config[normalized_name].get('config_file')
                if config_file:
                    # Normalize path separators for cross-platform compatibility
                    config_file = config_file.replace('\\', os.sep)
                    if os.path.exists(config_file):
                        return config_file
        except Exception as e:
            pass

    return None


def get_master_config_path(config_dir: str = "config") -> str:
    """
    Get the path to the master configuration file.

    Args:
        config_dir: Directory containing configuration files

    Returns:
        Path to the master configuration file
    """
    return os.path.join(config_dir, "lane_configs_master.json")


def has_video_config(video_source: str, config_dir: str = "config") -> bool:
    """
    Check if a configuration exists for a specific video.

    Args:
        video_source: Path to the video file (can be relative or absolute)
        config_dir: Directory containing configuration files

    Returns:
        True if configuration exists, False otherwise
    """
    # Check direct config file
    config_path = get_video_config_path(video_source, config_dir)
    if config_path and os.path.exists(config_path):
        return True

    # Also check master config with normalized video name
    master_config_path = get_master_config_path(config_dir)
    if os.path.exists(master_config_path):
        try:
            with open(master_config_path, 'r') as f:
                master_config = json.load(f)

            # Check with normalized video name (with extension)
            normalized_name = _normalize_video_path(video_source)
            if normalized_name in master_config:
                # Verify the referenced config file exists
                config_file = master_config[normalized_name].get('config_file')
                if config_file:
                    # Normalize path separators for cross-platform compatibility
                    config_file = config_file.replace('\\', os.sep)
                    if os.path.exists(config_file):
                        return True
        except Exception as e:
            pass

    return False


def load_video_config(video_source: str, config_dir: str = "config") -> Optional[Dict]:
    """
    Load the configuration for a specific video.

    Args:
        video_source: Path to the video file
        config_dir: Directory containing configuration files

    Returns:
        Configuration dictionary if found, None otherwise
    """
    config_path = get_video_config_path(video_source, config_dir)

    if not os.path.exists(config_path):
        return None

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}")
        return None


def list_configured_videos(config_dir: str = "config") -> Dict[str, str]:
    """
    List all videos that have configurations.

    Args:
        config_dir: Directory containing configuration files

    Returns:
        Dictionary mapping video names to their config file paths
    """
    master_config_path = get_master_config_path(config_dir)

    if not os.path.exists(master_config_path):
        return {}

    try:
        with open(master_config_path, 'r') as f:
            master_config = json.load(f)
        return {video: data['config_file'] for video, data in master_config.items()}
    except Exception as e:
        print(f"Error loading master configuration: {e}")
        return {}


def prompt_user_for_config(video_source: str) -> str:
    """
    Prompt user to configure lane or continue without filtering.

    Args:
        video_source: Path to the video file

    Returns:
        User's choice: 'config', 'skip', or 'quit'
    """
    video_name = os.path.basename(video_source)

    print("\n" + "="*60)
    print(f"No lane configuration found for: {video_name}")
    print("="*60)
    print("\nOptions:")
    print("  1. Configure lane now (recommended)")
    print("  2. Continue without lane filtering")
    print("  3. Quit")
    print()

    while True:
        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == '1':
            return 'config'
        elif choice == '2':
            return 'skip'
        elif choice == '3':
            return 'quit'
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def launch_lane_config_tool(video_source: str, config_dir: str = "config") -> bool:
    """
    Launch the lane configuration tool for a video.

    Args:
        video_source: Path to the video file
        config_dir: Directory to save configuration files

    Returns:
        True if configuration was successful, False otherwise
    """
    import subprocess
    import sys

    try:
        # Get the correct path to lane_config_tool.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        tool_path = os.path.join(current_dir, "lane_config_tool.py")

        # Launch the lane configuration tool
        cmd = [sys.executable, tool_path,
               "--video", video_source, "--config-dir", config_dir]
        result = subprocess.run(cmd, check=True)

        # Check if configuration was created
        return has_video_config(video_source, config_dir)
    except subprocess.CalledProcessError:
        print("Lane configuration was cancelled or failed.")
        return False
    except Exception as e:
        print(f"Error launching lane configuration tool: {e}")
        return False
