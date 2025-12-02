# Multi-Robot Task Allocation in Dynamic Environments

Implementation of the game-theoretic multi-robot task allocation framework from:

**"Multi-Robot Task Allocation Games in Dynamically Changing Environments"**  
*Shinkyu Park, Yaofeng Desmond Zhong, and Naomi Ehrich Leonard*  
ICRA 2021

## Overview

This package implements a decentralized decision-making algorithm that enables large teams of robots to optimally allocate tasks in dynamically changing environments. The framework uses:

- **Game-theoretic formulation**: Population game model for robot interactions
- **Poisson clock**: Asynchronous task revision timing
- **Payoff mechanism**: Determines task attractiveness based on resource levels
- **Revision protocol**: Probabilistic task switching rules

## Features

- ✅ Dynamic environment adaptation
- ✅ Robot failure resilience
- ✅ Scalable to large robot teams
- ✅ Convergence guarantees (Theorem 1 from paper)
- ✅ Webots simulation integration

## Installation
```bash
# Clone repository
git clone https://github.com/KipkoechTAMU/MultiRobotTaskAlloc
cd MultiRobotTaskAlloc

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

## Quick Start

### Running a Simulation
```bash
# In Webots, load the world file
# worlds/trash_collection.wbt

# The supervisor and robot controllers will automatically start
```


## Project Structure
```
multi_robot_task_allocation/
├── controllers/
│   ├── supervisor_controller/    # Supervisor logic
│   └── robot_controller/          # Individual robot control
├── models/                         # Core algorithms
│   ├── consumption_model.py       # Resource dynamics (Eq. 2, 3)
│   ├── payoff_mechanism.py        # Payoff calculation (Eq. 6)
│   └── revision_protocol.py       # Task switching (Eq. 7)
├── shared/                         # Shared utilities
│   ├── config.py                  # Configuration
│   ├── constants.py               # Constants
│   └── communication.py           # Messaging
├── experiments/                    # Experiment scripts
├── analysis/                       # Data analysis tools
├── tests/                          # Unit tests
└── worlds/                         # Webots worlds
```

## Configuration

Edit `shared/config.py` to modify:
```python
class Config:
    NUM_ROBOTS = 40              # Number of robots
    NUM_TASKS = 4                # Number of tasks/patches
    POISSON_LAMBDA = 8.0         # Revision rate (1/8 Hz)
    RHO = 1.0 / 600.0           # Protocol parameter
    NU = 0                       # Payoff weight (0=model-free)
    
    # Consumption model parameters (from paper)
    R_I = [3.44, 3.44, 3.44, 3.44]
    ALPHA_I = [0.036, 0.036, 0.036, 0.036]
    BETA_I = [0.91, 0.91, 0.91, 0.91]
```

## Key Algorithms

### Resource Dynamics (Equation 2)
```python
q̇_i(t) = -F_i(q_i(t), x_i(t)) + w_i
```

Where:
- `q_i`: Resource level at task i
- `F_i`: Consumption rate
- `w_i`: Growth rate
- `x_i`: Population fraction at task i

### Consumption Model (Equation 3)
```python
F_i(q_i, x_i) = R_i * (e^(α_i*q_i) - 1)/(e^(α_i*q_i) + 1) * x_i^β_i
```

### Payoff Mechanism (Equation 6)
```python
p_i(t) = q_i(t) + ν(-F_i(γ*, x_i) + w_i)
```

Where:
- `ν = 0`: Model-free (reactive)
- `ν > 0`: Model-based (predictive)

### Revision Protocol (Equation 7)
```python
P(switch i→j) = ρ[p_j - p_i]_+
P(stay at i) = 1 - ρ Σ_j [p_j - p_i]_+
```


## Performance Metrics

The system tracks:
- **Resource levels** `q(t)`: Should converge to equilibrium
- **Population state** `x(t)`: Should adapt to changes
- **Convergence time**: Time to reach equilibrium
- **Variance**: Measure of load balancing

## Citation

If you use this code, please cite the original paper:
```bibtex
@inproceedings{park2021multi,
  title={Multi-Robot Task Allocation Games in Dynamically Changing Environments},
  author={Park, Shinkyu and Zhong, Yaofeng Desmond and Leonard, Naomi Ehrich},
  booktitle={2021 IEEE International Conference on Robotics and Automation (ICRA)},
  year={2021},
  organization={IEEE}
}
```

## License

MIT License (or specify your license)

## Contact

For questions about the implementation:
- Create an issue on GitHub

For questions about the algorithm:
- Contact the paper authors:
  - shinkyu@princeton.edu
  - y.zhong@princeton.edu
  - naomi@princeton.edu

## Acknowledgments

