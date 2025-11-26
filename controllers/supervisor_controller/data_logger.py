"""
Data logging for experiment analysis
"""
import json
import csv
import numpy as np
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

class DataLogger:
    """
    Logs experimental data for post-processing and analysis
    """
    def __init__(self, experiment_name: str, log_dir: str = "logs"):
        self.experiment_name = experiment_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{experiment_name}_{timestamp}.csv"
        
        # Data buffers
        self.time_series = []
        self.resource_data = []
        self.population_data = []
        self.robot_counts = []
        self.growth_rates_history = []
        self.events = []
        
        # Initialize CSV
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Create CSV file with headers"""
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'time', 
                'q1', 'q2', 'q3', 'q4',
                'x1', 'x2', 'x3', 'x4',
                'robots_task1', 'robots_task2', 'robots_task3', 'robots_task4',
                'w1', 'w2', 'w3', 'w4'
            ])
    
    def log_state(self, time: float, q: List[float], x: List[float],
                  robot_counts: Dict[int, int], w: List[float]):
        """Log current state"""
        self.time_series.append(time)
        self.resource_data.append(q.copy())
        self.population_data.append(x.copy())
        self.robot_counts.append(list(robot_counts.values()))
        self.growth_rates_history.append(w.copy())
        
        # Write to CSV
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                time,
                *q,
                *x,
                *robot_counts.values(),
                *w
            ])
    
    def log_event(self, time: float, event_type: str, description: str):
        """Log discrete events (e.g., growth rate change, robot failure)"""
        self.events.append({
            'time': time,
            'type': event_type,
            'description': description
        })
    
    def save_metadata(self, config: Dict[str, Any]):
        """Save experiment configuration"""
        metadata_file = self.log_file.parent / f"{self.log_file.stem}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                'experiment': self.experiment_name,
                'config': config,
                'events': self.events
            }, f, indent=2)
    
    def get_data(self) -> Dict[str, Any]:
        """Return logged data as dictionary"""
        return {
            'time': np.array(self.time_series),
            'q': np.array(self.resource_data),
            'x': np.array(self.population_data),
            'robot_counts': np.array(self.robot_counts),
            'w': np.array(self.growth_rates_history),
            'events': self.events
        }
12. controllers/supervisor_controller/supervisor_controller.py
python"""
Main supervisor controller - orchestrates the simulation
"""
from controller import Supervisor
import numpy as np
from typing import List, Dict

from environment_model import EnvironmentModel
from state_manager import StateManager
from trash_spawner import TrashSpawner
from data_logger import DataLogger

from shared.config import Config, ExperimentConfig
from shared.communication import SupervisorBroadcast, Message, MessageType
from shared.constants import MessageType as MsgType

class SupervisorController:
    """
    Main supervisor that:
    1. Manages environment dynamics (q(t))
    2. Tracks robot distribution (x(t))
    3. Broadcasts global state to robots
    4. Logs data for analysis
    """
    def __init__(self):
        # Initialize Webots supervisor
        self.supervisor = Supervisor()
        self.timestep = int(self.supervisor.getBasicTimeStep())
        self.dt = self.timestep / 1000.0  # Convert to seconds
        
        # Communication
        self.emitter = self.supervisor.getDevice('emitter')
        self.receiver = self.supervisor.getDevice('receiver')
        self.receiver.enable(self.timestep)
        
        # Initialize components
        initial_q = [0.0] * Config.NUM_TASKS
        initial_w = Config.INITIAL_GROWTH_RATES.copy()
        
        self.env_model = EnvironmentModel(initial_q, initial_w)
        self.state_manager = StateManager(Config.NUM_ROBOTS, Config.NUM_TASKS)
        self.trash_spawner = TrashSpawner(self.supervisor, initial_w)
        
        # Data logging
        self.logger = DataLogger("multi_robot_allocation")
        
        # Time tracking
        self.current_time = 0.0
        self.last_broadcast_time = 0.0
        self.broadcast_interval = 0.1  # Broadcast every 100ms
        
        # Experiment control
        self.experiment_config = None
        
        print("Supervisor initialized")
    
    def set_experiment(self, experiment_type: str):
        """Configure experiment parameters"""
        if experiment_type == "surge":
            self.experiment_config = ExperimentConfig.experiment_1_surge()
        elif experiment_type == "failures":
            self.experiment_config = ExperimentConfig.experiment_2_failures()
        else:
            self.experiment_config = None
    
    def handle_experiment_events(self):
        """Execute experiment-specific events"""
        if self.experiment_config is None:
            return
        
        # Experiment 1: Growth rate surge
        if 'surge_start' in self.experiment_config:
            surge_start = self.experiment_config['surge_start']
            surge_end = self.experiment_config['surge_end']
            surge_patch = self.experiment_config['surge_patch']
            surge_rate = self.experiment_config['surge_rate']
            
            if abs(self.current_time - surge_start) < self.dt:
                print(f"[{self.current_time:.1f}s] Surge starting at patch {surge_patch}")
                self.env_model.set_growth_rate(surge_patch, surge_rate)
                self.trash_spawner.set_growth_rate(surge_patch, surge_rate)
                self.logger.log_event(
                    self.current_time, 
                    'growth_surge_start',
                    f'Patch {surge_patch} rate -> {surge_rate}'
                )
            
            if abs(self.current_time - surge_end) < self.dt:
                print(f"[{self.current_time:.1f}s] Surge ending at patch {surge_patch}")
                original_rate = Config.INITIAL_GROWTH_RATES[surge_patch]
                self.env_model.set_growth_rate(surge_patch, original_rate)
                self.trash_spawner.set_growth_rate(surge_patch, original_rate)
                self.logger.log_event(
                    self.current_time,
                    'growth_surge_end',
                    f'Patch {surge_patch} rate -> {original_rate}'
                )
        
        # Experiment 2: Robot failures
        if 'failure_start' in self.experiment_config:
            failure_start = self.experiment_config['failure_start']
            failure_end = self.experiment_config['failure_end']
            num_failures = self.experiment_config['num_failures']
            
            if abs(self.current_time - failure_start) < self.dt:
                print(f"[{self.current_time:.1f}s] Disabling {num_failures} robots")
                for i in range(num_failures):
                    self.state_manager.set_robot_active(i, False)
                    self.send_failure_command(i, disable=True)
                self.logger.log_event(
                    self.current_time,
                    'robot_failures',
                    f'{num_failures} robots disabled'
                )
            
            if abs(self.current_time - failure_end) < self.dt:
                print(f"[{self.current_time:.1f}s] Re-enabling {num_failures} robots")
                for i in range(num_failures):
                    self.state_manager.set_robot_active(i, True)
                    self.send_failure_command(i, disable=False)
                self.logger.log_event(
                    self.current_time,
                    'robot_recovery',
                    f'{num_failures} robots re-enabled'
                )
    
    def send_failure_command(self, robot_id: int, disable: bool):
        """Send command to disable/enable a robot"""
        msg = Message(MsgType.ROBOT_STATUS, {
            'robot_id': robot_id,
            'command': 'disable' if disable else 'enable'
        })
        self.emitter.send(msg.to_bytes())
    
    def process_robot_messages(self):
        """Process incoming messages from robots"""
        while self.receiver.getQueueLength() > 0:
            data = self.receiver.getData()
            msg = Message.from_bytes(data)
            
            if msg.type == MsgType.TASK_CHANGE:
                robot_id = msg.data['robot_id']
                new_task = msg.data['new_task']
                self.state_manager.update_robot_task(robot_id, new_task)
            
            elif msg.type == MsgType.ROBOT_STATUS:
                robot_id = msg.data['robot_id']
                # Can store additional robot info if needed
                pass
            
            self.receiver.nextPacket()
    
    def broadcast_global_state(self):
        """Broadcast q(t) and x(t) to all robots"""
        q = self.env_model.get_resources()
        x = self.state_manager.get_population_state()
        
        msg = SupervisorBroadcast.create_state_message(q, x, self.current_time)
        self.emitter.send(msg.to_bytes())
    
    def log_current_state(self):
        """Log current state for analysis"""
        q = self.env_model.get_resources()
        x = self.state_manager.get_population_state()
        w = self.env_model.get_growth_rates()
        robot_counts = self.state_manager.get_robot_count_per_task()
        
        self.logger.log_state(self.current_time, q, x, robot_counts, w)
    
    def run(self):
        """Main control loop"""
        print("Starting simulation...")
        
        # Initial broadcast
        self.broadcast_global_state()
        
        while self.supervisor.step(self.timestep) != -1:
            # Update time
            self.current_time += self.dt
            
            # Handle experiment-specific events
            self.handle_experiment_events()
            
            # Process robot messages
            self.process_robot_messages()
            
            # Get current population state
            x = self.state_manager.get_population_state()
            
            # Update environment model
            self.env_model.update(x, self.dt)
            
            # Update trash spawning
            self.trash_spawner.update(self.current_time, self.dt)
            
            # Broadcast state periodically
            if self.current_time - self.last_broadcast_time >= self.broadcast_interval:
                self.broadcast_global_state()
                self.last_broadcast_time = self.current_time
            
            # Log state
            self.log_current_state()
            
            # Check termination
            if self.current_time >= Config.SIMULATION_DURATION:
                print(f"Simulation complete at {self.current_time:.1f}s")
                break
        
        # Save final data
        self.logger.save_metadata({
            'num_robots': Config.NUM_ROBOTS,
            'num_tasks': Config.NUM_TASKS,
            'duration': Config.SIMULATION_DURATION,
            'experiment': self.experiment_config
        })
        print(f"Data saved to {self.logger.log_file}")

# Entry point
if __name__ == "__main__":
    controller = SupervisorController()
    controller.set_experiment("surge")  # or "failures" or None
    controller.run()