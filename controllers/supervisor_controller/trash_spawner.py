"""
Manages trash spawning using Poisson process
"""
import numpy as np
from typing import List, Tuple
from controller import Supervisor
from shared.config import Config

class TrashSpawner:
    """
    Spawns trash objects according to Poisson process
    """
    def __init__(self, supervisor: Supervisor, growth_rates: List[float]):
        self.supervisor = supervisor
        self.growth_rates = growth_rates
        self.next_spawn_times = [0.0] * Config.NUM_TASKS
        self.patch_positions = Config.PATCH_POSITIONS
        
        # Generate initial spawn times
        for i in range(Config.NUM_TASKS):
            self.next_spawn_times[i] = self._generate_next_spawn_time(i)
    
    def _generate_next_spawn_time(self, task_id: int) -> float:
        """Generate next spawn time using exponential distribution"""
        if self.growth_rates[task_id] <= 0:
            return float('inf')
        return np.random.exponential(1.0 / self.growth_rates[task_id])
    
    def update(self, current_time: float, dt: float):
        """Check if trash should spawn and create objects"""
        for task_id in range(Config.NUM_TASKS):
            if current_time >= self.next_spawn_times[task_id]:
                self._spawn_trash(task_id)
                self.next_spawn_times[task_id] = (
                    current_time + self._generate_next_spawn_time(task_id)
                )
    
    def _spawn_trash(self, task_id: int):
        """Spawn a trash object in patch"""
        # Get patch boundaries
        patch_center = self.patch_positions[task_id]
        patch_size = 20.0  # meters
        
        # Random position within patch
        x = patch_center[0] + np.random.uniform(-patch_size/2, patch_size/2)
        y = patch_center[1] + np.random.uniform(-patch_size/2, patch_size/2)
        
        # Create trash object in Webots
        trash_def = f"""
        DEF TRASH_{task_id}_{int(np.random.rand()*10000)} Solid {{
            translation {x} {y} 0.05
            children [
                Shape {{
                    appearance PBRAppearance {{
                        baseColor 1 0 0
                    }}
                    geometry Box {{
                        size 0.1 0.1 0.1
                    }}
                }}
            ]
        }}
        """
        self.supervisor.getRoot().getField('children').importMFNodeFromString(
            -1, trash_def
        )
    
    def set_growth_rate(self, task_id: int, new_rate: float):
        """Update growth rate for a task"""
        self.growth_rates[task_id] = new_rate