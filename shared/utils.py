"""
Utility functions
"""
import numpy as np
from typing import List, Tuple

def distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """Euclidean distance between two positions"""
    return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """Normalize a vector"""
    norm = np.linalg.norm(vector)
    return vector / norm if norm > 0 else vector

def angle_to_target(current_pos: Tuple[float, float], 
                    target_pos: Tuple[float, float]) -> float:
    """Calculate angle from current position to target"""
    dx = target_pos[0] - current_pos[0]
    dy = target_pos[1] - current_pos[1]
    return np.arctan2(dy, dx)

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))

class MovingAverage:
    """Simple moving average filter"""
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.values = []
    
    def update(self, value: float) -> float:
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)
        return np.mean(self.values)