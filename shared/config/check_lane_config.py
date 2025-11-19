#!/usr/bin/env python3
"""
Quick Lane Config Checker

This script loads a video frame and shows the current lane configuration
so you can verify if it covers the entire area you want to monitor.
"""

import cv2
import numpy as np
import json
import os
import sys
from video_config_manager import get_video_config_path, has_video_config


def visualize_lane_config(video_path, config_path=None):
    """Visualize the current lane configuration on the video"""

    # If no config path specified, use video-specific config
    if config_path is None:
        if not has_video_config(video_path):
            print(
                f"Error: No configuration found for {os.path.basename(video_path)}")
            print(
                f"Create one using: python lane_config_tool.py --video {video_path}")
            return
        config_path = get_video_config_path(video_path)

    # Load config
    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}")
        return

    with open(config_path, 'r') as f:
        config = json.load(f)

    lane_points = config.get('lane_points', [])
    print(f"Loaded {len(lane_points)} lane points:")
    for i, point in enumerate(lane_points):
        print(f"  Point {i+1}: X={point[0]}, Y={point[1]}")

    # Load video frame
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"Error: Could not read video: {video_path}")
        return

    h, w = frame.shape[:2]
    print(f"\nVideo dimensions: {w}x{h}")
    print(
        f"\nLane Y-range: {min(p[1] for p in lane_points)} to {max(p[1] for p in lane_points)}")
    print(
        f"Lane covers: {((max(p[1] for p in lane_points) - min(p[1] for p in lane_points)) / h * 100):.1f}% of frame height")

    # Draw the lane
    lane_polygon = np.array(lane_points, dtype=np.int32)

    # Create visualization
    display = frame.copy()

    # Draw filled polygon with transparency
    overlay = display.copy()
    cv2.fillPoly(overlay, [lane_polygon], (0, 255, 0))
    cv2.addWeighted(overlay, 0.3, display, 0.7, 0, display)

    # Draw polygon outline
    cv2.polylines(display, [lane_polygon], True, (0, 255, 0), 2)

    # Draw points with numbers
    for i, point in enumerate(lane_points):
        cv2.circle(display, tuple(point), 5, (0, 255, 255), -1)
        cv2.putText(display, str(i+1), (point[0]-10, point[1]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Draw reference lines
    min_y = min(p[1] for p in lane_points)
    max_y = max(p[1] for p in lane_points)

    cv2.line(display, (0, min_y), (w, min_y), (255, 0, 0), 1)
    cv2.putText(display, f"Top of lane (Y={min_y})", (10, min_y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    cv2.line(display, (0, max_y), (w, max_y), (255, 0, 0), 1)
    cv2.putText(display, f"Bottom of lane (Y={max_y})", (10, max_y+20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # Add info panel
    info_text = [
        "Lane Configuration Visualization",
        f"Points: {len(lane_points)}",
        f"Y-range: {min_y} to {max_y}",
        f"Coverage: {((max_y - min_y) / h * 100):.1f}% of height",
        "",
        "Press any key to close"
    ]

    y_pos = 30
    for text in info_text:
        cv2.putText(display, text, (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_pos += 25

    # Show the visualization
    cv2.namedWindow("Lane Configuration Check", cv2.WINDOW_NORMAL)
    cv2.imshow("Lane Configuration Check", display)

    print("\n" + "="*60)
    print("VISUAL CHECK:")
    print("="*60)
    print("- Green area = where vehicles WILL be detected")
    print("- Outside green area = vehicles IGNORED")
    print("- If the green area doesn't cover the whole road,")
    print("  you need to reconfigure the lane!")
    print("="*60)
    print("\nTo reconfigure:")
    print(f"  python lane_config_tool.py --video {video_path}")
    print("="*60)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Save visualization
    output_path = "config/lane_config_check.jpg"
    cv2.imwrite(output_path, display)
    print(f"\nVisualization saved to: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Check lane configuration for a video")
    parser.add_argument("--video", type=str, help="Path to video file")
    parser.add_argument("--config", type=str,
                        help="Path to specific config file (optional)")
    args = parser.parse_args()

    if args.video:
        video_path = args.video
    elif len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        video_path = sys.argv[1]
    else:
        video_path = "videos/test.mp4"
        print(f"Using default video: {video_path}")

    visualize_lane_config(video_path, args.config if args else None)
