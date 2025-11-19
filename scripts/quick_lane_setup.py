#!/usr/bin/env python3
"""
Quick Start Example for Lane-Based Traffic Detection

This script demonstrates the two-step process:
1. Configure lane using the interactive tool
2. Run traffic detection with lane filtering
"""

import os
import sys
import subprocess


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def main():
    # Check if a video file was provided
    if len(sys.argv) < 2:
        print("Usage: python quick_lane_setup.py <video_file>")
        print("\nExample:")
        print("  python quick_lane_setup.py rushing.mp4")
        print("  python quick_lane_setup.py Video_2.mp4")
        sys.exit(1)

    video_file = sys.argv[1]

    # Check if video file exists
    if not os.path.exists(video_file):
        print(f"Error: Video file not found: {video_file}")
        sys.exit(1)

    print_header("Lane-Based Traffic Detection - Quick Setup")

    print("This script will guide you through:")
    print("  1. Configuring the lane boundaries")
    print("  2. Running optimized traffic detection")
    print()

    # Step 1: Configure lane
    print_header("STEP 1: Configure Lane Boundaries")
    print("An interactive window will open where you can:")
    print("  • Left-click to add lane boundary points")
    print("  • Right-click to remove the last point")
    print("  • Press ESC to save and continue")
    print("  • Press Q to quit without saving")
    print()

    input("Press Enter to start lane configuration...")

    config_dir = "config"
    cmd_config = f'python lane_config_tool.py --video "{video_file}" --config-dir "{config_dir}"'

    print(f"\nRunning: {cmd_config}")
    result = subprocess.run(cmd_config, shell=True)

    if result.returncode != 0:
        print("\nLane configuration was cancelled or failed.")
        print("You can run it manually later with:")
        print(f'  python lane_config_tool.py --video "{video_file}"')
        sys.exit(1)

    # Check if config was created (video-specific)
    from video_config_manager import has_video_config, get_video_config_path

    if not has_video_config(video_file, config_dir):
        print(f"\nWarning: Configuration not found for this video")
        print("Lane filtering will be disabled.")
        print()

        response = input("Continue without lane filtering? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        config_path = get_video_config_path(video_file, config_dir)
        print(f"\n✓ Lane configuration saved to: {config_path}")
        print(
            f"✓ Preview image saved to: {config_path.replace('.json', '_preview.jpg')}")

    # Step 2: Run detection
    print_header("STEP 2: Run Traffic Detection")

    output_file = video_file.replace('.mp4', '_tracked.mp4')

    print("The system will now:")
    print("  • Load the configured lane boundaries")
    print("  • Filter vehicles to only those in the lane")
    print("  • Track only vehicles moving towards camera")
    print("  • Display real-time results")
    print()
    print(f"Output video will be saved to: {output_file}")
    print()

    response = input("Start traffic detection? (y/n): ")
    if response.lower() != 'y':
        print("\nYou can run detection manually later with:")
        print(
            f'  python final_tracking_onnx.py --source "{video_file}" --output "{output_file}"')
        sys.exit(0)

    cmd_detect = f'python final_tracking_onnx.py --source "{video_file}" --output "{output_file}" --lane-config "{config_path}"'

    print(f"\nRunning: {cmd_detect}")
    print("\nControls during detection:")
    print("  • Q: Quit")
    print("  • R: Reset vehicle count")
    print("  • S: Save screenshot")
    print()

    subprocess.run(cmd_detect, shell=True)

    print_header("Complete!")
    print(f"✓ Processed video: {video_file}")

    if os.path.exists(output_file):
        print(f"✓ Output saved to: {output_file}")

    if os.path.exists(config_path):
        print(f"✓ Lane config: {config_path}")

    print("\nTo process another video with the same lane configuration:")
    print(
        f'  python final_tracking_onnx.py --source "other_video.mp4" --lane-config "{config_path}"')
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
