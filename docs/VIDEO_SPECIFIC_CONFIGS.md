# Video-Specific Lane Configuration System

## Overview

The traffic control system now supports **video-specific lane configurations**. This means each video can have its own unique lane configuration, and the system will automatically use the correct configuration for each video.

## Features

### 1. Video-Specific Configuration Storage

- Each video gets its own configuration file: `config/lane_config_<video_name>.json`
- A master configuration file tracks all video-config mappings: `config/lane_configs_master.json`
- Old single-config system is replaced with a multi-config system

### 2. Automatic Configuration Detection

When you run traffic detection on a video:

- The system checks if a configuration exists for that specific video
- If found, it automatically loads the correct configuration
- If not found, you get prompted with options

### 3. User-Friendly Prompts

When no configuration exists for a video, you'll see:

```
============================================================
No lane configuration found for: your_video.mp4
============================================================

Options:
  1. Configure lane now (recommended)
  2. Continue without lane filtering
  3. Quit

Enter your choice (1/2/3):
```

## Usage

### Creating a Lane Configuration for a Video

**Option 1: Using the lane config tool directly**

```bash
python lane_config_tool.py --video videos/your_video.mp4
```

**Option 2: Let the system prompt you**

```bash
python final_tracking_onnx.py --source videos/your_video.mp4
# System will prompt you to configure if no config exists
```

### Running Traffic Detection

```bash
# Run with automatic video-specific config
python final_tracking_onnx.py --source videos/video1.mp4

# Run a different video (uses its own config)
python final_tracking_onnx.py --source videos/video2.mp4

# Run without any lane filtering
python final_tracking_onnx.py --source videos/video3.mp4 --no-filter
```

### Checking a Video's Configuration

```bash
# Check if a video has a configuration
python check_lane_config.py --video videos/your_video.mp4

# Or use the older syntax
python check_lane_config.py videos/your_video.mp4
```

### Quick Setup (Configuration + Detection)

```bash
python quick_lane_setup.py videos/your_video.mp4
```

## File Structure

```
config/
├── lane_configs_master.json          # Master mapping file
├── lane_config_Delhi2.json           # Config for Delhi2.mp4
├── lane_config_Delhi2_preview.jpg    # Preview for Delhi2.mp4
├── lane_config_test.json             # Config for test.mp4
├── lane_config_test_preview.jpg      # Preview for test.mp4
└── ...
```

### Master Configuration Format

```json
{
  "Delhi2.mp4": {
    "config_file": "config/lane_config_Delhi2.json",
    "video_path": "videos/Delhi2.mp4",
    "last_updated": "2025-10-09 12:30:45"
  },
  "test.mp4": {
    "config_file": "config/lane_config_test.json",
    "video_path": "videos/test.mp4",
    "last_updated": "2025-10-09 13:15:22"
  }
}
```

## Benefits

1. **No Configuration Conflicts**: Each video has its own configuration
2. **Easy Management**: Clear naming shows which config belongs to which video
3. **User-Friendly**: Prompts guide you when configuration is missing
4. **Backward Compatible**: Old commands still work with new system
5. **Flexible**: Can still disable filtering with `--no-filter`

## Migration from Old System

If you have an existing `config/lane_config.json`:

1. Rename it to match your video (e.g., `lane_config_Delhi2.json`)
2. Or simply reconfigure your videos using the new system
3. The old file won't interfere with the new system

## Troubleshooting

### "No configuration found" message

- Run: `python lane_config_tool.py --video your_video.mp4`
- Or choose option 1 when prompted

### Want to reconfigure a video

- Just run the lane config tool again with the same video
- It will overwrite the existing configuration

### Want to see all configured videos

```python
from video_config_manager import list_configured_videos
videos = list_configured_videos()
for video_name, config_path in videos.items():
    print(f"{video_name} -> {config_path}")
```

## API Reference

The `video_config_manager.py` module provides utility functions:

- `get_video_config_path(video_source, config_dir)` - Get config path for a video
- `has_video_config(video_source, config_dir)` - Check if config exists
- `load_video_config(video_source, config_dir)` - Load video's configuration
- `list_configured_videos(config_dir)` - List all configured videos
- `prompt_user_for_config(video_source)` - Interactive prompt for missing config
- `launch_lane_config_tool(video_source, config_dir)` - Launch config tool programmatically
