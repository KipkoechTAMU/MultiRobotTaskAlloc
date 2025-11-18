"""
Poisson clock for task revision timing
"""
import numpy as np
from shared.config import Config

class PoissonClock:
    """
    Generates revision opportunities according to Poisson process
    Each robot has independent clock
    """
    def __init__(self, lambda_param: float = Config.POISSON_LAMBDA):
        self.lambda_param = lambda_param
        self.next_tick_time = 0.0
        self.total_ticks = 0
        
        # Generate first tick
        self._generate_next_tick()
    
    def _generate_next_tick(self):
        """Generate next tick using exponential distribution"""
        # Time until next tick ~ Exp(λ)
        inter_arrival = np.random.exponential(1.0 / self.lambda_param)
        self.next_tick_time += inter_arrival
    
    def should_tick(self, current_time: float) -> bool:
        """
        Check if clock should tick at current time
        
        Args:
            current_time: Current simulation time
            
        Returns:
            True if it's time to revise task
        """
        if current_time >= self.next_tick_time:
            self.total_ticks += 1
            self._generate_next_tick()
            return True
        return False
    
    def reset(self, current_time: float):
        """Reset clock to current time"""
        self.next_tick_time = current_time
        self._generate_next_tick()
    
    def get_next_tick_time(self) -> float:
        """Get time of next scheduled tick"""
        return self.next_tick_time