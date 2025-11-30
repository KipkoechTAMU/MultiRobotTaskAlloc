from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import ContinuousSpace
from agent import RobotAgent, Config, PoissonClock
import random
import math

class ResourceModel(Model):
    """
    The Supervisor/Environment Model.
    Manages resource dynamics, trash spawning, and population state.
    """
    def __init__(self, num_robots=4, width=40, height=40, alpha=0.2):
        self.num_robots = num_robots
        self.width = width
        self.height = height
        self.alpha = alpha # Consumption rate
        self.schedule = SimultaneousActivation(self)
        
        # Use ContinuousSpace for non-discrete movement
        self.grid = ContinuousSpace(width, height, torus=False)
        self.running = True
        self.dt = 1.0 # Mesa step size (1 second)
        
        # System state (4 patches) - Mapped from your original code
        self.q = [0.1, 0.1, 0.1, 0.1]  # Resource levels (0-1)
        self.x = [1.0/num_robots] * Config.NUM_TASKS # Population distribution (starts even)
        self.w = [0.5, 0.5, 0.5, 0.5]  # Growth rates
        
        # Trash management
        self.trash_objects = []
        self.trash_spawn_rate = 1.0  # 1 trash/second
        self.max_trash = 50
        self.next_trash_id = 0
        
        # 1. Create Robots
        for i in range(self.num_robots):
            a = RobotAgent(i, self)
            self.schedule.add(a)
            # Place agent at its initial random position
            self.grid.place_agent(a, a.position)
            
        # 2. Update initial population distribution (x_i = robot_count_i / total_robots)
        self.update_population_distribution()
        
    def update_population_distribution(self):
        """Calculates the population share (x_i) in each task."""
        task_counts = [0] * Config.NUM_TASKS
        for agent in self.schedule.agents:
            task_counts[agent.current_task] += 1
            
        self.x = [count / self.num_robots for count in task_counts]
        return task_counts

    def update_resources(self):
        """
        Update resource levels using equation: q̇_i = -F_i(q_i, x_i) + w_i
        """
        for i in range(Config.NUM_TASKS):
            # Consumption function: F_i = alpha * x_i * (1 + q_i)
            consumption = self.alpha * self.x[i] * (1.0 + self.q[i])
            
            # Update: dq/dt = w_i - F_i
            dq = (self.w[i] - consumption) * self.dt
            self.q[i] += dq
            
            # Clamp to valid range [0, 1]
            self.q[i] = max(0.0, min(1.0, self.q[i]))

    def spawn_trash(self):
        """
        Use Poisson process to spawn trash objects.
        """
        if len(self.trash_objects) >= self.max_trash:
            return
        
        # Poisson probability for the step dt
        prob = self.trash_spawn_rate * self.dt
        
        if random.random() < prob:
            weights = [max(0.1, q) for q in self.q]
            total = sum(weights)
            weights = [w/total for w in weights]
            
            patch_id = random.choices(range(Config.NUM_TASKS), weights=weights)[0]
            
            # Patch area: centered at 10, 30, with a 10x10 radius.
            patch_centers = [
                (10, 10), (10, 30), (30, 10), (30, 30)
            ]
            
            base_x, base_y = patch_centers[patch_id]
            
            # Random offset within the 20x20 patch area (±10 units)
            offset_x = random.uniform(-10, 10)
            offset_y = random.uniform(-10, 10)
            
            trash = {
                'id': self.next_trash_id,
                'x': base_x + offset_x,
                'y': base_y + offset_y,
                'patch_id': patch_id,
                'spawn_time': self.schedule.time * self.dt
            }
            
            self.trash_objects.append(trash)
            self.next_trash_id += 1
            
            # Increase resource level upon trash spawn
            self.q[patch_id] = min(1.0, self.q[patch_id] + 0.02)
            
    def report_task_change(self, robot_id, old_task, new_task):
        """Handles task change reports from agents."""
        # The agent's task is already changed, just update global state
        self.update_population_distribution()
        print(f"Time {self.schedule.time * self.dt:.1f}s: Robot {robot_id} switched from T{old_task} to T{new_task}")

    def report_trash_collected(self, trash_id):
        """Handles trash collection reports from agents."""
        trash_to_remove = next((t for t in self.trash_objects if t['id'] == trash_id), None)
        
        if trash_to_remove:
            self.trash_objects.remove(trash_to_remove)
            
            # Decrease resource level
            patch_id = trash_to_remove['patch_id']
            self.q[patch_id] = max(0.0, self.q[patch_id] - 0.05)
            
            # print(f"Trash {trash_id} collected from Patch {patch_id}.")
            
    def step(self):
        """
        Main Supervisor control loop.
        """
        # 1. Update system dynamics
        self.update_resources()
        
        # 2. Spawn trash objects
        self.spawn_trash()
        
        # 3. Agents take a step (move, revise tasks)
        self.schedule.step()
        
        # 4. Update population distribution for the next step's calculation
        self.update_population_distribution()
        
        if self.schedule.time % 10 == 0:
            print(f"\n--- TIME {self.schedule.time * self.dt:.1f}s ---")
            print(f"Resources q: {[f'{q:.3f}' for q in self.q]}")
            print(f"Population x: {[f'{x:.3f}' for x in self.x]}")
            print(f"Trash objects: {len(self.trash_objects)}")