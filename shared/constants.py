"""
Physical and mathematical constants
"""
from enum import Enum

class RobotState(Enum):
    """Finite state machine states"""
    FORAGING = "foraging"
    VISUAL_SERVOING = "visual_servoing"
    OBJECT_PICKUP = "object_pickup"
    COLLISION_AVOIDANCE = "collision_avoidance"
    TRANSITION = "transition_to_patch"
    EMPTYING_BASKET = "emptying_basket"

class MessageType(Enum):
    """Communication message types"""
    STATE_UPDATE = "state_update"
    TASK_CHANGE = "task_change"
    ROBOT_STATUS = "robot_status"

# Physical constants
GRAVITY = 9.81
OBJECT_MASS = 0.1  # kg
DETECTION_RADIUS = 0.5  # meters
COLLISION_THRESHOLD = 0.3  # meters