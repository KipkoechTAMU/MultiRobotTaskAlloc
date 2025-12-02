"""
Verify 4-robot configuration
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from shared.config import Config

print("=" * 60)
print("4-ROBOT CONFIGURATION VERIFICATION")
print("=" * 60)
print()

# Check config
print(f"NUM_ROBOTS: {Config.NUM_ROBOTS}")
print(f"NUM_TASKS: {Config.NUM_TASKS}")
print()

# Check expected distribution
robots_per_task = Config.NUM_ROBOTS / Config.NUM_TASKS
print(f"Robots per task (expected): {robots_per_task}")
print(f"Initial x (expected): {[1.0/Config.NUM_TASKS] * Config.NUM_TASKS}")
print()

# Check world file
world_file = Path("worlds/trash_collection.wbt")
if world_file.exists():
    content = world_file.read_text()
    
    # Count robots in world file
    robot_count = content.count('E-puck {')
    print(f"Robots in world file: {robot_count}")
    
    if robot_count == Config.NUM_ROBOTS:
        print("✓ World file matches Config.NUM_ROBOTS")
    else:
        print(f"✗ MISMATCH: World has {robot_count} but Config has {Config.NUM_ROBOTS}")
else:
    print("✗ World file not found")

print()
print("=" * 60)

if robot_count == Config.NUM_ROBOTS == 4:
    print("✓ ALL CHECKS PASSED - Ready for 4-robot testing")
else:
    print("✗ Configuration issues detected")

print("=" * 60)