"""
Path Setup for Dashboard Backend
This module MUST be imported first to set up sys.path correctly.
"""

import sys
from pathlib import Path

# Get project root (3 levels up from this file)
_project_root = Path(__file__).resolve().parent.parent.parent

# Add to sys.path if not already there
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Export for use by other modules
PROJECT_ROOT = _project_root
