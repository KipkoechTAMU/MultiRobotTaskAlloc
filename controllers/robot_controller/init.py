"""
Robot controller components

This module implements individual robot control:
- DecisionMaker: Task selection based on payoffs and revision protocol
- PoissonClock: Asynchronous task revision timing
- FiniteStateMachine: Low-level behavior control (foraging, pickup, etc.)

Additional components:
- Navigation: Path planning and obstacle avoidance
- Manipulation: Object pickup and placement
- Sensors: Sensor data processing
"""

from .decision_maker import DecisionMaker
from .poisson_clock import PoissonClock
from .finite_state_machine import FiniteStateMachine

# Optional components (may not be fully implemented yet)
try:
    from .navigation import Navigation
    _HAS_NAVIGATION = True
except ImportError:
    _HAS_NAVIGATION = False

try:
    from .manipulation import Manipulation
    _HAS_MANIPULATION = True
except ImportError:
    _HAS_MANIPULATION = False

try:
    from .sensors import SensorProcessor
    _HAS_SENSORS = True
except ImportError:
    _HAS_SENSORS = False

__all__ = [
    'DecisionMaker',
    'PoissonClock',
    'FiniteStateMachine',
]

# Add optional components to exports if available
if _HAS_NAVIGATION:
    __all__.append('Navigation')

if _HAS_MANIPULATION:
    __all__.append('Manipulation')

if _HAS_SENSORS:
    __all__.append('SensorProcessor')

__version__ = '0.1.0'

# Factory function to create all robot components
def create_robot_components(robot, robot_id, nu=0, lambda_param=8.0):
    """
    Factory function to create all robot controller components
    
    Args:
        robot: Webots Robot instance
        robot_id: Unique robot identifier
        nu: Payoff mechanism parameter
        lambda_param: Poisson clock rate parameter
    
    Returns:
        dict: Dictionary containing all components
        
    Example:
        components = create_robot_components(
            robot=self.robot,
            robot_id=5,
            nu=40
        )
        decision_maker = components['decision_maker']
        fsm = components['fsm']
    """
    components = {
        'decision_maker': DecisionMaker(robot_id, nu=nu),
        'poisson_clock': PoissonClock(lambda_param=lambda_param),
        'fsm': FiniteStateMachine(robot_id, robot)
    }
    
    # Add optional components if available
    if _HAS_NAVIGATION:
        components['navigation'] = Navigation(robot)
    
    if _HAS_MANIPULATION:
        components['manipulation'] = Manipulation(robot)
    
    if _HAS_SENSORS:
        components['sensors'] = SensorProcessor(robot)
    
    return components

# Helper to check component availability
def get_available_components():
    """
    Get list of available robot controller components
    
    Returns:
        dict: Availability status of each component
    """
    return {
        'decision_maker': True,
        'poisson_clock': True,
        'fsm': True,
        'navigation': _HAS_NAVIGATION,
        'manipulation': _HAS_MANIPULATION,
        'sensors': _HAS_SENSORS
    }