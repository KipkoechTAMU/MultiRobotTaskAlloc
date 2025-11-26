"""
Environment dynamics (Equation 2)
"""
import numpy as np
from typing import List
from models.consumption_model import ConsumptionModel
from shared.config import Config

class EnvironmentModel:
    """
    Implements q̇_i(t) = -F_i(q_i, x_i) + w_i
    """
    def __init__(self, initial_q: List[float], 
                 initial_w: List[float]):
        self.q = np.array(initial_q, dtype=float)
        self.w = np.array(initial_w, dtype=float)
        self.consumption_model = ConsumptionModel()
    
    def update(self, x: List[float], dt: float):
        """
        Update resource levels using Euler integration
        
        Args:
            x: Current population state
            dt: Time step in seconds
        """
        # Compute consumption rates
        F = self.consumption_model.compute_all_consumption(
            self.q.tolist(), x
        )
        F = np.array(F)
        
        # Update: q(t+dt) = q(t) + (-F + w) * dt
        self.q += (self.w - F) * dt
        
        # Ensure non-negative resources
        self.q = np.maximum(self.q, 0)
    
    def get_resources(self) -> List[float]:
        """Get current resource levels"""
        return self.q.tolist()
    
    def set_growth_rate(self, task_id: int, new_rate: float):
        """Change growth rate for a specific task"""
        self.w[task_id] = new_rate
    
    def get_growth_rates(self) -> List[float]:
        """Get current growth rates"""
        return self.w.tolist()