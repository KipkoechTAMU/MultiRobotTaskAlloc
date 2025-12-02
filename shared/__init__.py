"""
Shared utilities and configuration for multi-robot task allocation

This module provides:
- Configuration classes for experiments and system parameters
- Constants and enumerations for robot states and message types
- Utility functions for geometry and calculations
- Communication protocols between robots and supervisor
"""

from .config import Config, ExperimentConfig
from .constants import RobotState, MessageType
from .utils import (
    distance,
    normalize_vector,
    angle_to_target,
    clamp,
    MovingAverage
)
from .communication import (
    Message,
    SupervisorBroadcast,
    RobotReport
)

__all__ = [
    # Configuration
    'Config',
    'ExperimentConfig',
    
    # Constants and Enums
    'RobotState',
    'MessageType',
    
    # Utility Functions
    'distance',
    'normalize_vector',
    'angle_to_target',
    'clamp',
    'MovingAverage',
    
    # Communication Classes
    'Message',
    'SupervisorBroadcast',
    'RobotReport',
]

__version__ = '0.1.0'

# Convenience imports for common patterns
def get_default_config():
    """Get default configuration"""
    return Config()

def get_experiment_config(experiment_type):
    """
    Get configuration for specific experiment type
    
    Args:
        experiment_type: 'surge', 'failures', etc.
    
    Returns:
        Experiment configuration dictionary
    """
    if experiment_type == 'surge':
        return ExperimentConfig.experiment_1_surge()
    elif experiment_type == 'failures':
        return ExperimentConfig.experiment_2_failures()
    else:
        raise ValueError(f"Unknown experiment type: {experiment_type}")