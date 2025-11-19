"""
Configuration management utilities.
"""

from .video_config_manager import (
    get_video_config_path,
    get_master_config_path,
    has_video_config,
    load_video_config,
    list_configured_videos
)

__all__ = [
    "get_video_config_path",
    "get_master_config_path",
    "has_video_config",
    "load_video_config",
    "list_configured_videos"
]
