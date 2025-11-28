"""
Payoff mechanism (Equation 6)
"""
import numpy as np
from typing import List
from models.consumption_model import ConsumptionModel
from shared.config import Config

class PayoffMechanism:
    """
    Implements p_i(t) = q_i(t) + ν(-F_i(γ*, x_i) + w_i)
    """
    def __init__(self, nu: float = 0):
        self.nu = nu
        self.consumption_model = ConsumptionModel()
        self.gamma_star = None
        self.x_star = None
    
    def set_equilibrium(self, gamma_star: float, x_star: List[float]):
        """Set equilibrium values for model-based payoff"""
        self.gamma_star = gamma_star
        self.x_star = x_star
    
    def compute_payoff(self, task_id: int, q: List[float], 
                      x: List[float], w: List[float]) -> float:
        """
        Compute payoff for task i
        
        Args:
            task_id: Task index
            q: Current resource levels
            x: Current population state
            w: Growth rates
            
        Returns:
            Payoff value
        """
        if self.nu == 0:
            # Model-free: payoff is just current resource level
            return q[task_id]
        else:
            # Model-based: incorporate equilibrium prediction
            if self.gamma_star is None or self.x_star is None:
                raise ValueError("Equilibrium not set for model-based payoff")
            
            F_equilibrium = self.consumption_model.compute_consumption(
                task_id, self.gamma_star, x[task_id]
            )
            
            return q[task_id] + self.nu * (-F_equilibrium + w[task_id])
    
    def compute_all_payoffs(self, q: List[float], x: List[float],
                           w: List[float]) -> List[float]:
        """Compute payoffs for all tasks"""
        return [self.compute_payoff(i, q, x, w) 
                for i in range(len(q))]