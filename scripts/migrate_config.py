#!/usr/bin/env python3
"""
Migrate old lane_config.json to new video-specific system
"""

import os
import json
import shutil
from datetime import datetime


def migrate_old_config():
    """Migrate the old single config file to video-specific format"""
    old_config_path = "config/lane_config.json"

    if not os.path.exists(old_config_path):
        print("No old configuration file found. Nothing to migrate.")
        return

    print("="*70)
    print("Migrating Old Configuration to Video-Specific System")
    print("="*70)

    # Load old config
    try:
        with open(old_config_path, 'r') as f:
            old_config = json.load(f)
    except Exception as e:
        print(f"Error reading old config: {e}")
        return

    # Get video source
    video_source = old_config.get('video_source', '')
    if not video_source:
        print("Error: Old config doesn't specify video_source")
        return

    video_name = os.path.basename(video_source)
    print(f"\nFound configuration for: {video_name}")
    print(f"Original file: {old_config_path}")

    # Create new config filename
    video_basename = os.path.splitext(video_name)[0]
    new_config_path = f"config/lane_config_{video_basename}.json"

    print(f"New file: {new_config_path}")

    # Check if new config already exists
    if os.path.exists(new_config_path):
        response = input(
            f"\n{new_config_path} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return

    # Copy to new location
    try:
        shutil.copy2(old_config_path, new_config_path)
        print(f"✓ Created: {new_config_path}")
    except Exception as e:
        print(f"✗ Error creating new config: {e}")
        return

    # Migrate preview image if it exists
    old_preview = "config/lane_config_preview.jpg"
    new_preview = f"config/lane_config_{video_basename}_preview.jpg"

    if os.path.exists(old_preview):
        try:
            shutil.copy2(old_preview, new_preview)
            print(f"✓ Created: {new_preview}")
        except Exception as e:
            print(f"⚠ Warning: Could not copy preview image: {e}")

    # Update master config
    master_config_path = "config/lane_configs_master.json"
    master_config = {}

    if os.path.exists(master_config_path):
        try:
            with open(master_config_path, 'r') as f:
                master_config = json.load(f)
        except:
            master_config = {}

    # Add entry
    master_config[video_name] = {
        "config_file": new_config_path,
        "video_path": video_source,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "migrated_from": old_config_path
    }

    # Save master config
    try:
        with open(master_config_path, 'w') as f:
            json.dump(master_config, f, indent=4)
        print(f"✓ Updated: {master_config_path}")
    except Exception as e:
        print(f"✗ Error updating master config: {e}")
        return

    # Backup old config
    backup_path = old_config_path + ".backup"
    try:
        shutil.copy2(old_config_path, backup_path)
        print(f"\n✓ Backup created: {backup_path}")
    except Exception as e:
        print(f"⚠ Warning: Could not create backup: {e}")

    print("\n" + "="*70)
    print("Migration Summary")
    print("="*70)
    print(f"✓ Configuration migrated successfully")
    print(f"✓ Video: {video_name}")
    print(f"✓ New config: {new_config_path}")
    print(f"\nThe old config file (lane_config.json) has been backed up.")
    print("You can safely delete the old files if everything works correctly.")
    print("\nTo test the migration:")
    print(f"  python final_tracking_onnx.py --source {video_source}")
    print("="*70)


if __name__ == "__main__":
    migrate_old_config()
