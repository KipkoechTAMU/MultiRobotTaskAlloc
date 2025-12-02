"""
Supervisor Controller for Multi-Robot Trash Collection
Manages:
- Trash object spawning (Poisson process)
- System state tracking (q and x)
- Statistics collection and display
- Communication with robots
"""

from controller import Supervisor
import numpy as np
import random
import math
import struct

# Simulation parameters
TIME_STEP = 64
NUM_ROBOTS = 40
NUM_PATCHES = 4

# Patch parameters (from Example 1)
R = [3.44, 3.44, 3.44, 3.44]
ALPHA = [0.036, 0.036, 0.036, 0.036]
BETA = [0.91, 0.91, 0.91, 0.91]
W = [0.5, 0.5, 0.5, 0.5]  # Growth rates (trash/second)

# Patch boundaries
PATCH_BOUNDS = [
    (-6.75, -0.75, 0.75, 6.75),   # Patch 1: (x_min, x_max, y_min, y_max)
    (-6.75, -0.75, -6.75, -0.75), # Patch 2
    (0.75, 6.75, -6.75, -0.75),   # Patch 3
    (0.75, 6.75, 0.75, 6.75)      # Patch 4
]

TRASH_SIZE = 0.05  # Size of trash objects

class SupervisorController:
    def __init__(self):
        self.supervisor = Supervisor()
        self.timestep = int(self.supervisor.getBasicTimeStep())
        
        # Communication
        self.emitter = self.supervisor.getDevice('emitter')
        self.receiver = self.supervisor.getDevice('receiver')
        self.receiver.enable(self.timestep)
        
        # State variables
        self.q = [0.0] * NUM_PATCHES  # Trash volume in each patch
        self.x = [0.25] * NUM_PATCHES  # Robot distribution
        self.robot_assignments = [0] * NUM_ROBOTS  # Track which patch each robot is in
        
        # Trash objects
        self.trash_objects = [[] for _ in range(NUM_PATCHES)]
        self.trash_id_counter = 0
        
        # Poisson process for trash generation
        self.last_spawn_time = [0.0] * NUM_PATCHES
        self.next_spawn_time = [self.sample_spawn_time(i) for i in range(NUM_PATCHES)]
        
        # Statistics
        self.time = 0
        self.stats_update_interval = 1000  # Update every 1 second
        self.last_stats_time = 0
        
        print("Supervisor initialized")
        print(f"Growth rates: {W}")
        print(f"Initial distribution x: {self.x}")
    
    def sample_spawn_time(self, patch_idx):
        """Sample next trash spawn time from exponential distribution"""
        if W[patch_idx] == 0:
            return float('inf')
        rate = W[patch_idx]  # Objects per second
        return random.expovariate(rate) * 1000  # Convert to ms
    
    def spawn_trash(self, patch_idx):
        """Spawn a trash object in the specified patch"""
        bounds = PATCH_BOUNDS[patch_idx]
        x_min, x_max, y_min, y_max = bounds
        
        # Random position within patch
        x = random.uniform(x_min, x_max)
        y = random.uniform(y_min, y_max)
        z = TRASH_SIZE / 2
        
        # Create trash object
        trash_name = f"trash_{self.trash_id_counter}"
        self.trash_id_counter += 1
        
        trash_string = f"""
DEF {trash_name} Solid {{
  translation {x} {y} {z}
  children [
    Shape {{
      appearance PBRAppearance {{
        baseColor 1 0 0
        metalness 0
        roughness 0.5
      }}
      geometry Box {{
        size {TRASH_SIZE} {TRASH_SIZE} {TRASH_SIZE}
      }}
    }}
  ]
  name "{trash_name}"
  contactMaterial "trash"
  boundingObject Box {{
    size {TRASH_SIZE} {TRASH_SIZE} {TRASH_SIZE}
  }}
  physics Physics {{
    density 100
  }}
}}
"""
        
        # Import the trash object
        root = self.supervisor.getRoot()
        children_field = root.getField('children')
        children_field.importMFNodeFromString(-1, trash_string)
        
        # Track the trash object
        trash_node = self.supervisor.getFromDef(trash_name)
        if trash_node:
            self.trash_objects[patch_idx].append(trash_node)
            self.q[patch_idx] += 1.0
            print(f"Spawned trash in patch {patch_idx}. q = {self.q}")
    
    def check_trash_spawning(self):
        """Check and spawn trash based on Poisson process"""
        current_time = self.supervisor.getTime() * 1000  # Convert to ms
        
        for i in range(NUM_PATCHES):
            if current_time >= self.last_spawn_time[i] + self.next_spawn_time[i]:
                self.spawn_trash(i)
                self.last_spawn_time[i] = current_time
                self.next_spawn_time[i] = self.sample_spawn_time(i)
    
    def receive_robot_status(self):
        """Receive status updates from robots using native floats"""
        while self.receiver.getQueueLength() > 0:
            # Use getFloats() to read the message (should contain 3 floats)
            floats = self.receiver.getFloats()
            
            if len(floats) == 3:
                # Unpack the list of floats
                robot_id = int(floats[0])
                current_patch = int(floats[1])
                # trash_collected = floats[2]  # We don't use this directly here, but it's received
                
                if 0 <= robot_id < NUM_ROBOTS:
                    # current_patch is now guaranteed to be a robust integer
                    self.robot_assignments[robot_id] = current_patch
            
            self.receiver.nextPacket()
    
    def update_distribution(self):
        """Update robot distribution x based on assignments"""
        counts = [0] * NUM_PATCHES
        for assignment in self.robot_assignments:
            if 0 <= assignment < NUM_PATCHES:
                counts[assignment] += 1
        
        # Calculate proportions
        self.x = [count / NUM_ROBOTS for count in counts]
    
    def broadcast_state(self):
        """Broadcast q and x to all robots using native Webots float list"""
        # Create a list of 9 floats
        message_floats = [
            self.q[0], self.q[1], self.q[2], self.q[3],
            self.x[0], self.x[1], self.x[2], self.x[3],
            float(self.time)
        ]
        # Send the list directly to the emitter
        self.emitter.send(message_floats)
    
    def consumption_rate(self, qi, xi, patch_idx):
        """Consumption rate F_i from Equation (3)"""
        if xi == 0:
            return 0
        exp_term = math.exp(ALPHA[patch_idx] * qi)
        saturating = (exp_term - 1) / (exp_term + 1)
        return R[patch_idx] * saturating * (xi ** BETA[patch_idx])
    
    def update_trash_volumes(self, dt):
        """Update trash volumes based on dynamics (Equation 2)"""
        for i in range(NUM_PATCHES):
            # dq/dt = -F_i(q_i, x_i) + w_i
            F_i = self.consumption_rate(self.q[i], self.x[i], i)
            dq = (-F_i + W[i]) * dt
            self.q[i] = max(0, self.q[i] + dq)
    
    def print_statistics(self):
        """Print simulation statistics"""
        print("\n" + "="*60)
        print(f"Time: {self.time:.1f}s")
        print("-"*60)
        print("Patch | Trash q_i | Robots x_i | Consumption F_i | dq/dt")
        print("-"*60)
        
        for i in range(NUM_PATCHES):
            F_i = self.consumption_rate(self.q[i], self.x[i], i)
            dq_dt = -F_i + W[i]
            robot_count = int(self.x[i] * NUM_ROBOTS)
            
            print(f"  {i+1}   |  {self.q[i]:7.2f}  | {robot_count:2d} ({self.x[i]:.2%}) "
                  f"|     {F_i:6.3f}      | {dq_dt:+6.3f}")
        
        print("-"*60)
        total_trash = sum(self.q)
        max_trash = max(self.q)
        balance = 1 - (max(self.x) - min(self.x))
        
        print(f"Total trash: {total_trash:.2f}")
        print(f"Max trash:   {max_trash:.2f}")
        print(f"Balance:     {balance:.3f}")
        print(f"Convergence (γ*): {total_trash/NUM_PATCHES:.2f}")
        print("="*60 + "\n")
    
    def remove_trash_objects(self, patch_idx, count):
        """Remove trash objects from patch (simulating collection)"""
        removed = 0
        for trash_node in self.trash_objects[patch_idx][:]:
            if trash_node and removed < count:
                trash_node.remove()
                self.trash_objects[patch_idx].remove(trash_node)
                removed += 1
                self.q[patch_idx] = max(0, self.q[patch_idx] - 1.0)
        
        return removed
    
    def simulate_collection(self):
        """Simulate trash collection based on robot distribution"""
        # This is a simplified collection model
        # In reality, individual robots would pick up trash
        dt = self.timestep / 1000.0  # Convert to seconds
        
        for i in range(NUM_PATCHES):
            if self.x[i] > 0 and len(self.trash_objects[i]) > 0:
                # Collection rate based on consumption function
                F_i = self.consumption_rate(self.q[i], self.x[i], i)
                objects_to_remove = int(F_i * dt)
                
                if objects_to_remove > 0:
                    self.remove_trash_objects(i, objects_to_remove)
    
    def run(self):
        """Main supervisor loop"""
        while self.supervisor.step(self.timestep) != -1:
            self.time = self.supervisor.getTime()
            
            # Receive robot status
            self.receive_robot_status()
            
            # Update robot distribution
            self.update_distribution()
            
            # Check for trash spawning
            self.check_trash_spawning()
            
            # Simulate trash collection
            self.simulate_collection()
            
            # Update trash volumes based on dynamics
            dt = self.timestep / 1000.0
            # self.update_trash_volumes(dt)  # Commented out - using actual object count
            
            # Broadcast state to robots
            self.broadcast_state()
            
            # Print statistics periodically
            if (self.time * 1000) - self.last_stats_time >= self.stats_update_interval:
                self.print_statistics()
                self.last_stats_time = self.time * 1000

if __name__ == "__main__":
    supervisor = SupervisorController()
    supervisor.run()
