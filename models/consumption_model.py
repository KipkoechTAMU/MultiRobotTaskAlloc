"""
Consumption rate model (Equation 3)
"""
import numpy as np
from typing import List
from shared.config import Config

class ConsumptionModel:
    """
    Implements F_i(q_i, x_i) from the paper
    """
    def __init__(self):
        self.R = Config.R_I
        self.alpha = Config.ALPHA_I
        self.beta = Config.BETA_I
    
    def compute_consumption(self, task_id: int, q_i: float, 
                          x_i: float) -> float:
        """
        Compute consumption rate for task i
        
        F_i(q_i, x_i) = R_i * (e^(α_i*q_i) - 1)/(e^(α_i*q_i) + 1) * x_i^β_i
        
        Args:
            task_id: Task index
            q_i: Resource level for task i
            x_i: Population state for task i
            
        Returns:
            Consumption rate
        """
        if x_i <= 0:
            return 0.0
        
        # Hyperbolic tangent-like function
        exp_term = np.exp(self.alpha[task_id] * q_i)
        tanh_term = (exp_term - 1) / (exp_term + 1)
        
        # Power-law dependency on population
        power_term = np.power(x_i, self.beta[task_id])
        
        return self.R[task_id] * tanh_term * power_term
    
    def compute_all_consumption(self, q: List[float], 
                               x: List[float]) -> List[float]:
        """Compute consumption rates for all tasks"""
        return [self.compute_consumption(i, q[i], x[i]) 
                for i in range(len(q))]
    
    def compute_equilibrium(self, w: List[float], 
                          x: List[float]) -> List[float]:
        """
        Find equilibrium resource levels q* where F_i(q*, x_i) = w_i
        Uses numerical root finding
        """
        from scipy.optimize import fsolve
        
        def equations(q_vals):
            return [self.compute_consumption(i, q_vals[i], x[i]) - w[i]
                   for i in range(len(w))]
        
        # Initial guess
        q_init = [10.0] * len(w)
        q_star = fsolve(equations, q_init)
        
        return q_star.tolist()