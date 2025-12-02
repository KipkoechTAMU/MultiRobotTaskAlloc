
"""
macOS-compatible launcher
"""
import subprocess
import sys
from pathlib import Path
import time

def launch_webots_macos(world_file):
    """Launch Webots on macOS using 'open' command"""
    
    # Check Webots is installed
    webots_app = Path("/Applications/Webots.app")
    if not webots_app.exists():
        print("❌ ERROR: Webots not found")
        print("Install with: brew install --cask webots")
        sys.exit(1)
    
    print("✓ Webots found")
    
    # Get absolute path to world file
    world_path = Path(world_file).resolve()
    if not world_path.exists():
        print(f"❌ ERROR: World file not found: {world_path}")
        sys.exit(1)
    
    print(f"✓ World file: {world_path}")
    
    # Remove quarantine
    try:
        subprocess.run(
            ["sudo", "xattr", "-rd", "com.apple.quarantine", str(webots_app)],
            check=False,
            capture_output=True
        )
    except:
        pass
    
    # Launch using 'open' command (proper macOS way)
    print("\nLaunching Webots...")
    
    try:
        subprocess.run(
            ["open", "-a", "Webots", str(world_path)],
            check=True
        )
        
        # Give it time to start
        time.sleep(2)
        
        print("✓ Webots launched")
        print("\nCheck Webots window for simulation")
        print("Press Ctrl+C in Webots or close window to stop")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to launch Webots: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nStopped by user")

if __name__ == "__main__":
    import os
    
    # Check we're in project directory
    if not Path("worlds/trash_collection.wbt").exists():
        print("❌ ERROR: Not in project directory")
        print("Run from project root")
        sys.exit(1)
    
    world_file = "worlds/trash_collection.wbt"
    launch_webots_macos(world_file)