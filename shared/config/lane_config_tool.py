#!/usr/bin/env python3
"""
Lane Configuration Tool

Interactive tool for selecting lane points on a video frame.
Users can click to define lane boundaries, and the configuration is saved for optimized vehicle detection.
"""

import cv2
import numpy as np
import json
import argparse
import os
from pathlib import Path
from datetime import datetime


class LaneConfigTool:
    """Interactive lane configuration tool"""

    def __init__(self, video_source: str, config_dir: str = "config"):
        """Initialize lane configuration tool"""
        self.video_source = video_source
        self.config_dir = config_dir

        # Generate video-specific config filename
        video_name = os.path.splitext(os.path.basename(video_source))[0]
        self.video_config_file = os.path.join(
            config_dir, f"lane_config_{video_name}.json")
        self.master_config_file = os.path.join(
            config_dir, "lane_configs_master.json")

        self.lane_points = []
        self.current_frame = None
        self.original_frame = None
        self.window_name = "Lane Configuration Tool"
        self.point_radius = 5
        self.line_thickness = 2
        self.instructions_shown = True

        # Colors
        self.point_color = (0, 255, 255)  # Yellow
        self.line_color = (0, 255, 0)     # Green
        self.polygon_color = (0, 255, 0)  # Green with transparency
        self.text_color = (255, 255, 255)  # White
        self.bg_color = (0, 0, 0)         # Black

    def load_video_frame(self):
        """Load first frame from video"""
        cap = cv2.VideoCapture(self.video_source)

        if not cap.isOpened():
            raise ValueError(
                f"Could not open video source: {self.video_source}")

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError("Could not read frame from video")

        self.original_frame = frame.copy()
        self.current_frame = frame.copy()

        return frame

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Add point
            self.lane_points.append([x, y])
            print(f"Added point {len(self.lane_points)}: ({x}, {y})")
            self.redraw_frame()

        elif event == cv2.EVENT_RBUTTONDOWN:
            # Remove last point
            if self.lane_points:
                removed = self.lane_points.pop()
                print(f"Removed point: ({removed[0]}, {removed[1]})")
                self.redraw_frame()

    def redraw_frame(self):
        """Redraw frame with current lane points"""
        self.current_frame = self.original_frame.copy()

        # Draw polygon if we have at least 3 points
        if len(self.lane_points) >= 3:
            # Create filled polygon with transparency
            overlay = self.current_frame.copy()
            points = np.array(self.lane_points, dtype=np.int32)
            cv2.fillPoly(overlay, [points], self.polygon_color)
            # Blend with original
            cv2.addWeighted(overlay, 0.3, self.current_frame,
                            0.7, 0, self.current_frame)

            # Draw polygon outline
            cv2.polylines(self.current_frame, [
                          points], True, self.line_color, self.line_thickness)

        # Draw lines between consecutive points
        for i in range(len(self.lane_points) - 1):
            pt1 = tuple(self.lane_points[i])
            pt2 = tuple(self.lane_points[i + 1])
            cv2.line(self.current_frame, pt1, pt2,
                     self.line_color, self.line_thickness)

        # Draw line from last to first if we have at least 2 points (to show closure)
        if len(self.lane_points) >= 2:
            pt1 = tuple(self.lane_points[-1])
            pt2 = tuple(self.lane_points[0])
            cv2.line(self.current_frame, pt1, pt2,
                     (128, 128, 128), 1, cv2.LINE_AA)

        # Draw points with numbers
        for i, point in enumerate(self.lane_points):
            # Draw point
            cv2.circle(self.current_frame, tuple(point),
                       self.point_radius, self.point_color, -1)
            cv2.circle(self.current_frame, tuple(point),
                       self.point_radius + 2, (0, 0, 0), 1)

            # Draw point number
            text = str(i + 1)
            text_size = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            text_x = point[0] - text_size[0] // 2
            text_y = point[1] - self.point_radius - 5
            cv2.putText(self.current_frame, text, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.text_color, 1, cv2.LINE_AA)

        # Draw instructions
        if self.instructions_shown:
            self.draw_instructions()

    def draw_instructions(self):
        """Draw instructions on the frame"""
        instructions = [
            "Lane Configuration Tool",
            "=====================",
            "Left Click: Add point",
            "Right Click: Remove last point",
            "S: Save configuration",
            "L: Load configuration",
            "C: Clear all points",
            "H: Hide/Show instructions",
            "Q: Quit without saving",
            "ESC: Save and quit",
            "",
            f"Points: {len(self.lane_points)}"
        ]

        # Calculate instruction panel size
        padding = 10
        line_height = 25
        panel_width = 300
        panel_height = len(instructions) * line_height + padding * 2

        # Draw semi-transparent background
        overlay = self.current_frame.copy()
        cv2.rectangle(overlay, (padding, padding),
                      (padding + panel_width, padding + panel_height),
                      self.bg_color, -1)
        cv2.addWeighted(overlay, 0.7, self.current_frame,
                        0.3, 0, self.current_frame)

        # Draw border
        cv2.rectangle(self.current_frame, (padding, padding),
                      (padding + panel_width, padding + panel_height),
                      (255, 255, 255), 2)

        # Draw instructions text
        y = padding + line_height
        for i, line in enumerate(instructions):
            if i <= 1:  # Title lines
                cv2.putText(self.current_frame, line, (padding + 10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
            else:
                cv2.putText(self.current_frame, line, (padding + 10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.text_color, 1, cv2.LINE_AA)
            y += line_height

    def save_config(self):
        """Save lane configuration to JSON file"""
        if len(self.lane_points) < 3:
            print("Error: Need at least 3 points to define a lane")
            return False

        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)

        # Get frame dimensions
        height, width = self.original_frame.shape[:2]

        # Prepare configuration
        config = {
            "video_source": self.video_source,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "frame_dimensions": {
                "width": width,
                "height": height
            },
            "lane_points": self.lane_points,
            "num_points": len(self.lane_points)
        }

        # Save video-specific config file
        with open(self.video_config_file, 'w') as f:
            json.dump(config, f, indent=4)

        print(f"Configuration saved to {self.video_config_file}")

        # Update master config file
        self._update_master_config()

        # Save preview image
        preview_path = self.video_config_file.replace('.json', '_preview.jpg')
        cv2.imwrite(preview_path, self.current_frame)
        print(f"Preview image saved to {preview_path}")

        return True

    def _update_master_config(self):
        """Update master configuration file with video-config mapping"""
        # Load existing master config
        master_config = {}
        if os.path.exists(self.master_config_file):
            try:
                with open(self.master_config_file, 'r') as f:
                    master_config = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load master config: {e}")
                master_config = {}

        # Add or update entry for this video
        video_name = os.path.basename(self.video_source)
        master_config[video_name] = {
            "config_file": self.video_config_file,
            "video_path": self.video_source,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save master config
        with open(self.master_config_file, 'w') as f:
            json.dump(master_config, f, indent=4)

        print(f"Master configuration updated: {self.master_config_file}")

    def load_config(self):
        """Load lane configuration from JSON file"""
        if not os.path.exists(self.video_config_file):
            print(f"Configuration file not found: {self.video_config_file}")
            return False

        try:
            with open(self.video_config_file, 'r') as f:
                config = json.load(f)

            self.lane_points = config.get('lane_points', [])
            print(
                f"Loaded {len(self.lane_points)} points from {self.video_config_file}")
            self.redraw_frame()
            return True

        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False

    def clear_points(self):
        """Clear all lane points"""
        self.lane_points = []
        print("Cleared all points")
        self.redraw_frame()

    def run(self):
        """Run the lane configuration tool"""
        try:
            # Load first frame
            print("Loading video frame...")
            self.load_video_frame()

            # Create window
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.setMouseCallback(self.window_name, self.mouse_callback)

            # Initial draw
            self.redraw_frame()

            print("\nLane Configuration Tool Started")
            print("================================")
            print("Click on the video frame to add lane boundary points")
            print("Define the lane where vehicles approach the camera")
            print()

            # Main loop
            while True:
                cv2.imshow(self.window_name, self.current_frame)
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    # Quit without saving
                    print("Quitting without saving...")
                    break

                elif key == 27:  # ESC
                    # Save and quit
                    if self.save_config():
                        print("Configuration saved. Exiting...")
                    break

                elif key == ord('s'):
                    # Save configuration
                    self.save_config()

                elif key == ord('l'):
                    # Load configuration
                    self.load_config()

                elif key == ord('c'):
                    # Clear all points
                    self.clear_points()

                elif key == ord('h'):
                    # Toggle instructions
                    self.instructions_shown = not self.instructions_shown
                    self.redraw_frame()

            cv2.destroyAllWindows()

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Lane Configuration Tool")
    parser.add_argument("--video", type=str, required=True,
                        help="Path to video file")
    parser.add_argument("--config-dir", type=str, default="config",
                        help="Directory to save configuration files")
    args = parser.parse_args()

    # Check if video file exists
    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        return

    # Create and run tool
    tool = LaneConfigTool(args.video, args.config_dir)
    tool.run()


if __name__ == "__main__":
    main()
