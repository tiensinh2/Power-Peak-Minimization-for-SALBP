"""
MaxSAT Unary Model (Inaugural Model) adapter for the salb3pm package.
"""

from inaugural_model.encoder import InauguralMaxSATEncoder
from inaugural_model.solver import InauguralMaxSATSolver

__all__ = ["InauguralMaxSATEncoder", "InauguralMaxSATSolver"]
