#!/usr/bin/env python3
"""
Launcher script for PyInstaller.
This script uses absolute imports to work correctly when bundled.
"""

import sys
import os

# Add src to path for PyInstaller
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    bundle_dir = sys._MEIPASS
    sys.path.insert(0, bundle_dir)
else:
    # Running in development
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.insert(0, src_dir)

# Now import and run
from pg_isomap.desktop_app import main

if __name__ == "__main__":
    main()
