"""
Stream Manager for Video Frame Encoding and Buffering
Handles frame encoding, compression, and streaming to dashboard clients.
"""

import cv2
import numpy as np
import base64
import logging
from typing import Optional, Tuple
from collections import deque
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class StreamManager:
    """
    Manages video frame encoding, compression, and buffering for dashboard streaming.

    Features:
    - JPEG encoding with configurable quality
    - Frame rate control
    - Automatic frame buffering
    - Frame resizing for bandwidth optimization
    - Base64 encoding for WebSocket transmission
    """

    def __init__(
        self,
        target_fps: int = 5,
        jpeg_quality: int = 80,
        max_width: int = 1280,
        buffer_size: int = 30
    ):
        """
        Initialize the stream manager.

        Args:
            target_fps: Target frames per second for streaming (default: 5)
            jpeg_quality: JPEG compression quality 0-100 (default: 80)
            max_width: Maximum frame width for streaming (default: 1280)
            buffer_size: Maximum number of frames to buffer (default: 30)
        """
        self.target_fps = target_fps
        self.jpeg_quality = jpeg_quality
        self.max_width = max_width
        self.buffer_size = buffer_size

        # Frame timing control
        self.frame_interval = 1.0 / target_fps
        self.last_frame_time = 0

        # Frame buffer (stores recent encoded frames)
        self.frame_buffer = deque(maxlen=buffer_size)

        # Statistics
        self.stats = {
            'frames_encoded': 0,
            'frames_dropped': 0,
            'total_bytes_sent': 0,
            'avg_encode_time': 0,
            'start_time': time.time()
        }

        logger.info(
            f"StreamManager initialized: {target_fps} FPS, Quality: {jpeg_quality}")

    def should_process_frame(self) -> bool:
        """
        Check if enough time has passed to process next frame.

        Returns:
            True if frame should be processed, False otherwise
        """
        current_time = time.time()
        if current_time - self.last_frame_time >= self.frame_interval:
            self.last_frame_time = current_time
            return True
        return False

    def resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Resize frame to maximum width while maintaining aspect ratio.

        Args:
            frame: Input frame (BGR numpy array)

        Returns:
            Resized frame
        """
        height, width = frame.shape[:2]

        if width > self.max_width:
            scale = self.max_width / width
            new_width = self.max_width
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height),
                               interpolation=cv2.INTER_AREA)
            logger.debug(
                f"Frame resized: {width}x{height} -> {new_width}x{new_height}")

        return frame

    def encode_frame(self, frame: np.ndarray, resize: bool = True) -> Optional[str]:
        """
        Encode frame to base64 JPEG string.

        Args:
            frame: Input frame (BGR numpy array)
            resize: Whether to resize frame before encoding

        Returns:
            Base64 encoded JPEG string, or None on failure
        """
        if frame is None or frame.size == 0:
            logger.warning("Cannot encode empty frame")
            return None

        try:
            encode_start = time.time()

            # Resize if requested
            if resize:
                frame = self.resize_frame(frame)

            # Encode to JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
            success, buffer = cv2.imencode('.jpg', frame, encode_params)

            if not success:
                logger.error("Failed to encode frame to JPEG")
                return None

            # Convert to base64
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            # Update statistics
            encode_time = time.time() - encode_start
            self._update_stats(encode_time, len(jpg_as_text))

            logger.debug(
                f"Frame encoded: {len(jpg_as_text)} bytes in {encode_time*1000:.2f}ms")

            return jpg_as_text

        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
            return None

    def process_frame(self, frame: np.ndarray) -> Optional[str]:
        """
        Process frame with rate limiting and encoding.

        Args:
            frame: Input frame (BGR numpy array)

        Returns:
            Base64 encoded JPEG string if frame should be sent, None otherwise
        """
        # Check if we should process this frame (rate limiting)
        if not self.should_process_frame():
            self.stats['frames_dropped'] += 1
            return None

        # Encode frame
        encoded = self.encode_frame(frame)

        if encoded:
            # Add to buffer
            self.frame_buffer.append({
                'data': encoded,
                'timestamp': datetime.now().isoformat(),
                'size': len(encoded)
            })

        return encoded

    def add_overlay_info(
        self,
        frame: np.ndarray,
        fps: float = 0,
        frame_count: int = 0,
        vehicle_count: int = 0,
        ambulance_detected: bool = False
    ) -> np.ndarray:
        """
        Add information overlay to frame.

        Args:
            frame: Input frame
            fps: Current FPS
            frame_count: Current frame count
            vehicle_count: Vehicle count
            ambulance_detected: Whether ambulance is detected

        Returns:
            Frame with overlay
        """
        overlay = frame.copy()

        # Background for text
        cv2.rectangle(overlay, (10, 10), (300, 120), (0, 0, 0), -1)

        # Add transparency
        alpha = 0.6
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        # Add text information
        y_offset = 35
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2

        info_texts = [
            f"FPS: {fps:.1f}",
            f"Frame: {frame_count}",
            f"Vehicles: {vehicle_count}"
        ]

        for i, text in enumerate(info_texts):
            cv2.putText(
                frame,
                text,
                (20, y_offset + i * 25),
                font,
                font_scale,
                (255, 255, 255),
                thickness
            )

        # Ambulance alert
        if ambulance_detected:
            cv2.rectangle(frame, (10, 130), (300, 170), (0, 0, 255), -1)
            cv2.putText(
                frame,
                "AMBULANCE DETECTED!",
                (20, 155),
                font,
                0.7,
                (255, 255, 255),
                2
            )

        return frame

    def _update_stats(self, encode_time: float, byte_size: int):
        """Update encoding statistics."""
        self.stats['frames_encoded'] += 1
        self.stats['total_bytes_sent'] += byte_size

        # Update average encode time (exponential moving average)
        alpha = 0.1
        if self.stats['avg_encode_time'] == 0:
            self.stats['avg_encode_time'] = encode_time
        else:
            self.stats['avg_encode_time'] = (
                alpha * encode_time + (1 - alpha) *
                self.stats['avg_encode_time']
            )

    def get_stats(self) -> dict:
        """Get stream statistics."""
        uptime = time.time() - self.stats['start_time']

        return {
            'frames_encoded': self.stats['frames_encoded'],
            'frames_dropped': self.stats['frames_dropped'],
            'total_bytes_sent': self.stats['total_bytes_sent'],
            'avg_encode_time_ms': self.stats['avg_encode_time'] * 1000,
            'effective_fps': self.stats['frames_encoded'] / uptime if uptime > 0 else 0,
            'uptime_seconds': uptime,
            'buffer_size': len(self.frame_buffer)
        }

    def get_latest_frame(self) -> Optional[dict]:
        """Get the latest buffered frame."""
        if self.frame_buffer:
            return self.frame_buffer[-1]
        return None

    def clear_buffer(self):
        """Clear the frame buffer."""
        self.frame_buffer.clear()
        logger.info("Frame buffer cleared")

    def update_settings(
        self,
        target_fps: Optional[int] = None,
        jpeg_quality: Optional[int] = None,
        max_width: Optional[int] = None
    ):
        """
        Update stream settings on the fly.

        Args:
            target_fps: New target FPS
            jpeg_quality: New JPEG quality
            max_width: New maximum width
        """
        if target_fps is not None:
            self.target_fps = target_fps
            self.frame_interval = 1.0 / target_fps
            logger.info(f"Target FPS updated to {target_fps}")

        if jpeg_quality is not None:
            self.jpeg_quality = max(0, min(100, jpeg_quality))
            logger.info(f"JPEG quality updated to {self.jpeg_quality}")

        if max_width is not None:
            self.max_width = max_width
            logger.info(f"Max width updated to {max_width}")


# Test function
def test_stream_manager():
    """Test the stream manager with a sample frame."""
    logger.setLevel(logging.DEBUG)

    # Create a test frame
    test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

    # Initialize stream manager
    manager = StreamManager(target_fps=5, jpeg_quality=80)

    print("\n" + "="*60)
    print("🎥 Stream Manager Test")
    print("="*60)

    # Test encoding
    for i in range(10):
        encoded = manager.process_frame(test_frame)
        if encoded:
            print(f"Frame {i+1}: Encoded {len(encoded)} bytes")
        else:
            print(f"Frame {i+1}: Dropped (rate limiting)")
        time.sleep(0.1)

    # Print statistics
    stats = manager.get_stats()
    print("\n" + "-"*60)
    print("Statistics:")
    print(f"  Frames encoded: {stats['frames_encoded']}")
    print(f"  Frames dropped: {stats['frames_dropped']}")
    print(f"  Total bytes: {stats['total_bytes_sent']:,}")
    print(f"  Avg encode time: {stats['avg_encode_time_ms']:.2f}ms")
    print(f"  Effective FPS: {stats['effective_fps']:.2f}")
    print("="*60 + "\n")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_stream_manager()
