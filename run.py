#!/usr/bin/env python3
"""
Simple launcher script for the Agent-Intelligent Anonymization System.
Run this script to start the web interface.
"""

import sys
import os
import subprocess

def main():
    """Launch the web UI."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the web UI script
    web_ui_path = os.path.join(script_dir, "src", "interfaces", "web_ui.py")
    
    # Check if the web UI script exists
    if not os.path.exists(web_ui_path):
        print("❌ Error: Web UI script not found at:", web_ui_path)
        print("Make sure you're running this from the project root directory.")
        return 1
    
    # Print startup message
    print("🚀 Starting Agent-Intelligent Anonymization System...")
    print("🌐 Web interface will be available at: http://127.0.0.1:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Run the web UI
        subprocess.run([sys.executable, web_ui_path], cwd=script_dir)
    except KeyboardInterrupt:
        print("\n👋 Shutting down the server. Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Error starting the web interface: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())