"""
Finite state machine for robot behavior
"""
from enum import Enum
from typing import Optional, Tuple
import numpy as np

from shared.constants import RobotState
from shared.config import Config
from shared.utils import distance, angle_to_target

class FiniteStateMachine:
    """
    Controls robot behavior through states:
    - FORAGING: Search for trash in current patch
    - VISUAL_SERVOING: Approach detected object
    - OBJECT_PICKUP: Pick up object
    - COLLISION_AVOIDANCE: Avoid obstacles
    - TRANSITION: Move to different patch
    - EMPTYING_BASKET: Go to dumpster
    """
    def __init__(self, robot_id: int, robot):
        self.robot_id = robot_id
        self.robot = robot
        
        self.state = RobotState.FORAGING
        self.current_task = None
        self.basket_count = 0
        
        # Target tracking
        self.target_position = None
        self.detected_object = None
        
        # Get robot devices
        self.left_motor = robot.getDevice('left wheel motor')
        self.right_motor = robot.getDevice('right wheel motor')
        self.left_motor.setPosition(float('inf'))
        self.right_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)
        
        self.gps = robot.getDevice('gps')
        self.gps.enable(int(robot.getBasicTimeStep()))
        
        self.compass = robot.getDevice('compass')
        self.compass.enable(int(robot.getBasicTimeStep()))
        
        # Distance sensors for collision avoidance
        self.distance_sensors = []
        for i in range(8):
            sensor = robot.getDevice(f'ps{i}')
            sensor.enable(int(robot.getBasicTimeStep()))
            self.distance_sensors.append(sensor)
        
        # Camera for object detection
        self.camera = robot.getDevice('camera')
        self.camera.enable(int(robot.getBasicTimeStep()))
        
        # Manipulator (simplified)
        self.gripper = robot.getDevice('gripper')
    
    def get_position(self) -> Tuple[float, float]:
        """Get current robot position"""
        pos = self.gps.getValues()
        return (pos[0], pos[1])
    
    def get_heading(self) -> float:
        """Get current heading angle"""
        compass_values = self.compass.getValues()
        return np.arctan2(compass_values[0], compass_values[1])
    
    def set_task(self, task_id: int):
        """Change current task and transition to new patch"""
        if task_id != self.current_task:
            self.current_task = task_id
            self.state = RobotState.TRANSITION
            self.target_position = Config.PATCH_POSITIONS[task_id]
    
    def update(self) -> RobotState:
        """
        Execute one step of FSM
        
        Returns:
            Current state after update
        """
        if self.state == RobotState.FORAGING:
            self._foraging_behavior()
        
        elif self.state == RobotState.VISUAL_SERVOING:
            self._visual_servoing_behavior()
        
        elif self.state == RobotState.OBJECT_PICKUP:
            self._pickup_behavior()
        
        elif self.state == RobotState.COLLISION_AVOIDANCE:
            self._collision_avoidance_behavior()
        
        elif self.state == RobotState.TRANSITION:
            self._transition_behavior()
        
        elif self.state == RobotState.EMPTYING_BASKET:
            self._emptying_behavior()
        
        return self.state
    
    def _foraging_behavior(self):
        """Search for trash objects in current patch"""
        # Check if basket is full
        if self.basket_count >= Config.BASKET_CAPACITY:
            self.state = RobotState.EMPTYING_BASKET
            # Find nearest dumpster
            current_pos = self.get_position()
            nearest_dumpster = min(
                Config.DUMPSTER_POSITIONS,
                key=lambda d: distance(current_pos, d)
            )
            self.target_position = nearest_dumpster
            return
        
        # Check for obstacles
        if self._obstacle_detected():
            self.state = RobotState.COLLISION_AVOIDANCE
            return
        
        # Try to detect trash object
        detected_obj = self._detect_object()
        if detected_obj is not None:
            self.detected_object = detected_obj
            self.state = RobotState.VISUAL_SERVOING
            return
        
        # Random walk within patch
        self._random_walk()
    
    def _visual_servoing_behavior(self):
        """Approach detected object"""
        if self.detected_object is None:
            self.state = RobotState.FORAGING
            return
        
        # Check if close enough to pickup
        current_pos = self.get_position()
        obj_distance = distance(current_pos, self.detected_object)
        
        if obj_distance < 0.3:  # Within pickup range
            self.state = RobotState.OBJECT_PICKUP
            return
        
        # Move toward object
        self._move_to_target(self.detected_object)
    
    def _pickup_behavior(self):
        """Pick up object"""
        # Stop motors
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)
        
        # Simulate pickup (in real implementation, control gripper)
        self.basket_count += 1
        self.detected_object = None
        
        print(f"Robot {self.robot_id}: Picked up object ({self.basket_count}/{Config.BASKET_CAPACITY})")
        
        # Return to foraging
        self.state = RobotState.FORAGING
    
    def _collision_avoidance_behavior(self):
        """Avoid obstacles using potential field"""
        # Get sensor readings
        sensor_values = [s.getValue() for s in self.distance_sensors]
        
        # If no obstacles, return to previous behavior
        if max(sensor_values) < 80:  # Threshold
            self.state = RobotState.FORAGING
            return
        
        # Simple avoidance: turn away from obstacle
        left_obstacle = sum(sensor_values[:3])
        right_obstacle = sum(sensor_values[5:])
        
        if left_obstacle > right_obstacle:
            # Turn right
            self.left_motor.setVelocity(3.0)
            self.right_motor.setVelocity(-1.0)
        else:
            # Turn left
            self.left_motor.setVelocity(-1.0)
            self.right_motor.setVelocity(3.0)
    
    def _transition_behavior(self):
        """Move to new patch"""
        if self.target_position is None:
            self.state = RobotState.FORAGING
            return
        
        current_pos = self.get_position()
        dist = distance(current_pos, self.target_position)
        
        # Arrived at patch
        if dist < 2.0:
            print(f"Robot {self.robot_id}: Arrived at patch {self.current_task}")
            self.target_position = None
            self.state = RobotState.FORAGING
            return
        
        # Move toward patch center
        self._move_to_target(self.target_position)
    
    def _emptying_behavior(self):
        """Move to dumpster and empty basket"""
        if self.target_position is None:
            self.basket_count = 0
            self.state = RobotState.FORAGING
            return
        
        current_pos = self.get_position()
        dist = distance(current_pos, self.target_position)
        
        # Arrived at dumpster
        if dist < 1.0:
            print(f"Robot {self.robot_id}: Emptying basket at dumpster")
            self.basket_count = 0
            self.target_position = None
            self.state = RobotState.FORAGING
            return
        
        # Move toward dumpster
        self._move_to_target(self.target_position)
    
    def _obstacle_detected(self) -> bool:
        """Check if obstacle is nearby"""
        sensor_values = [s.getValue() for s in self.distance_sensors]
        return max(sensor_values) > 80
    
    def _detect_object(self) -> Optional[Tuple[float, float]]:
        """
        Detect trash object using camera
        
        Returns:
            Object position if detected, None otherwise
        """
        # Simplified detection using camera
        # In real implementation, use image processing
        image = self.camera.getImage()
        if image is None:
            return None
        
        # Placeholder: random detection with low probability
        if np.random.rand() < 0.01:
            # Return random position near robot
            current_pos = self.get_position()
            obj_pos = (
                current_pos[0] + np.random.uniform(-2, 2),
                current_pos[1] + np.random.uniform(-2, 2)
            )
            return obj_pos
        
        return None
    
    def _random_walk(self):
        """Random walk behavior"""
        # Simple random walk
        if np.random.rand() < 0.05:  # Change direction occasionally
            self.left_motor.setVelocity(np.random.uniform(2, 4))
            self.right_motor.setVelocity(np.random.uniform(2, 4))
        # Otherwise maintain current velocity
    
    def _move_to_target(self, target: Tuple[float, float]):
        """Move toward target position"""
        current_pos = self.get_position()
        current_heading = self.get_heading()
        
        # Calculate desired heading
        desired_heading = angle_to_target(current_pos, target)
        heading_error = desired_heading - current_heading
        
        # Normalize angle to [-π, π]
        heading_error = np.arctan2(np.sin(heading_error), np.cos(heading_error))
        
        # Simple proportional controller
        K_p = 2.0
        base_speed = 3.0
        
        left_speed = base_speed + K_p * heading_error
        right_speed = base_speed - K_p * heading_error
        
        # Clamp speeds
        left_speed = np.clip(left_speed, -6.0, 6.0)
        right_speed = np.clip(right_speed, -6.0, 6.0)
        
        self.left_motor.setVelocity(left_speed)
        self.right_motor.setVelocity(right_speed)
    
    def stop(self):
        """Stop all motion"""
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)