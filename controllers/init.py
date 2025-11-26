"""
Webots controllers for supervisor and robots

This module contains the main control logic for:
- Supervisor: Global state management and environment dynamics
- Robots: Individual robot decision-making and behavior

Note: These controllers are designed to be run directly by Webots.
They should not typically be imported as modules, but their components
can be imported for testing or standalone use.
"""

__version__ = '0.1.0'

# Import paths for components (useful for testing)
from pathlib import Path

SUPERVISOR_PATH = Path(__file__).parent / 'supervisor_controller'
ROBOT_PATH = Path(__file__).parent / 'robot_controller'

__all__ = []  # Controllers are not meant to be imported

# Metadata
CONTROLLER_INFO = {
    'supervisor': {
        'name': 'supervisor_controller',
        'description': 'Global state manager and environment controller',
        'main_file': 'supervisor_controller.py'
    },
    'robot': {
        'name': 'robot_controller',
        'description': 'Individual robot decision-making and control',
        'main_file': 'robot_controller.py'
    }
}

def get_controller_info(controller_type='supervisor'):
    """
    Get information about a controller
    
    Args:
        controller_type: 'supervisor' or 'robot'
    
    Returns:
        dict: Controller information
    """
    return CONTROLLER_INFO.get(controller_type, {})