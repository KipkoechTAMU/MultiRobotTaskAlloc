"""
Supervisor controller components

This module manages:
- Environment dynamics (resource growth and consumption)
- Robot state tracking (population distribution)
- Trash spawning (Poisson process)
- Data logging for analysis

Components:
    EnvironmentModel: Implements equation (2) for resource dynamics
    StateManager: Tracks robot task assignments and population state
    TrashSpawner: Manages stochastic trash generation
    DataLogger: Records experimental data for post-analysis
"""

from .environment_model import EnvironmentModel
from .state_manager import StateManager
from .trash_spawner import TrashSpawner
from .data_logger import DataLogger

__all__ = [
    'EnvironmentModel',
    'StateManager',
    'TrashSpawner',
    'DataLogger',
]

__version__ = '0.1.0'

# Convenience function to create all supervisor components
def create_supervisor_components(supervisor, num_robots=40, num_tasks=4, 
                                 initial_q=None, initial_w=None,
                                 experiment_name='default'):
    """
    Factory function to create all supervisor components at once
    
    Args:
        supervisor: Webots Supervisor instance
        num_robots: Number of robots in system
        num_tasks: Number of tasks/patches
        initial_q: Initial resource levels (default: all zeros)
        initial_w: Initial growth rates (default: from Config)
        experiment_name: Name for data logging
    
    Returns:
        dict: Dictionary containing all components
        
    Example:
        components = create_supervisor_components(
            supervisor=self.supervisor,
            num_robots=40,
            experiment_name='test_run'
        )
        env_model = components['environment']
        state_manager = components['state_manager']
    """
    from shared.config import Config
    
    if initial_q is None:
        initial_q = [0.0] * num_tasks
    
    if initial_w is None:
        initial_w = Config.INITIAL_GROWTH_RATES.copy()
    
    components = {
        'environment': EnvironmentModel(initial_q, initial_w),
        'state_manager': StateManager(num_robots, num_tasks),
        'trash_spawner': TrashSpawner(supervisor, initial_w),
        'data_logger': DataLogger(experiment_name)
    }
    
    return components

# Helper function for common supervisor operations
def get_system_state(env_model, state_manager):
    """
    Get complete system state
    
    Args:
        env_model: EnvironmentModel instance
        state_manager: StateManager instance
    
    Returns:
        dict: Complete system state
    """
    return {
        'q': env_model.get_resources(),
        'x': state_manager.get_population_state(),
        'w': env_model.get_growth_rates(),
        'robot_counts': state_manager.get_robot_count_per_task()
    }