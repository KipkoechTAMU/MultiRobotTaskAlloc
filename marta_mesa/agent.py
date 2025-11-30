import numpy as np
import random
from mesa import Agent
import math

# --- Configuration (Normally in shared/config.py) ---
class Config:
    POISSON_LAMBDA = 0.5  # Task revision rate (0.5 revisions per second)
    MOVEMENT_SPEED = 1.0
    NUM_TASKS = 4
    
# --- Poisson Clock (from your original code) ---
class PoissonClock:
    def __init__(self, lambda_param: float):
        self.lambda_param = lambda_param
        self.next_tick_time = 0.0
        self._generate_next_tick()
    
    def _generate_next_tick(self):
        # Time until next tick ~ Exp(λ)
        inter_arrival = np.random.exponential(1.0 / self.lambda_param)
        self.next_tick_time += inter_arrival
    
    def should_tick(self, current_time: float) -> bool:
        if current_time >= self.next_tick_time:
            self._generate_next_tick()
            return True
        return False

# --- Agent (Robot) Implementation ---
class RobotAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.robot_id = unique_id
        
        # State
        self.current_task = unique_id % Config.NUM_TASKS # Initial task assignment
        self.basket_count = 0
        self.position = self._get_initial_position(self.current_task)
        
        # Components
        self.clock = PoissonClock(Config.POISSON_LAMBDA)
        
        print(f"Robot {self.robot_id} initialized to Task {self.current_task}")

    def _get_initial_position(self, task_id):
        # Maps task ID (0-3) to a start position within the patch
        patch_coords = [
            (10, 10), # Task 0: Bottom-Left (15, 15 in WBT, using 10,10 center here)
            (10, 30), # Task 1: Top-Left
            (30, 10), # Task 2: Bottom-Right
            (30, 30)  # Task 3: Top-Right
        ]
        # Random initial position near the center of the patch
        cx, cy = patch_coords[task_id]
        return (cx + random.uniform(-5, 5), cy + random.uniform(-5, 5))

    def calculate_utility(self, q_i, x_i, w_i):
        """
        Calculates the expected utility (e.g., resource availability) for a task i.
        This is the core decision logic (DecisionMaker).
        """
        # A simple utility: high resource q_i and low population x_i are good.
        # Utility U_i = q_i / x_i (avoid division by zero by clamping x_i)
        
        # Get resource state from the model
        q = self.model.q[q_i]
        x = self.model.x[x_i]
        
        # Clamp population share to prevent division by zero
        # Add a small epsilon if it is zero, or return max utility
        x_clamped = max(0.01, x)
        
        # Utility function: Higher resource levels (q) and lower competition (x)
        utility = q / x_clamped
        
        return utility

    def revise_task(self):
        """
        Runs the task allocation algorithm.
        """
        # Get global state from the model
        q = self.model.q
        x = self.model.x
        w = self.model.w
        
        utilities = []
        for i in range(Config.NUM_TASKS):
            # Calculate utility U_i for task i
            utility = self.calculate_utility(i, i, i)
            utilities.append(utility)
            
        # Select the task with the highest utility
        new_task = np.argmax(utilities)
        
        if new_task != self.current_task:
            # Report task change to the Model (Supervisor)
            self.model.report_task_change(self.robot_id, self.current_task, new_task)
            self.current_task = new_task
            
    def move(self):
        """
        Simulates movement towards the center of the assigned patch.
        """
        patch_coords = [
            (10, 10), (10, 30), (30, 10), (30, 30) 
        ]
        target_x, target_y = patch_coords[self.current_task]
        current_x, current_y = self.pos
        
        # Calculate vector to target
        dx = target_x - current_x
        dy = target_y - current_y
        
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0.5: # If far enough, move
            # Normalize and scale by speed
            move_x = dx / distance * Config.MOVEMENT_SPEED
            move_y = dy / distance * Config.MOVEMENT_SPEED
            
            new_x = current_x + move_x * self.model.dt
            new_y = current_y + move_y * self.model.dt
            
            new_pos = (new_x, new_y)
            self.model.grid.move_agent(self, new_pos)
            self.position = new_pos
        else:
            # If close, simulate collecting trash
            self.collect_trash()


    def collect_trash(self):
        """
        Simulates collecting trash when near the patch center.
        """
        if self.model.trash_objects:
            # Find the closest trash in the current patch
            closest_trash = None
            min_dist_sq = float('inf')
            
            for trash in self.model.trash_objects:
                if trash['patch_id'] == self.current_task:
                    tx, ty = trash['x'], trash['y']
                    px, py = self.pos
                    
                    dist_sq = (tx - px)**2 + (ty - py)**2
                    
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        closest_trash = trash
            
            # If close to trash, collect it
            if closest_trash and min_dist_sq < 2.0: # Arbitrary collection radius
                self.model.report_trash_collected(closest_trash['id'])
                self.basket_count += 1
                
    def step(self):
        """
        Main simulation step for the agent.
        """
        # Check for task revision opportunity
        if self.clock.should_tick(self.model.schedule.time * self.model.dt):
            self.revise_task()
            
        # Agent movement and task execution
        self.move()