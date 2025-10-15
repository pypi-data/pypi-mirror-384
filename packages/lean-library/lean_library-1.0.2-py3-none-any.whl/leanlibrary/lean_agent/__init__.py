"""
LeanAgent: A comprehensive library for Lean theorem proving with AI assistance.

This package provides tools for:
- Repository tracing and data extraction
- Theorem proving with AI assistance
- Model training and evaluation
- Database management for Lean repositories
"""

__version__ = "0.1.0"
__author__ = "LeanLibrary Contributors"

from leanlibrary.prover import BaseProver, ExternalProver, RetrievalProver
from leanlibrary.trainer import RetrievalTrainer

from .config import ProverConfig, TrainingConfig
from .database.dynamic_database import DynamicDatabase

__all__ = [
    "DynamicDatabase",
    "TrainingConfig",
    "ProverConfig",
    "BaseProver",
    "ExternalProver",
    "RetrievalProver",
    "RetrievalTrainer",
]
