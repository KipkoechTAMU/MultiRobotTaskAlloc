"""
Multi-Robot Trash Collection Controller
Based on Park, Zhong, Leonard (ICRA 2021)

Implements:
- Game-theoretic task allocation
- Poisson clock revision protocol
- Payoff-based decision making
- Finite state machine for robot behavior
"""

from controller import Robot, GPS, Compass, DistanceSensor, Emitter, Receiver
import numpy as np
import random
import math
import struct

# Simulation parameters
TIME_STEP = 64  # ms
NUM_ROBOTS = 40
NUM_PATCHES = 4
LAMBDA = 0.125  # Poisson clock parameter (1/8 seconds)
RHO = 1/600     # Task revision protocol rate
NU = 0          # Payoff mechanism weight (0 for model-free)

# Patch parameters (from Example 1 in paper)
R = [3.44, 3.44, 3.44, 3.44]      # Maximum consumption rate
ALPHA = [0.036, 0.036, 0.036, 0.036]  # Saturation parameter
BETA = [0.91, 0.91, 0.91, 0.91]   # Power parameter
W = [0.5, 0.5, 0.5, 0.5]          # Growth rates

# Patch centers
PATCH_CENTERS = [
    (-3.75, 3.75),   # Patch 1 (top-left)
    (-3.75, -3.75),  # Patch 2 (bottom-left)
    (3.75, -3.75),   # Patch 3 (bottom-right)
    (3.75, 3.75)     # Patch 4 (top-right)
]

# Dumpster locations
DUMPSTERS = [
    (-6.5, 6.5),    # Dumpster 1
    (-6.5, -6.5),   # Dumpster 2
    (6.5, -6.5),    # Dumpster 3
    (6.5, 6.5)      # Dumpster 4
]

# Robot states
STATE_FORAGING = 0
STATE_VISUAL_SERVOING = 1
STATE_PICKUP = 2
STATE_COLLISION_AVOIDANCE = 3
STATE_TRANSITION = 4
STATE_DUMP = 5

class RobotController:
    def __init__(self):
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())
        
        # Get robot ID from name
        self.name = self.robot.getName()
        self.robot_id = int(self.name.split('_')[1])
        
        # Initialize devices
        self.gps = self.robot.getDevice('gps')
        self.gps.enable(self.timestep)
        
        self.compass = self.robot.getDevice('compass')
        self.compass.enable(self.timestep)
        
        # Initialize motors
        self.left_motor = self.robot.getDevice('left wheel motor')
        self.right_motor = self.robot.getDevice('right wheel motor')
        self.left_motor.setPosition(float('inf'))
        self.right_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)
        
        # Initialize distance sensors
        self.distance_sensors = []
        for i in range(8):
            sensor = self.robot.getDevice(f'ps{i}')
            sensor.enable(self.timestep)
            self.distance_sensors.append(sensor)
        
        # Communication
        self.emitter = self.robot.getDevice('emitter')
        self.receiver = self.robot.getDevice('receiver')
        self.receiver.enable(self.timestep)
        
        # State variables
        self.state = STATE_FORAGING
        self.current_patch = self.robot_id % NUM_PATCHES  # Initial assignment
        self.target_patch = self.current_patch
        self.trash_collected = 0
        self.max_capacity = 10
        
        # Game-theoretic variables
        self.q = [0.0] * NUM_PATCHES  # Trash volumes (received from supervisor)
        self.x = [0.25] * NUM_PATCHES  # Robot distribution
        self.last_revision_time = 0
        self.next_revision_time = self.sample_poisson_time()
        
        # Navigation
        self.target_position = PATCH_CENTERS[self.current_patch]
        self.collision_avoidance_time = 0
        
        print(f"Robot {self.robot_id} initialized in patch {self.current_patch}")
    
    def sample_poisson_time(self):
        """Sample next revision time from exponential distribution"""
        return random.expovariate(LAMBDA) * 1000  # Convert to ms
    
    def consumption_rate(self, qi, xi, patch_idx):
        """Consumption rate F_i from Equation (3)"""
        exp_term = math.exp(ALPHA[patch_idx] * qi)
        saturating = (exp_term - 1) / (exp_term + 1)
        return R[patch_idx] * saturating * (xi ** BETA[patch_idx])
    
    def payoff(self, patch_idx):
        """Payoff mechanism from Equation (6)"""
        if NU == 0:
            # Model-free: payoff is just trash volume
            return self.q[patch_idx]
        else:
            # Model-based
            gamma_star = max(self.q)
            return (self.q[patch_idx] + 
                   NU * (-self.consumption_rate(gamma_star, self.x[patch_idx], patch_idx) + 
                         W[patch_idx]))
    
    def revision_protocol(self):
        """Task revision protocol from Equation (7)"""
        # Calculate payoffs for all patches
        payoffs = [self.payoff(i) for i in range(NUM_PATCHES)]
        
        # Current patch payoff
        current_payoff = payoffs[self.current_patch]
        
        # Calculate switching probabilities
        switch_probs = []
        for i in range(NUM_PATCHES):
            if i == self.current_patch:
                switch_probs.append(0)
            else:
                diff = payoffs[i] - current_payoff
                switch_probs.append(RHO * max(0, diff))
        
        # Normalize probabilities
        total = sum(switch_probs)
        if total > 0:
            switch_probs = [p / total for p in switch_probs]
        
        # Stay probability
        stay_prob = 1 - sum(switch_probs)
        
        # Make decision
        rand = random.random()
        cumulative = 0
        
        for i in range(NUM_PATCHES):
            if i != self.current_patch:
                cumulative += switch_probs[i]
                if rand < cumulative:
                    # Switch to patch i
                    print(f"Robot {self.robot_id}: Switching from patch {self.current_patch} to {i}")
                    print(f"  Payoffs: {[f'{p:.2f}' for p in payoffs]}")
                    return i
        
        # Stay in current patch
        return self.current_patch
    
    def receive_state_info(self):
        """Receive q and x from supervisor"""
        while self.receiver.getQueueLength() > 0:
            try:
                # Use getFloats() - This is the cleanest way for float-only messages
                # It handles the underlying byte-to-float conversion correctly.
                floats = self.receiver.getFloats()
                
                if len(floats) == 9:
                    # First 4 are q values
                    self.q = list(floats[0:4])
                    # Next 4 are x values
                    self.x = list(floats[4:8])
                    # Last one is time (we can ignore)
                else:
                    if not hasattr(self, '_warned_size'):
                        # This warning likely comes from the supervisor's 'iif' status message 
                        # being incorrectly picked up by the robot's receiver, 
                        # which is not a 9-float message.
                        print(f"Robot {self.robot_id}: Expected 9 floats, got {len(floats)}")
                        self._warned_size = True
                    
            except Exception as e:
                if not hasattr(self, '_warned'):
                    print(f"Robot {self.robot_id}: Error: {e}")
                    self._warned = True
            
            self.receiver.nextPacket()
    
    def send_status(self):
        """Send robot status to supervisor using native floats"""
        # Pack: robot_id, current_patch, trash_collected (all converted to floats)
        message_floats = [
            float(self.robot_id), 
            float(self.current_patch), 
            self.trash_collected
        ]
        self.emitter.send(message_floats)
    def get_position(self):
        """Get current robot position"""
        pos = self.gps.getValues()
        return (pos[0], pos[1])
    
    def get_heading(self):
        """Get current heading angle"""
        north = self.compass.getValues()
        heading = math.atan2(north[0], north[1])
        return heading
    
    def distance_to(self, target):
        """Calculate distance to target position"""
        pos = self.get_position()
        dx = target[0] - pos[0]
        dy = target[1] - pos[1]
        return math.sqrt(dx**2 + dy**2)
    
    def angle_to(self, target):
        """Calculate angle to target position"""
        pos = self.get_position()
        dx = target[0] - pos[0]
        dy = target[1] - pos[1]
        target_angle = math.atan2(dy, dx)
        heading = self.get_heading()
        angle_diff = target_angle - heading
        
        # Normalize to [-pi, pi]
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        return angle_diff
    
    def detect_collision(self):
        """Check for obstacles using distance sensors"""
        threshold = 80  # Sensor threshold
        for sensor in self.distance_sensors:
            if sensor.getValue() > threshold:
                return True
        return False
    
    def move_to_target(self, target, max_speed=6.28):
        """Simple proportional controller to move to target"""
        angle_diff = self.angle_to(target)
        
        # Proportional control
        angular_speed = 2.0 * angle_diff
        
        # Set motor speeds
        left_speed = max_speed - angular_speed
        right_speed = max_speed + angular_speed
        
        # Clamp speeds
        left_speed = max(-max_speed, min(max_speed, left_speed))
        right_speed = max(-max_speed, min(max_speed, right_speed))
        
        self.left_motor.setVelocity(left_speed)
        self.right_motor.setVelocity(right_speed)
    
    def stop(self):
        """Stop the robot"""
        self.left_motor.setVelocity(0)
        self.right_motor.setVelocity(0)
    
    def collision_avoidance(self):
        """Simple collision avoidance behavior"""
        # Get sensor values
        sensors = [s.getValue() for s in self.distance_sensors]
        
        # Weighted sum for steering
        left_obstacle = sensors[0] + sensors[1] + sensors[2]
        right_obstacle = sensors[5] + sensors[6] + sensors[7]
        
        # Avoid obstacles
        left_speed = 3.0 - 0.01 * left_obstacle
        right_speed = 3.0 - 0.01 * right_obstacle
        
        self.left_motor.setVelocity(left_speed)
        self.right_motor.setVelocity(right_speed)
    
    def check_revision_time(self):
        """Check if it's time to revise task selection (Poisson clock)"""
        current_time = self.robot.getTime() * 1000  # Convert to ms
        
        if current_time >= self.last_revision_time + self.next_revision_time:
            # Time for revision
            new_patch = self.revision_protocol()
            
            if new_patch != self.current_patch:
                self.target_patch = new_patch
                self.state = STATE_TRANSITION
            
            # Sample next revision time
            self.last_revision_time = current_time
            self.next_revision_time = self.sample_poisson_time()
    
    def run(self):
        """Main control loop"""
        while self.robot.step(self.timestep) != -1:
            # Receive state information
            self.receive_state_info()
            
            # Send status
            self.send_status()
            
            # Check for task revision (Poisson clock)
            self.check_revision_time()
            
            # Finite state machine
            if self.state == STATE_FORAGING:
                # Navigate within current patch
                patch_center = PATCH_CENTERS[self.current_patch]
                
                # Random foraging within patch
                if random.random() < 0.01:  # Occasionally pick new random point
                    offset_x = random.uniform(-2, 2)
                    offset_y = random.uniform(-2, 2)
                    self.target_position = (patch_center[0] + offset_x, 
                                          patch_center[1] + offset_y)
                
                # Check for collisions
                if self.detect_collision():
                    self.state = STATE_COLLISION_AVOIDANCE
                    self.collision_avoidance_time = self.robot.getTime()
                else:
                    self.move_to_target(self.target_position, max_speed=4.0)
                
                # Check if trash basket is full
                if self.trash_collected >= self.max_capacity:
                    self.state = STATE_DUMP
                    # Find nearest dumpster
                    nearest_dumpster = min(DUMPSTERS, 
                                         key=lambda d: self.distance_to(d))
                    self.target_position = nearest_dumpster
            
            elif self.state == STATE_COLLISION_AVOIDANCE:
                self.collision_avoidance()
                
                # Return to foraging after 1 second
                if self.robot.getTime() - self.collision_avoidance_time > 1.0:
                    self.state = STATE_FORAGING
            
            elif self.state == STATE_TRANSITION:
                # Transition to new patch
                target_patch_center = PATCH_CENTERS[self.target_patch]
                self.move_to_target(target_patch_center, max_speed=6.0)
                
                # Check if reached target patch
                if self.distance_to(target_patch_center) < 1.0:
                    self.current_patch = self.target_patch
                    self.state = STATE_FORAGING
                    print(f"Robot {self.robot_id}: Arrived at patch {self.current_patch}")
                
                # Collision avoidance during transition
                if self.detect_collision():
                    self.state = STATE_COLLISION_AVOIDANCE
                    self.collision_avoidance_time = self.robot.getTime()
            
            elif self.state == STATE_DUMP:
                # Navigate to dumpster
                self.move_to_target(self.target_position, max_speed=5.0)
                
                # Check if reached dumpster
                if self.distance_to(self.target_position) < 0.5:
                    # Empty trash
                    self.trash_collected = 0
                    self.state = STATE_FORAGING
                    print(f"Robot {self.robot_id}: Emptied trash at dumpster")

if __name__ == "__main__":
    controller = RobotController()
    controller.run()
