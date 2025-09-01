#!/usr/bin/env python3
"""
"""
import sys
import os
import subprocess

def main():
    """Launch CLI mode with arguments."""
    print("🚀 Google Photos Downloader - CLI Mode")
    print("=" * 50)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Forward all arguments to cli_mode.py
    args = sys.argv[1:]  # Skip script name
    
    try:
        # Run CLI mode
        result = subprocess.run([sys.executable, "cli_mode.py"] + args)
        return result.returncode
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 130
    except Exception as e:
        print(f"❌ Error launching CLI: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())