"""
Global configuration and parameters
"""

class Config:
    # Simulation parameters
    TIME_STEP = 32  # ms, Webots timestep
    SIMULATION_DURATION = 2000  # seconds
    
    # Robot parameters
    NUM_ROBOTS = 4
    BASKET_CAPACITY = 10
    ROBOT_SPEED = 1.0  # m/s
    
    # Task allocation parameters
    NUM_TASKS = 4
    POISSON_LAMBDA = 8.0  # 1/8 Hz (revision every 8 seconds on average)
    RHO = 1.0 / 600.0  # Revision protocol parameter
    NU = 0  # Payoff mechanism weight (0, 40, or 800)
    
    # Environment parameters
    INITIAL_GROWTH_RATES = [0.5, 0.5, 0.5, 0.5]
    PATCH_POSITIONS = [
        (15, 15),   # Patch 1
        (15, 55),   # Patch 2
        (55, 15),   # Patch 3
        (55, 55)    # Patch 4
    ]
    DUMPSTER_POSITIONS = [
        (0, 35),    # Left
        (70, 35),   # Right
        (35, 0),    # Bottom
        (35, 70)    # Top
    ]
    
    # Consumption model parameters (from Fig. 2)
    R_I = [3.44, 3.44, 3.44, 3.44]
    ALPHA_I = [0.036, 0.036, 0.036, 0.036]
    BETA_I = [0.91, 0.91, 0.91, 0.91]
    
    # Communication
    EMITTER_CHANNEL = 1
    RECEIVER_CHANNEL = 1

class ExperimentConfig:
    """Configurations for specific experiments"""
    
    @staticmethod
    def experiment_1_surge():
        """Growth rate surge in patch 1"""
        return {
            'surge_start': 500,
            'surge_end': 600,
            'surge_patch': 0,
            'surge_rate': 5.0
        }
    
    @staticmethod
    def experiment_2_failures():
        """Robot failures"""
        return {
            'failure_start': 500,
            'failure_end': 1500,
            'num_failures': 15
        }