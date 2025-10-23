#!/usr/bin/env python3
"""
Test script for the Development Project Manager GUI
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from project_manager_gui import ProjectManagerGUI
    import tkinter as tk
    
    def test_gui():
        """Test the GUI functionality"""
        print("Testing Development Project Manager GUI...")
        
        # Create a test window
        root = tk.Tk()
        root.withdraw()  # Hide the main window for testing
        
        try:
            # Initialize the GUI
            app = ProjectManagerGUI(root)
            print("[OK] GUI initialized successfully")
            
            # Test configuration loading
            config = app.load_config()
            print(f"[OK] Configuration loaded: {len(config)} settings")
            
            # Test projects directory
            projects_dir = Path(config["projects_dir"])
            print(f"[OK] Projects directory: {projects_dir}")
            print(f"[OK] Directory exists: {projects_dir.exists()}")
            
            # Test project loading
            app.load_projects()
            print(f"[OK] Projects loaded: {len(app.projects)} projects found")
            
            # Test refresh functionality
            app.refresh_projects()
            print("[OK] Projects list refreshed successfully")
            
            print("\n[SUCCESS] All tests passed! The GUI should work correctly.")
            
        except Exception as e:
            print(f"[ERROR] Error during testing: {e}")
            return False
        finally:
            root.destroy()
        
        return True
    
    if __name__ == "__main__":
        success = test_gui()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Make sure all required packages are installed:")
    print("pip install psutil requests")
    sys.exit(1)
