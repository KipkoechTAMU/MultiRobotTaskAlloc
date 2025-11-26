"""
Manages global state (q, x) and robot tracking
"""
import numpy as np
from typing import List, Dict
from shared.config import Config

class StateManager:
    """
    Tracks population state and robot assignments
    """
    def __init__(self, num_robots: int, num_tasks: int):
        self.num_robots = num_robots
        self.num_tasks = num_tasks
        
        # Robot assignments: robot_id -> task_id
        self.robot_tasks = {}
        
        # Initialize uniform distribution
        robots_per_task = num_robots // num_tasks
        for i in range(num_robots):
            self.robot_tasks[i] = i % num_tasks
        
        # Robot status tracking
        self.robot_active = {i: True for i in range(num_robots)}
    
    def update_robot_task(self, robot_id: int, new_task: int):
        """Update task assignment for a robot"""
        if robot_id in self.robot_tasks:
            self.robot_tasks[robot_id] = new_task
    
    def set_robot_active(self, robot_id: int, is_active: bool):
        """Set robot active/inactive status"""
        self.robot_active[robot_id] = is_active
    
    def get_population_state(self) -> List[float]:
        """
        Compute x(t) = (x_1, ..., x_M) where
        x_i = (# robots on task i) / (total active robots)
        
        Returns:
            Population state vector
        """
        # Count active robots per task
        task_counts = np.zeros(self.num_tasks)
        total_active = 0
        
        for robot_id, task_id in self.robot_tasks.items():
            if self.robot_active.get(robot_id, True):
                task_counts[task_id] += 1
                total_active += 1
        
        if total_active == 0:
            # If no robots active, return uniform distribution
            return [1.0 / self.num_tasks] * self.num_tasks
        
        # Normalize to get proportions
        x = task_counts / total_active
        return x.tolist()
    
    def get_robot_count_per_task(self) -> Dict[int, int]:
        """Get number of active robots assigned to each task"""
        counts = {i: 0 for i in range(self.num_tasks)}
        
        for robot_id, task_id in self.robot_tasks.items():
            if self.robot_active.get(robot_id, True):
                counts[task_id] += 1
        
        return counts