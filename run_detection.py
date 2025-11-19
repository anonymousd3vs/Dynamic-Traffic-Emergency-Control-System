#!/usr/bin/env python3
"""
Main entry point for running vehicle detection and tracking.

This script provides a simple interface to the core detection system.
"""

from core.detectors.traffic_detector import main
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main detection system

if __name__ == "__main__":
    main()
