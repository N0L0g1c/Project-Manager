#!/usr/bin/env python3
"""
Development Project Manager - GUI Launcher
Simple launcher for the GUI version
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from project_manager_gui import main
    main()
except ImportError as e:
    print(f"Error importing GUI: {e}")
    print("Please install required dependencies:")
    print("pip install -r requirements.txt")
    sys.exit(1)
