"""
Main robot controller - integrates all components
"""
from controller import Robot
from typing import Optional

from decision_maker import DecisionMaker
from poisson_clock import PoissonClock
from finite_state_machine import FiniteStateMachine

from shared.config import Config
from shared.communication import Message, RobotReport, MessageType

class RobotController:
    """
    Main controller for individual robot
    Integrates decision-making, timing, and behavior control
    """
    def __init__(self):
        # Initialize Webots robot
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())
        self.dt = self.timestep / 1000.0
        
        # Get robot ID from name
        robot_name = self.robot.getName()
        self.robot_id = int(robot_name.split('_')[-1]) if '_' in robot_name else 0
        
        # Communication
        self.emitter = self.robot.getDevice('emitter')
        self.receiver = self.robot.getDevice('receiver')
        self.receiver.enable(self.timestep)
        
        # Initialize components
        self.decision_maker = DecisionMaker(self.robot_id, Config.NU)
        self.poisson_clock = PoissonClock(Config.POISSON_LAMBDA)
        self.fsm = FiniteStateMachine(self.robot_id, self.robot)
        
        # State
        self.current_time = 0.0
        self.is_active = True
        
        # Initialize task
        initial_task = self.decision_maker.initialize_task()
        self.fsm.set_task(initial_task)
        
        print(f"Robot {self.robot_id} initialized")
    
    def process_supervisor_messages(self):
        """Process messages from supervisor"""
        while self.receiver.getQueueLength() > 0:
            data = self.receiver.getData()
            msg = Message.from_bytes(data)
            
            if msg.type == MessageType.STATE_UPDATE:
                # Update global state
                q = msg.data['q']
                x = msg.data['x']
                w = msg.data.get('w', Config.INITIAL_GROWTH_RATES)
                self.decision_maker.update_state(q, x, w)
            
            elif msg.type == MessageType.ROBOT_STATUS:
                # Check for failure commands
                if msg.data.get('robot_id') == self.robot_id:
                    command = msg.data.get('command')
                    if command == 'disable':
                        self.is_active = False
                        self.fsm.stop()
                        print(f"Robot {self.robot_id}: DISABLED")
                    elif command == 'enable':
                        self.is_active = True
                        print(f"Robot {self.robot_id}: RE-ENABLED")
            
            self.receiver.nextPacket()
    
    def check_task_revision(self):
        """Check if it's time to revise task"""
        if not self.is_active:
            return
        
        # Check Poisson clock
        if self.poisson_clock.should_tick(self.current_time):
            # Revise task
            new_task = self.decision_maker.revise_task()
            
            if new_task is not None:
                # Task changed - notify supervisor
                old_task = self.fsm.current_task
                self.fsm.set_task(new_task)
                
                msg = RobotReport.create_task_change_message(
                    self.robot_id, old_task, new_task
                )
                self.emitter.send(msg.to_bytes())
    
    def send_status_update(self):
        """Periodically send status to supervisor"""
        if self.current_time % 1.0 < self.dt:  # Every second
            msg = RobotReport.create_status_message(
                self.robot_id,
                self.fsm.current_task,
                self.fsm.basket_count,
                self.fsm.get_position(),
                self.is_active
            )
            self.emitter.send(msg.to_bytes())
    
    def run(self):
        """Main control loop"""
        print(f"Robot {self.robot_id} starting...")
        
        while self.robot.step(self.timestep) != -1:
            # Update time
            self.current_time += self.dt
            
            # Process messages from supervisor
            self.process_supervisor_messages()
            
            # Check for task revision
            self.check_task_revision()
            
            # Execute behavior (if active)
            if self.is_active:
                self.fsm.update()
            
            # Send status update
            self.send_status_update()

# Entry point
if __name__ == "__main__":
    controller = RobotController()
    controller.run()