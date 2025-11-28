"""
Core mathematical models for task allocation algorithm

This module implements the key equations from the paper:
- Consumption Model (Equation 3): F_i(q_i, x_i)
- Payoff Mechanism (Equation 6): p_i(t) = q_i(t) + ν(...)
- Revision Protocol (Equation 7): Probabilistic task switching

Usage:
    from models import ConsumptionModel, PayoffMechanism, RevisionProtocol
    
    # Create models
    consumption = ConsumptionModel()
    payoff = PayoffMechanism(nu=40)
    protocol = RevisionProtocol(rho=1/600)
    
    # Use in decision-making
    F = consumption.compute_consumption(task_id, q_i, x_i)
    p = payoff.compute_all_payoffs(q, x, w)
    new_task = protocol.select_task(current_task, payoffs)
"""

from .consumption_model import ConsumptionModel
from .payoff_mechanism import PayoffMechanism
from .revision_protocol import RevisionProtocol

__all__ = [
    'ConsumptionModel',
    'PayoffMechanism',
    'RevisionProtocol',
]

__version__ = '0.1.0'

# Model validation helper
def validate_models_compatibility(consumption, payoff, protocol):
    """
    Validate that models are compatible with each other
    
    Args:
        consumption: ConsumptionModel instance
        payoff: PayoffMechanism instance
        protocol: RevisionProtocol instance
    
    Returns:
        bool: True if compatible
    
    Raises:
        ValueError: If models are incompatible
    """
    # Check that payoff mechanism has same consumption model
    if not isinstance(consumption, ConsumptionModel):
        raise ValueError("Invalid consumption model")
    
    if not isinstance(payoff, PayoffMechanism):
        raise ValueError("Invalid payoff mechanism")
    
    if not isinstance(protocol, RevisionProtocol):
        raise ValueError("Invalid revision protocol")
    
    # Additional compatibility checks could go here
    return True

# Factory function for creating complete model set
def create_model_set(nu=0, rho=1/600):
    """
    Create a complete set of compatible models
    
    Args:
        nu: Payoff mechanism weight parameter
        rho: Revision protocol rate parameter
    
    Returns:
        tuple: (ConsumptionModel, PayoffMechanism, RevisionProtocol)
    
    Example:
        consumption, payoff, protocol = create_model_set(nu=40)
    """
    consumption = ConsumptionModel()
    payoff = PayoffMechanism(nu=nu)
    protocol = RevisionProtocol(rho=rho)
    
    validate_models_compatibility(consumption, payoff, protocol)
    
    return consumption, payoff, protocol