"""
LeanLibrary: A comprehensive library for Lean theorem proving with AI assistance.

This unified package provides:
- lean_agent: Repository tracing, theorem proving, and model training
- lean_dojo: Lean interaction and data extraction tools
- utils: Common utilities and helper functions
"""

__version__ = "0.1.9"
__author__ = "LeanLibrary Contributors"

# Import main components for easy access
from .agent import BaseAgent, HFAgent, LeanAgent
from .prover import BaseProver, ExternalProver, HFProver, RetrievalProver

__all__ = [
    "BaseAgent",
    "HFAgent",
    "LeanAgent",
    "BaseProver",
    "HFProver",
    "RetrievalProver",
    "ExternalProver",
]
