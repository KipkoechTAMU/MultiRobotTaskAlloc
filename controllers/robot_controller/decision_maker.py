"""
Decision-making logic for task selection
"""
from typing import List, Optional
import numpy as np

from models.payoff_mechanism import PayoffMechanism
from models.revision_protocol import RevisionProtocol
from shared.config import Config

class DecisionMaker:
    """
    Implements task selection based on payoffs and revision protocol
    """
    def __init__(self, robot_id: int, nu: float = Config.NU):
        self.robot_id = robot_id
        self.current_task = None
        
        # Initialize decision-making components
        self.payoff_mechanism = PayoffMechanism(nu)
        self.revision_protocol = RevisionProtocol(Config.RHO)
        
        # Cache for latest state
        self.latest_q = None
        self.latest_x = None
        self.latest_w = None
        
        print(f"Robot {robot_id}: Decision maker initialized (ν={nu})")
    
    def set_equilibrium(self, gamma_star: float, x_star: List[float]):
        """Set equilibrium for model-based payoff"""
        self.payoff_mechanism.set_equilibrium(gamma_star, x_star)
    
    def update_state(self, q: List[float], x: List[float], w: List[float]):
        """Update cached global state"""
        self.latest_q = q
        self.latest_x = x
        self.latest_w = w
    
    def initialize_task(self) -> int:
        """
        Initialize task selection (uniform random)
        
        Returns:
            Initial task ID
        """
        self.current_task = self.robot_id % Config.NUM_TASKS
        print(f"Robot {self.robot_id}: Initial task = {self.current_task}")
        return self.current_task
    
    def revise_task(self) -> Optional[int]:
        """
        Decide whether to switch task based on current state
        
        Returns:
            New task ID if switching, None if staying
        """
        if self.latest_q is None or self.latest_x is None:
            print(f"Robot {self.robot_id}: No state available yet")
            return None
        
        if self.current_task is None:
            return self.initialize_task()
        
        # Compute payoffs for all tasks
        payoffs = self.payoff_mechanism.compute_all_payoffs(
            self.latest_q, self.latest_x, 
            self.latest_w or Config.INITIAL_GROWTH_RATES
        )
        
        # Apply revision protocol
        new_task = self.revision_protocol.select_task(
            self.current_task, payoffs
        )
        
        if new_task != self.current_task:
            print(f"Robot {self.robot_id}: Switching {self.current_task} -> {new_task}")
            print(f"  Payoffs: {[f'{p:.2f}' for p in payoffs]}")
            self.current_task = new_task
            return new_task
        
        return None  # No change
    
    def get_current_task(self) -> Optional[int]:
        """Get current task assignment"""
        return self.current_task