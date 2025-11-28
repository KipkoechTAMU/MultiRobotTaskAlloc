"""
Task revision protocol (Equation 7)
"""
import numpy as np
from typing import List
from shared.config import Config

class RevisionProtocol:
    """
    Implements probabilistic task switching
    
    P(switch from i to j) = ρ[p_j - p_i]_+
    P(stay at i) = 1 - ρ Σ_j [p_j - p_i]_+
    """
    def __init__(self, rho: float = Config.RHO):
        self.rho = rho
    
    @staticmethod
    def positive_part(value: float) -> float:
        """[x]_+ = max(0, x)"""
        return max(0, value)
    
    def compute_switch_probabilities(self, current_task: int,
                                    payoffs: List[float]) -> List[float]:
        """
        Compute probability distribution over tasks
        
        Args:
            current_task: Current task index
            payoffs: Payoff values for all tasks
            
        Returns:
            Probability distribution (sums to 1)
        """
        num_tasks = len(payoffs)
        probs = np.zeros(num_tasks)
        current_payoff = payoffs[current_task]
        
        # Compute switch probabilities
        for j in range(num_tasks):
            if j == current_task:
                continue
            probs[j] = self.rho * self.positive_part(
                payoffs[j] - current_payoff
            )
        
        # Compute stay probability
        probs[current_task] = 1.0 - np.sum(probs)
        
        # Ensure valid probability distribution
        assert np.isclose(np.sum(probs), 1.0), \
            f"Probabilities don't sum to 1: {np.sum(probs)}"
        assert np.all(probs >= 0), \
            f"Negative probabilities: {probs}"
        
        return probs.tolist()
    
    def select_task(self, current_task: int, 
                   payoffs: List[float]) -> int:
        """
        Sample new task according to revision protocol
        
        Args:
            current_task: Current task index
            payoffs: Payoff values for all tasks
            
        Returns:
            New task index (may be same as current)
        """
        probs = self.compute_switch_probabilities(current_task, payoffs)
        return np.random.choice(len(payoffs), p=probs)